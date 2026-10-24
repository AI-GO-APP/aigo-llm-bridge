"""Synthetic HTTP only: no provider credentials, inference or external network."""
import json
import socket
import ssl
import shutil
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest

from desktop_bridge import relay as module
from desktop_bridge.relay import Relay, decode_work, MAX_FORWARD
from desktop_bridge.relay_transport import Connections, TransportError, Wire
from desktop_bridge.store import Store


@pytest.fixture
def server():
    entered, release = threading.Event(), threading.Event()
    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'
        def log_message(self, *_): pass
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            self.server.received.append((self.path, self.client_address, body, self.headers))
            if self.path == '/stall':
                entered.set(); release.wait(3)
            if self.path == '/drop':
                self.close_connection = True
                self.connection.shutdown(socket.SHUT_RDWR)
                return
            if self.path == '/drip':
                try:
                    self.connection.sendall(b'HTTP/1.1 200 OK\r\n')
                    for _ in range(12):
                        self.connection.sendall(b'X-Fixture: synthetic\r\n'); time.sleep(.07)
                except OSError: pass
                self.close_connection = True
                return
            self.send_response(302 if self.path == '/redirect' else 400 if self.path == '/error' else 200)
            self.send_header('Location', '/target')
            self.send_header('Content-Length', str(900 if self.path == '/truncated' else len(body)))
            self.send_header('X-Bridge-Cost-Source', 'fixture')
            self.send_header('X-Private-Fixture', 'must-not-forward')
            if self.path in ('/close', '/truncated', '/body-stall'): self.send_header('Connection', 'close')
            self.end_headers()
            if self.path == '/body-stall': entered.set(); release.wait(3)
            try: self.wfile.write(body); self.wfile.flush()
            except OSError: pass
            if self.path == '/stale': self.close_connection = True
    http = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    http.daemon_threads = True
    http.received = []
    thread = threading.Thread(target=http.serve_forever, daemon=True); thread.start()
    yield SimpleNamespace(http=http, base=f'http://127.0.0.1:{http.server_port}', entered=entered, release=release)
    release.set(); http.shutdown(); http.server_close(); thread.join(2)


def test_reuse_close_error_filter_and_unicode(server):
    pool = Connections(1, threading.Event(), local=True)
    try:
        body = json.dumps({'fixture': '合成內容'}, ensure_ascii=False).encode()
        for _ in range(3):
            assert pool.exchange(server.base, '/', {}, body)[1] == body
        assert len({item[1] for item in server.http.received}) == 1
        assert pool.snapshot()['connections_created'] == 1
        assert pool.snapshot()['reused_requests'] == 2
        status, raw, headers = pool.exchange(server.base, '/error', {}, body, success_only=False)
        assert (status, raw, headers) == (400, body, {'X-Bridge-Cost-Source': 'fixture'})
        assert pool.exchange(server.base, '/close', {}, body)[1] == body
        assert pool.snapshot()['idle'] == 0
        pool.exchange(server.base, '/', {}, body)
        assert pool.snapshot()['connections_created'] == 2
    finally: pool.close()


def test_real_tls_reuse_and_untrusted_certificate_rejected(server, tmp_path, monkeypatch):
    if not shutil.which('openssl'): pytest.skip('Local TLS fixture requires openssl')
    cert, key = tmp_path/'fixture.pem', tmp_path/'fixture.key'
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
                    '-subj', '/CN=localhost', '-addext', 'subjectAltName=DNS:localhost',
                    '-keyout', str(key), '-out', str(cert)], check=True, capture_output=True)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); context.load_cert_chain(cert, key)
    http = ThreadingHTTPServer(('127.0.0.1', 0), server.http.RequestHandlerClass)
    http.daemon_threads = True; http.received = []
    http.socket = context.wrap_socket(http.socket, server_side=True)
    thread = threading.Thread(target=http.serve_forever, daemon=True); thread.start()
    monkeypatch.setattr(module.urllib.request, 'getproxies', lambda: {})
    pool = Connections(1, threading.Event()); untrusted = Connections(1, threading.Event())
    pool.context = ssl.create_default_context(cafile=str(cert))
    base = f'https://localhost:{http.server_port}'
    try:
        for _ in range(3): assert pool.json(base, '/', {}, 'synthetic') == {}
        assert pool.snapshot()['connections_created'] == 1 and pool.snapshot()['reused_requests'] == 2
        large = ('合成'*400_000).encode()
        assert pool.exchange(base, '/', {}, large, limit=len(large))[1] == large
        with pytest.raises(TransportError, match='^io$'): untrusted.json(base, '/', {}, 'synthetic')
        assert len(http.received) == 4
    finally:
        pool.close(); untrusted.close(); http.shutdown(); http.server_close(); thread.join(2)


@pytest.mark.parametrize('path,kwargs,category', [
    ('/redirect', {}, 'http_status'), ('/truncated', {}, 'truncated_response'),
    ('/', {'limit': 1}, 'response_size'), ('/drop', {}, 'io'),
])
def test_failed_submission_is_never_replayed(server, path, kwargs, category):
    pool = Connections(1, threading.Event(), local=True)
    try:
        with pytest.raises(TransportError, match=f'^{category}$'):
            pool.exchange(server.base, path, {'Authorization': 'Bearer synthetic'}, b'{}', **kwargs)
        assert len(server.http.received) == 1
        assert pool.snapshot()['idle'] == 0
    finally: pool.close()


@pytest.mark.parametrize('path', ['/stall', '/body-stall'])
def test_stop_interrupts_active_read_and_slot_waiter(server, monkeypatch, path):
    # Model platforms where shutdown/close does not wake a blocking read/select.
    monkeypatch.setattr(Wire, 'shutdown', lambda *_: None)
    stop = threading.Event(); pool = Connections(1, stop, local=True); failures = []
    def run():
        try: pool.exchange(server.base, path, {}, b'{}')
        except TransportError as error: failures.append(str(error))
    first = threading.Thread(target=run); first.start()
    assert server.entered.wait(2)
    second = threading.Thread(target=run); second.start()
    started = time.monotonic(); stop.set(); pool.close()
    for thread in (first, second): thread.join(1)
    assert not first.is_alive() and not second.is_alive()
    assert time.monotonic() - started < 1
    assert len(failures) == 2 and len(server.http.received) == 1
    assert pool.snapshot()['active'] == pool.snapshot()['idle'] == 0


def test_timeout_and_separate_poll_result_connections(server):
    poll = Connections(1, threading.Event(), local=True)
    results = Connections(1, threading.Event(), local=True)
    errors = []
    def run():
        try: poll.exchange(server.base, '/stall', {}, b'{}', timeout=.2)
        except TransportError as error: errors.append(str(error))
    thread = threading.Thread(target=run); thread.start()
    try:
        assert server.entered.wait(1)
        assert results.exchange(server.base, '/result', {}, b'{}')[0] == 200
        thread.join(1)
        assert errors and not thread.is_alive()
    finally: poll.close(); results.close()


def test_slow_headers_cannot_extend_total_deadline(server):
    pool = Connections(1, threading.Event(), local=True)
    try:
        began = time.monotonic()
        with pytest.raises(TransportError, match='^timeout$'):
            pool.exchange(server.base, '/drip', {}, b'{}', timeout=.2)
        assert time.monotonic() - began < .6
        assert len(server.http.received) == 1
    finally: pool.close()


def test_partial_write_is_cooperatively_cancelled_without_shutdown():
    sender, receiver = socket.socketpair()
    sender.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
    stop = threading.Event(); pool = Connections(1, stop, local=True)
    wire = Wire(sender); wire.bind(pool.check, time.monotonic()+3); errors = []
    def write():
        try: wire.sendall(b'x'*3_000_000)
        except TransportError as error: errors.append(str(error))
    thread = threading.Thread(target=write); thread.start()
    try:
        time.sleep(.05); stop.set(); thread.join(1)
        assert not thread.is_alive() and errors == ['stopped']
    finally: stop.set(); wire.close(); receiver.close(); pool.close(); thread.join(2)


def test_stale_idle_connection_is_not_automatically_reconnected(server):
    pool = Connections(1, threading.Event(), local=True)
    try:
        pool.exchange(server.base, '/stale', {}, b'{}')
        time.sleep(.05)
        with pytest.raises(TransportError): pool.exchange(server.base, '/', {}, b'{}')
        assert len(server.http.received) == 1
        assert pool.snapshot()['connections_created'] == 1
        # A distinct subsequent work may use a fresh connection; the failed work was not replayed.
        assert pool.exchange(server.base, '/', {}, b'{"new_work":true}')[0] == 200
        assert len(server.http.received) == 2 and pool.snapshot()['connections_created'] == 2
    finally: pool.close()


def test_https_origin_and_proxy_fallback_preserve_verification_and_no_redirect(monkeypatch):
    # The OS proxy route retains urllib tunnel/auth behavior; direct pooling is disabled.
    opened = []
    class Response:
        status = 200; headers = {}
        def read(self, limit): return b'{}'
        def close(self): pass
    def build(*handlers):
        assert any(isinstance(h, module.NoRedirect) for h in handlers)
        https = next(h for h in handlers if isinstance(h, module.urllib.request.HTTPSHandler))
        assert https._context.verify_mode.name == 'CERT_REQUIRED'
        return SimpleNamespace(open=lambda req, timeout: opened.append(req) or Response())
    monkeypatch.setattr(module.urllib.request, 'getproxies', lambda: {'https': 'http://synthetic.invalid:80'})
    monkeypatch.setattr(module.urllib.request, 'proxy_bypass', lambda _: False)
    monkeypatch.setattr(module.urllib.request, 'build_opener', build)
    pool = Connections(1, threading.Event())
    try:
        assert pool.json('https://fixture.invalid', '/agent/poll', {}, 'synthetic') == {}
        assert len(opened) == 1 and pool.snapshot()['proxy_requests'] == 1
        assert pool.snapshot()['connections_created'] == pool.snapshot()['idle'] == 0
        for base in ('http://fixture.invalid', 'https://user:password@fixture.invalid', 'https://fixture.invalid?secret=1'):
            with pytest.raises(TransportError, match='origin'): pool.exchange(base, '/', {}, b'{}')
    finally: pool.close()


def work(**changes):
    return dict(id=str(uuid.uuid4()), path='/api/v1/chat/completions', method='POST',
                authorization='Bearer synthetic', body='{}', deadline=int((time.time() + 60) * 1000), **changes)


def test_batch_and_legacy_decode_reject_entire_malformed_batch():
    first, second = work(), work()
    assert decode_work({'request': first}) == [dict(first, request_id=None)]
    assert decode_work({'request': None}) == decode_work({'requests': []}) == []
    assert len(decode_work({'requests': [first, second]})) == 2
    malformed = dict(second, path='/admin/private')
    values = [{'requests': [first, malformed]}, {'requests': [first, first]},
              {'request': first, 'requests': []}, {'requests': [first, second]}]
    for value in values:
        with pytest.raises(ValueError): decode_work(value, requested=1)
    for patch in ({'deadline': float('nan')}, {'deadline': True}, {'deadline': (time.time()+1000)*1000},
                  {'authorization': 'Bearer synthetic\r\nInjected: fixture'}, {'body': '字'*1_000_001}):
        with pytest.raises(ValueError): decode_work({'requests': [dict(first, **patch)]})


def test_loop_bounds_all_submitted_work(tmp_path, monkeypatch):
    store = Store(tmp_path); store.set('public_url', 'https://synthetic.invalid')
    relay = Relay(store, 0); session = relay.session
    release = threading.Event(); calls = []
    monkeypatch.setattr(module.secret, 'load', lambda _: 'synthetic')
    def poll(*args, **kwargs):
        requested = args[2]['batch_size']; calls.append(requested)
        return {'requests': [work() for _ in range(requested)]}
    def forward(*_):
        release.wait(3)
    monkeypatch.setattr(session.poll, 'json', poll)
    monkeypatch.setattr(relay, 'forward', forward)
    try:
        relay.start()
        deadline = time.monotonic() + 2
        while len(session.inflight) < MAX_FORWARD and time.monotonic() < deadline: time.sleep(.005)
        time.sleep(.05)
        assert len(session.inflight) == session.counts['works_dispatched'] == MAX_FORWARD
        assert sum(calls) == MAX_FORWARD and max(calls) <= 8
        relay.stop(); release.set()
        assert not relay.thread.is_alive()
    finally: release.set(); relay.stop(); store.close()


def test_duplicate_cross_poll_and_old_generation_cannot_change_state(tmp_path, monkeypatch):
    store = Store(tmp_path); store.set('public_url', 'https://synthetic.invalid')
    relay = Relay(store, 0); old = relay.session; item = work(); dispatched = []
    monkeypatch.setattr(module.secret, 'load', lambda _: 'synthetic')
    monkeypatch.setattr(old.poll, 'json', lambda *_args, **_kwargs: {'requests': [item]})
    monkeypatch.setattr(relay, 'forward', lambda *args: dispatched.append(args[0]['id']))
    try:
        relay.start()
        deadline = time.monotonic() + 2
        while not old.counts['duplicate_rejections'] and time.monotonic() < deadline: time.sleep(.005)
        assert dispatched == [item['id']] and old.counts['duplicate_rejections'] == 1
        relay.stop(); relay._reset()
        relay.state = 'new generation'
        relay.state_for(old, 'late failure')
        assert relay.state == 'new generation' and old.stop.is_set()
        assert relay.session.id != old.id
    finally: relay.stop(); store.close()


def test_forward_preserves_local_error_receipt_and_cost_headers(tmp_path, server):
    store = Store(tmp_path); relay = Relay(store, server.http.server_port); sent = []
    relay.session.results.json = lambda *args, **_kwargs: sent.append(args[2]) or {'accepted': True}
    item = work(); item['path'] = '/error'; item['body'] = '{"error":"合成失敗"}'
    try:
        relay.forward(item, 'https://synthetic.invalid', 'synthetic')
        assert sent == [{'id': item['id'], 'status': 400, 'body': item['body'],
                         'headers': {'X-Bridge-Cost-Source': 'fixture'}}]
        assert relay.snapshot()['forward_errors'] == 0
    finally: relay.stop(); store.close()
