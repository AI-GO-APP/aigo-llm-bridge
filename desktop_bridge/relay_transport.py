"""Bounded, origin-scoped HTTP connections. Never retry a submitted request."""
import http.client
import io
import json
import select
import socket
import ssl
import threading
import time
import urllib.request
import urllib.error
from urllib.parse import urlsplit

import certifi

COST_HEADERS = ('X-Bridge-Cost-Source', 'X-Bridge-Pricing-Model', 'X-Bridge-Pricing-Fetched-At')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


class TransportError(ValueError):
    """Fixed category only; never expose URLs, credentials or response text."""
    def __init__(self, category, status=None):
        super().__init__(category)
        self.status = status


def parse_json(raw):
    def invalid(_):
        raise TransportError('protocol')
    value = json.loads(raw, parse_constant=invalid)
    if not isinstance(value, dict):
        raise TransportError('protocol')
    return value


class Reader(io.RawIOBase):
    def __init__(self, wire):
        self.wire = wire
        self.released = False
        with wire.lock: wire.readers += 1
    def readable(self): return True
    def readinto(self, buffer): return self.wire.receive(buffer)
    def close(self):
        with self.wire.lock:
            if not self.released:
                self.released = True
                self.wire.readers -= 1
                if self.wire.closed and not self.wire.readers: self.wire.raw.close()
        super().close()


class Wire:
    """Nonblocking I/O checks cancellation without depending on OS close wakeups.

    HTTPResponse can own its reader after HTTPConnection closes (Connection: close).
    Keep that reader valid until it closes, matching socket.makefile semantics.
    """
    def __init__(self, raw):
        self.raw = raw
        self.lock = threading.Lock()
        self.readers = 0; self.closed = False
        raw.setblocking(False)

    def bind(self, check, deadline): self.check, self.deadline = check, deadline
    def settimeout(self, _): self.check(self.deadline)
    def makefile(self, mode, *args, **kwargs):
        if mode != 'rb': raise TransportError('protocol')
        return io.BufferedReader(Reader(self))
    def close(self):
        with self.lock:
            self.closed = True
            if not self.readers: self.raw.close()
    def shutdown(self, how): self.raw.shutdown(how)

    def usable(self):
        # Readable idle sockets may contain EOF, TLS close-notify or unexpected
        # leftover data. Discard before sending any bytes of a new request.
        try:
            return (not self.closed and self.raw.fileno() >= 0
                    and not (isinstance(self.raw, ssl.SSLSocket) and self.raw.pending())
                    and not select.select([self.raw], [], [], 0)[0])
        except (OSError, ValueError): return False

    def wait(self, read):
        while True:
            delay = min(.05, self.check(self.deadline))
            readable, writable, _ = select.select([self.raw] if read else [], [] if read else [self.raw], [], delay)
            if readable or writable: return

    def receive(self, buffer):
        while True:
            self.check(self.deadline)
            try: return self.raw.recv_into(buffer)
            except ssl.SSLWantWriteError: self.wait(False)
            except (ssl.SSLWantReadError, BlockingIOError): self.wait(True)

    def sendall(self, data):
        remaining = memoryview(data)
        while remaining:
            self.check(self.deadline)
            try:
                sent = self.raw.send(remaining)
                if not sent: raise TransportError('io')
                remaining = remaining[sent:]
            except ssl.SSLWantReadError: self.wait(True)
            except (ssl.SSLWantWriteError, BlockingIOError): self.wait(False)


class Connections:
    def __init__(self, limit, stop, *, local=False):
        self.limit, self.stop, self.local = limit, stop, local
        self.context = ssl.create_default_context(cafile=certifi.where())
        self.slots = threading.BoundedSemaphore(limit)
        self.lock = threading.Lock()
        self.idle = []
        self.active = set()
        self.sockets = {}
        self.closed = False
        self.counts = dict(requests_started=0, requests_completed=0, requests_failed=0,
                           connections_created=0, reused_requests=0, proxy_requests=0,
                           idle_discarded=0, last_failure=None)

    def snapshot(self):
        with self.lock:
            return {**self.counts, 'active': len(self.active), 'idle': len(self.idle),
                    'limit': self.limit, 'closed': self.closed}

    def check(self, deadline):
        if self.closed or self.stop.is_set():
            raise TransportError('stopped')
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TransportError('timeout')
        return remaining

    @staticmethod
    def dispose(conn, wire=None):
        wire = wire or conn.sock
        if wire is not None:
            try: wire.shutdown(socket.SHUT_RDWR)
            except OSError: pass
        try: conn.close()
        except OSError: pass

    def close(self):
        with self.lock:
            self.closed = True
            items = [(conn, self.sockets.get(conn)) for conn in self.active]
            items += [(conn, None) for _, conn, _ in self.idle]
            self.idle.clear()
        # Shutdown interrupts a read even if the response owns a socket file.
        for conn, wire in items:
            self.dispose(conn, wire)

    def exchange(self, base, path, headers, body, *, timeout=30, limit=6_100_000, success_only=True, fresh=False):
        deadline = time.monotonic() + timeout
        acquired = False
        conn = wire = response = None
        reusable = reused = False
        phase, idle_ms = 'slot', None
        try:
            while not acquired:
                acquired = self.slots.acquire(timeout=min(.05, self.check(deadline)))
            with self.lock: self.counts['requests_started'] += 1
            phase = 'origin'
            target = urlsplit(base.rstrip('/') + path)
            if (target.username is not None or target.password is not None or target.query or target.fragment
                    or not target.hostname or target.scheme not in ('http', 'https')):
                raise TransportError('origin')
            if target.scheme == 'http' and not (self.local and target.hostname in ('127.0.0.1', '::1')):
                raise TransportError('origin')
            if self.local and target.hostname not in ('127.0.0.1', '::1'):
                raise TransportError('origin')
            proxies = {} if self.local else urllib.request.getproxies()
            proxy = bool((proxies.get(target.scheme) or proxies.get('all'))
                         and not urllib.request.proxy_bypass(target.netloc))
            if proxy:
                phase = 'proxy'
                # Keep urllib's existing proxy/tunnel/auth semantics. No redirect/retry.
                with self.lock:
                    old = self.idle; self.idle = []
                    self.counts['proxy_requests'] += 1
                for _, stale, _ in old: self.dispose(stale)
                opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxies), NoRedirect(),
                    urllib.request.HTTPSHandler(context=self.context))
                req = urllib.request.Request(target.geturl(), data=body, headers=headers,
                                             method='POST' if body is not None else 'GET')
                try:
                    response = opener.open(req, timeout=self.check(deadline))
                except urllib.error.HTTPError as error:
                    if success_only:
                        error.close()
                        raise TransportError('http_status', error.code) from None
                    response = error
                raw = response.read(limit + 1)
                if len(raw) > limit: raise TransportError('response_size')
                self.check(deadline)
                result = (response.status, raw, {k: response.headers[k] for k in COST_HEADERS if response.headers.get(k)})
            else:
                origin = (target.scheme, target.hostname, target.port or (443 if target.scheme == 'https' else 80))
                with self.lock:
                    self.check(deadline)
                    while self.idle:
                        previous, candidate, ready = self.idle.pop()
                        age = time.monotonic() - ready
                        if (not fresh and previous == origin and age < 10 and candidate.sock is not None
                                and candidate.sock.usable()):
                            idle_ms = round(age * 1000)
                            conn = candidate; reused = True; break
                        self.dispose(candidate)
                        self.counts['idle_discarded'] += 1
                    if conn is None:
                        if target.scheme == 'https':
                            conn = http.client.HTTPSConnection(origin[1], origin[2], context=self.context,
                                                               timeout=self.check(deadline))
                        else:
                            conn = http.client.HTTPConnection(origin[1], origin[2], timeout=self.check(deadline))
                        conn.auto_open = 0  # Explicit connect only; stop must never cause an implicit reconnect.
                    self.active.add(conn)
                phase = 'connect'
                if conn.sock is None:
                    conn.connect()
                    with self.lock: self.counts['connections_created'] += 1
                    conn.sock = Wire(conn.sock)
                wire = conn.sock
                wire.bind(self.check, deadline)
                with self.lock: self.sockets[conn] = wire
                wire.settimeout(self.check(deadline))
                phase = 'send'
                conn.request('POST' if body is not None else 'GET', target.path or '/', body=body,
                             headers=headers)
                phase = 'headers'
                response = conn.getresponse()
                if success_only and not 200 <= response.status < 300:
                    raise TransportError('http_status', response.status)
                phase = 'body'
                if response.getheader('Content-Encoding', 'identity').lower() != 'identity':
                    raise TransportError('content_encoding')
                if response.length is not None and response.length > limit:
                    raise TransportError('response_size')
                parts = []; size = 0
                while True:
                    wire.settimeout(self.check(deadline))
                    part = response.read1(min(65536, limit + 1 - size))
                    if not part:
                        if response.length not in (None, 0): raise TransportError('truncated_response')
                        break
                    size += len(part)
                    if size > limit: raise TransportError('response_size')
                    parts.append(part)
                    if response.length == 0: break
                raw = b''.join(parts)
                result = (response.status, raw, {k: response.getheader(k) for k in COST_HEADERS if response.getheader(k)})
                reusable = not response.will_close and conn.sock is not None
            with self.lock:
                self.counts['requests_completed'] += 1
                if reused and reusable: self.counts['reused_requests'] += 1
            return result
        except Exception as error:
            category = str(error) if isinstance(error, TransportError) else 'io'
            if time.monotonic() >= deadline: category = 'timeout'
            if category not in {'stopped','timeout','origin','http_status','content_encoding','response_size','truncated_response','protocol','io'}: category = 'io'
            status = getattr(error, 'status', None) or (response.status if response is not None else None)
            if type(status) is not int or not 100 <= status <= 599: status = None
            name = type(error).__name__
            if name not in {'TransportError','RemoteDisconnected','IncompleteRead','TimeoutError','SSLError','ConnectionResetError','BrokenPipeError','NotConnected','CannotSendRequest','ResponseNotReady','OSError','ValueError'}: name = 'Exception'
            with self.lock:
                self.counts['requests_failed'] += 1
                self.counts['last_failure'] = dict(category=category, phase=phase, status=status,
                    error_class=name, reused=reused, idle_ms=idle_ms)
            raise TransportError(category, status) from None
        finally:
            if response is not None: response.close()
            if conn is not None:
                with self.lock:
                    self.active.discard(conn); self.sockets.pop(conn, None)
                    keep = reusable and not self.closed and not self.stop.is_set()
                    if keep: self.idle.append((origin, conn, time.monotonic()))
                if not keep: self.dispose(conn, wire)
            if acquired: self.slots.release()

    def json(self, base, path, body, credential, *, limit=6_100_000, timeout=30, fresh=False):
        raw = json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode()
        _, value, _ = self.exchange(base, path, {
            'Authorization': 'Bearer ' + credential, 'Content-Type': 'application/json',
            'User-Agent': 'local-token-buffet-bridge-relay/0.9.14'}, raw, limit=limit, timeout=timeout, fresh=fresh)
        return parse_json(value)
