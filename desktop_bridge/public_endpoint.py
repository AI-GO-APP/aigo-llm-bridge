"""Public route checks without credentials or inference; evidence stays in RAM."""
import json
import re
import ssl
import threading
import time
import urllib.error
import urllib.request

import certifi

from . import __version__
from .connection_test import NoRedirect

ROUTES = {'decisions': ('POST', '/api/alpha/decisions'),
          'capabilities': ('GET', '/bridge/v1/model-capabilities'),
          'refresh': ('POST', '/bridge/v1/models/refresh'),
          'probe': ('POST', '/bridge/v1/models/probe')}


def inspect(origin):
    """Only unauthenticated requests: accepted paths stop at the auth gate."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
    result = {'checked_at': time.time(), 'worker_version': None, 'online': None, 'routes': {}}
    for name, (method, path) in {'health': ('GET', '/health'), **ROUTES}.items():
        req = urllib.request.Request(origin + path, method=method,
            data=b'{}' if method == 'POST' else None,
            headers={'User-Agent': 'local-token-buffet-route-check/1.0', 'Content-Type': 'application/json'})
        try:
            try: response = opener.open(req, timeout=5)
            except urllib.error.HTTPError as error: response = error
            with response:
                code = response.status
                if name == 'health' and code == 200:
                    value = json.loads(response.read(8193))
                    version = value.get('version')
                    if isinstance(version, str) and re.fullmatch(r'[0-9][0-9A-Za-z.\-]{0,40}', version):
                        result['worker_version'] = version
                    result['online'] = value.get('device_online') if type(value.get('device_online')) is bool else None
                elif name != 'health':
                    result['routes'][name] = {'http_status': code,
                        'state': 'reachable' if code == 401 else 'unsupported' if code == 404 else 'unknown'}
        except (OSError, ValueError, TypeError, AttributeError):
            if name != 'health': result['routes'][name] = {'http_status': None, 'state': 'unknown'}
    return result


class PublicEndpoint:
    def __init__(self, store):
        self.store = store
        self.lock = threading.Lock()
        self.origin = None
        self.result = {}
        self.tests = {}

    def snapshot(self):
        with self.lock:
            origin = self.store.get('public_url')
            if self.origin != origin:
                self.origin, self.result, self.tests = origin, {}, {}
            routes = self.result.get('routes', {})
            stale = bool(self.result) and time.time() - self.result['checked_at'] > 300
            states = [v['state'] for v in routes.values()]
            state = ('local_only' if not origin else 'unchecked' if not states or stale else
                     'needs_update' if 'unsupported' in states else
                     'routes_reachable' if len(states) == len(ROUTES) and all(s == 'reachable' for s in states) else 'unreachable')
            return {'local_version': __version__, 'origin': origin, 'state': state, 'stale': stale,
                    **self.result, 'tests': [dict(v) for v in self.tests.values()]}

    def check(self):
        origin = self.store.get('public_url')
        if not origin: return self.snapshot()
        result = inspect(origin)
        with self.lock:
            if self.store.get('public_url') == origin:
                if self.origin != origin: self.tests = {}
                self.origin, self.result = origin, result
        return self.snapshot()

    def observe(self, endpoint, model, protocol, result):
        with self.lock:
            if endpoint != self.store.get('public_url') + '/api/v1': return
            if self.origin != self.store.get('public_url'):
                self.origin, self.result, self.tests = self.store.get('public_url'), {}, {}
            self.tests[(model, protocol)] = {'model': model, 'protocol': protocol,
                'success': bool(result['success']), 'checked_at': time.time(),
                'http_status': result.get('http_status'), 'cost_usd': result.get('cost_usd')}
