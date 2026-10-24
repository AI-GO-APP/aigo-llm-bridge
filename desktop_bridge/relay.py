"""Outbound, bounded batch relay. Content and credentials remain in RAM."""
from concurrent.futures import ThreadPoolExecutor
import math
import random
import threading
import time
import urllib.request
import ssl
import uuid

import certifi

from . import secret
from .capacity import STANDARD_CONCURRENCY, CONTROL_CONCURRENCY, is_inference_request
from .relay_transport import Connections, COST_HEADERS, NoRedirect, parse_json, TransportError

MAX_CLOUD_BODY = 6_100_000
MAX_BATCH = 8
MAX_FORWARD = STANDARD_CONCURRENCY + CONTROL_CONCURRENCY
MAX_SEEN = 4096


def read_cloud(response, limit=MAX_CLOUD_BODY):
    raw = response.read(limit + 1)
    if len(raw) > limit: raise ValueError('Relay response too large')
    return parse_json(raw)


def allowed_path(method, path):
    return method in ('GET', 'POST') and isinstance(path, str) and (
        path in {'/api/v1/models', '/v1/models', '/api/v1/chat/completions', '/v1/chat/completions',
                 '/api/alpha/decisions', '/bridge/v1/jobs', '/bridge/v1/preflight',
                 '/bridge/v1/model-capabilities', '/bridge/v1/models/refresh', '/bridge/v1/models/probe'}
        or path.startswith('/bridge/v1/jobs/') or path.startswith('/bridge/v1/receipts/'))


def decode_work(value, requested=MAX_BATCH):
    if 'requests' in value:
        if 'request' in value: raise ValueError('Ambiguous relay envelope')
        works = value['requests']
    else:
        works = [value['request']] if value.get('request') is not None else []
    if not isinstance(works, list) or len(works) > requested: raise ValueError('Invalid relay batch')
    ids = set(); normalized = []
    for work in works:
        if not isinstance(work, dict): raise ValueError('Invalid relay work')
        wid, path, method = work.get('id'), work.get('path'), work.get('method')
        try: valid_id = isinstance(wid, str) and str(uuid.UUID(wid)) == wid
        except ValueError: valid_id = False
        if not valid_id or wid in ids or not allowed_path(method, path): raise ValueError('Invalid relay work')
        authorization, body, deadline = (work.get(k) for k in ('authorization', 'body', 'deadline'))
        if (not isinstance(authorization, str) or not authorization.startswith('Bearer ')
                or len(authorization) > 263 or '\r' in authorization or '\n' in authorization
                or not isinstance(body, str) or len(body.encode()) > 3_000_000
                or type(deadline) not in (int, float) or not math.isfinite(deadline)
                or not 0 < deadline < 1e14 or deadline > (time.time() + 120) * 1000):
            raise ValueError('Invalid relay work')
        request_id = work.get('request_id')
        if request_id is not None and (not isinstance(request_id, str) or len(request_id) != 36
                                       or any(c not in '0123456789abcdefABCDEF-' for c in request_id)):
            raise ValueError('Invalid relay request ID')
        ids.add(wid)
        normalized.append(dict(id=wid, path=path, method=method, authorization=authorization,
                               body=body, deadline=deadline, request_id=request_id))
    return normalized


class Session:
    def __init__(self):
        self.id = uuid.uuid4().hex
        self.stop = threading.Event()
        self.condition = threading.Condition()
        self.pool = ThreadPoolExecutor(max_workers=STANDARD_CONCURRENCY, thread_name_prefix='relay-forward')
        self.control = ThreadPoolExecutor(max_workers=CONTROL_CONCURRENCY, thread_name_prefix='relay-control')
        self.poll = Connections(1, self.stop)
        self.results = Connections(8, self.stop)
        self.local = Connections(MAX_FORWARD, self.stop, local=True)
        self.inflight = set(); self.seen = {}
        self.counts = dict(poll_responses=0, batch_responses=0, legacy_responses=0,
                           works_dispatched=0, peak_inflight=0, protocol_errors=0,
                           duplicate_rejections=0, forward_errors=0, results_not_accepted=0,
                           result_delivery_retries=0)


class Relay:
    def __init__(self, store, port):
        self.store, self.port = store, port
        self.lock = threading.Lock()
        self.thread = None
        self.state = '未連線'
        self.cloud_opener = urllib.request.build_opener(NoRedirect(),
            urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
        self._reset()

    def _reset(self):
        self.session = Session()
        self.stop_event = self.session.stop
        self.agent_session = self.session.id
        self.pool, self.control_pool = self.session.pool, self.session.control

    def snapshot(self):
        session = self.session
        with session.condition:
            value = {**session.counts, 'inflight': len(session.inflight), 'forward_limit': MAX_FORWARD,
                     'batch_size': MAX_BATCH, 'seen_entries': len(session.seen), 'stopped': session.stop.is_set()}
        return {**value, 'poll': session.poll.snapshot(), 'results': session.results.snapshot(),
                'local': session.local.snapshot()}

    def start(self):
        with self.lock:
            if self.thread and self.thread.is_alive():
                if self.session.stop.is_set(): raise ValueError('Relay is still stopping.')
                return
            if not self.store.get('public_url'): raise ValueError('請先填入已部署的固定 HTTPS 網址。')
            if not secret.load(self.store.directory): raise ValueError('請先設定雲端轉接的裝置配對 key。')
            if self.session.stop.is_set(): self._reset()
            session = self.session
            self.thread = threading.Thread(target=self.loop, args=(session,), daemon=True, name='bridge-relay')
            self.thread.start()

    def state_for(self, session, text):
        with self.lock:
            if self.session is session and not session.stop.is_set(): self.state = text

    def stop(self):
        with self.lock:
            session, thread = self.session, self.thread
            session.stop.set(); self.state = '已停止'
        with session.condition: session.condition.notify_all()
        for transport in (session.poll, session.results, session.local): transport.close()
        session.pool.shutdown(wait=False, cancel_futures=True)
        session.control.shutdown(wait=False, cancel_futures=True)
        if thread and thread is not threading.current_thread(): thread.join(timeout=2)

    @staticmethod
    def finished(session, wid):
        with session.condition:
            session.inflight.discard(wid)
            session.condition.notify_all()

    def loop(self, session):
        backoff = 1
        while not session.stop.is_set():
            work = works = item = None
            try:
                with session.condition:
                    now = time.time()
                    session.seen = {wid: until for wid, until in session.seen.items() if until > now}
                    requested = min(MAX_BATCH, MAX_FORWARD - len(session.inflight))
                    if not requested:
                        session.condition.wait(.05); continue
                base = self.store.get('public_url').rstrip('/')
                device_key = secret.load(self.store.directory)
                with self.store.lock:
                    digests = [row[0] for row in self.store.db.execute('select digest from api_keys where revoked_ts is null')]
                item = session.poll.json(base, '/agent/poll', {
                    'key_digests': digests, 'agent_session': session.id, 'batch_size': requested}, device_key)
                if session.stop.is_set(): break
                works = decode_work(item, requested)
                with session.condition:
                    session.counts['poll_responses'] += 1
                    session.counts['batch_responses' if 'requests' in item else 'legacy_responses'] += 1
                    if any(w['id'] in session.seen for w in works):
                        session.counts['duplicate_rejections'] += 1
                        raise ValueError('Repeated relay work')
                    if len(session.seen) + len(works) > MAX_SEEN: raise ValueError('Relay ledger full')
                    for work in works:
                        session.seen[work['id']] = max(time.time(), work['deadline'] / 1000) + 2
                        session.inflight.add(work['id'])
                    session.counts['peak_inflight'] = max(session.counts['peak_inflight'], len(session.inflight))
                self.state_for(session, '已連線'); backoff = 1
                submitted = set()
                try:
                    for work in works:
                        if session.stop.is_set(): break
                        pool = session.pool if is_inference_request(work['method'], work['path']) else session.control
                        future = pool.submit(self.forward, work, base, device_key, session)
                        submitted.add(work['id'])
                        future.add_done_callback(lambda _, wid=work['id']: self.finished(session, wid))
                        with session.condition: session.counts['works_dispatched'] += 1
                finally:
                    for work in works:
                        if work['id'] not in submitted: self.finished(session, work['id'])
                work = works = item = None
            except Exception:
                work = works = item = None
                if session.stop.is_set(): break
                with session.condition: session.counts['protocol_errors'] += 1
                self.state_for(session, '離線／重連中')
                session.stop.wait(backoff + random.uniform(0, backoff * .25))
                backoff = min(20, backoff * 2)

    def forward(self, work, base, device_key, session=None):
        session = session or self.session
        result = None
        try:
            if session.stop.is_set(): return
            headers = {'Authorization': work['authorization'], 'Content-Type': 'application/json',
                       'X-Bridge-Deadline': str(work['deadline'])}
            if work.get('request_id'): headers['X-AIEA-Request-Id'] = work['request_id']
            timeout = max(.001, min(self.store.get('timeout_s') + 10, work['deadline'] / 1000 - time.time() + 5))
            status, raw, costs = session.local.exchange(f'http://127.0.0.1:{self.port}', work['path'], headers,
                work['body'].encode() if work['method'] == 'POST' else None,
                timeout=timeout, limit=4_000_000, success_only=False)
            result = {'id': work['id'], 'status': status, 'body': raw.decode(), 'headers': costs}
            delivery_deadline = work['deadline'] / 1000 + 2
            work = raw = None
            if session.stop.is_set(): return
            for attempt in range(2):
                try:
                    accepted = session.results.json(base, '/agent/result', result, device_key, limit=1000,
                        timeout=max(.001, min(30, delivery_deadline-time.time())), fresh=attempt > 0)
                    break
                except TransportError as error:
                    transient = str(error) in {'io','timeout','truncated_response'} or (
                        str(error) == 'http_status' and (error.status == 408 or (error.status or 0) >= 500))
                    if attempt or not transient or session.stop.is_set() or time.time() >= delivery_deadline:
                        raise
                    # Only redeliver this already computed result with the same work
                    # ID. Worker removes pending[id] before resolving the caller, so
                    # duplicate delivery cannot infer or resolve a caller twice.
                    with session.condition: session.counts['result_delivery_retries'] += 1
            if accepted.get('accepted') is not True:
                with session.condition: session.counts['results_not_accepted'] += 1
        except Exception:
            with session.condition: session.counts['forward_errors'] += 1
            self.state_for(session, '回傳中斷／等待下一筆請求')
        finally:
            work = result = None
