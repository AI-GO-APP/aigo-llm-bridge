"""Bounded, origin-scoped HTTP connections. Never retry a submitted request."""
import http.client
import json
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


def parse_json(raw):
    def invalid(_):
        raise TransportError('protocol')
    value = json.loads(raw, parse_constant=invalid)
    if not isinstance(value, dict):
        raise TransportError('protocol')
    return value


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
                           connections_created=0, reused_requests=0, proxy_requests=0)

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

    def exchange(self, base, path, headers, body, *, timeout=30, limit=6_100_000, success_only=True):
        deadline = time.monotonic() + timeout
        acquired = False
        conn = wire = response = None
        timer = None
        timer_lock = threading.Lock()
        timer_done = False
        reusable = reused = False
        try:
            while not acquired:
                acquired = self.slots.acquire(timeout=min(.05, self.check(deadline)))
            with self.lock: self.counts['requests_started'] += 1
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
                        raise TransportError('http_status') from None
                    response = error
                raw = response.read(limit + 1)
                if len(raw) > limit: raise TransportError('response_size')
                self.check(deadline)
                result = (response.status, raw, {k: response.headers[k] for k in COST_HEADERS if response.headers.get(k)})
            else:
                origin = (target.scheme, target.hostname, target.port or (443 if target.scheme == 'https' else 80))
                stale = []
                with self.lock:
                    self.check(deadline)
                    while self.idle:
                        previous, candidate, ready = self.idle.pop()
                        if previous == origin and time.monotonic() - ready < 60 and candidate.sock is not None:
                            conn = candidate; reused = True; break
                        stale.append(candidate)
                    if conn is None:
                        if target.scheme == 'https':
                            conn = http.client.HTTPSConnection(origin[1], origin[2], context=self.context,
                                                               timeout=self.check(deadline))
                        else:
                            conn = http.client.HTTPConnection(origin[1], origin[2], timeout=self.check(deadline))
                        conn.auto_open = 0  # Explicit connect only; stop must never cause an implicit reconnect.
                    self.active.add(conn)
                for old in stale: self.dispose(old)
                if conn.sock is None:
                    conn.connect()
                    with self.lock: self.counts['connections_created'] += 1
                wire = conn.sock
                with self.lock: self.sockets[conn] = wire
                # A socket timeout alone can be extended indefinitely by slowly
                # arriving headers. Bound the entire direct exchange as well.
                def expire():
                    with timer_lock:
                        if not timer_done: self.dispose(conn, wire)
                timer = threading.Timer(self.check(deadline), expire)
                timer.daemon = True; timer.start()
                wire.settimeout(self.check(deadline))
                conn.request('POST' if body is not None else 'GET', target.path or '/', body=body,
                             headers=headers)
                response = conn.getresponse()
                if success_only and not 200 <= response.status < 300:
                    raise TransportError('http_status')
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
            with self.lock: self.counts['requests_failed'] += 1
            category = str(error) if isinstance(error, TransportError) else 'io'
            if time.monotonic() >= deadline: category = 'timeout'
            raise TransportError(category) from None
        finally:
            with timer_lock: timer_done = True
            if timer is not None: timer.cancel()
            if response is not None: response.close()
            if conn is not None:
                with self.lock:
                    self.active.discard(conn); self.sockets.pop(conn, None)
                    keep = reusable and not self.closed and not self.stop.is_set()
                    if keep: self.idle.append((origin, conn, time.monotonic()))
                if not keep: self.dispose(conn, wire)
            if acquired: self.slots.release()

    def json(self, base, path, body, credential, *, limit=6_100_000):
        raw = json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode()
        _, value, _ = self.exchange(base, path, {
            'Authorization': 'Bearer ' + credential, 'Content-Type': 'application/json',
            'User-Agent': 'local-token-buffet-bridge-relay/0.9.13'}, raw, limit=limit)
        return parse_json(value)
