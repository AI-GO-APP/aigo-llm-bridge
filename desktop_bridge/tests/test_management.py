import json
import threading
import urllib.error
import urllib.request

import pytest

from desktop_bridge.management import ManagementServer
from desktop_bridge.service import ApiServer, Runtime
from desktop_bridge.store import Store


@pytest.fixture
def console(tmp_path, monkeypatch):
    monkeypatch.setattr("desktop_bridge.management.providers.status", lambda p, s: {"ready": True})
    monkeypatch.setattr("desktop_bridge.management.startup_enabled", lambda *_: False)
    store = Store(tmp_path)
    runtime = Runtime(store, lambda *_: ("OK", {'prompt_tokens':1,'completion_tokens':1}, "stop"))
    api = ApiServer(runtime, 0)
    api.start()
    done = threading.Event()
    manager = ManagementServer(store, runtime, api, on_shutdown=done.set)
    manager.start()
    yield manager, done
    manager.stop(); runtime.stop(); api.stop(); store.close()


def request(manager, path="/manage/state", data=None, headers=None):
    req = urllib.request.Request(manager.origin + path, data=json.dumps(data).encode() if data is not None else None,
        headers={"Authorization": "Bearer " + manager.token, "Content-Type": "application/json", **(headers or {})})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try: response = opener.open(req, timeout=5)
    except urllib.error.HTTPError as error: response = error
    with response:
        body = response.read()
        return response.status, json.loads(body) if "application/json" in response.headers.get("Content-Type", "") else body, response.headers


def test_local_boundary_and_static_assets(console):
    manager, _ = console
    assert manager.server.server_address[0] == "127.0.0.1"
    assert request(manager, headers={"Authorization": ""})[0] == 401
    assert request(manager, headers={"Origin": "https://external.example"})[0] == 403
    assert request(manager, headers={"Host": "rebind.example"})[0] == 403
    assert request(manager, "/manage/accepting", {"accepting": False}, {"Origin":"https://external.example"})[0] == 403
    assert manager.store.get("accepting") is True
    for path in ("/", "/app.js", "/platform.js", "/integration.js", "/style.css"):
        code, body, headers = request(manager, path, headers={"Authorization":""})
        assert code == 200 and body
        assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
        assert headers["Cache-Control"] == "no-store"
        assert manager.token.encode() not in body
        assert "Access-Control-Allow-Origin" not in headers
    assert request(manager, "/../store.py")[0] == 404


def test_key_lifecycle_and_no_secret_readback(console):
    m, _ = console
    code, created, _ = request(m, "/manage/keys/create", {"label":"UI test", "providers":["claude"], "rpm":12})
    assert code == 200
    assert m.store.authenticate(created["token"])["rpm"] == 12
    _, state, _ = request(m)
    assert created["token"] not in json.dumps(state)
    assert "digest" not in state["keys"][0]
    assert state["keys"][0]["label"] == "UI test"
    code, rotated, _ = request(m, "/manage/keys/rotate", {"id":created["id"]})
    assert code == 200 and m.store.authenticate(created["token"]) is None
    assert m.store.authenticate(rotated["token"])
    assert request(m, "/manage/keys/revoke", {"id":rotated["id"]})[0] == 200
    assert m.store.authenticate(rotated["token"]) is None
    assert request(m, "/manage/keys/rotate", {"id":rotated["id"]})[0] == 400


def test_new_keys_default_to_all_providers_and_future_registered_models(console):
    m,_=console
    code,created,_=request(m,'/manage/keys/create',{'label':'All models by default'})
    assert code==200
    caller=m.store.authenticate(created['token'])
    assert caller['providers']==['claude','codex']
    models=m.store.get('models')+[{'id':'synthetic/new-model','provider':'codex','native':'synthetic-new'}]
    m.store.set('models',models)
    assert all(item['provider'] in caller['providers'] for item in models)
    assert request(m,'/manage/keys/create',{'label':'Explicit empty is invalid','providers':[]})[0]==400
    _,restricted,_=request(m,'/manage/keys/create',{'label':'Restricted','providers':['codex']})
    assert m.store.authenticate(restricted['token'])['providers']==['codex']
    _,rotated,_=request(m,'/manage/keys/rotate',{'id':restricted['id']})
    assert m.store.authenticate(rotated['token'])['providers']==['codex']


def test_settings_validate_before_writing_and_persist(console):
    m, _ = console
    values = {**m.state()["settings"], "startup":False}
    assert request(m, "/manage/settings", {**values, "port":80, "public_url":"https://valid.example"})[0] == 400
    assert m.store.get("public_url") == ""
    assert request(m, "/manage/settings", {**values, "public_url":"https://bad.example/api/v1"})[0] == 400
    assert request(m, "/manage/settings", {**values, "models":[]})[0] == 400
    assert request(m, "/manage/settings", {**values, "relay_enabled":True})[0] == 400
    values.update(public_url="https://bridge.example", retention_days=7, timeout_s=90)
    assert request(m, "/manage/settings", values)[0] == 200
    assert m.state()["endpoint"] == "https://bridge.example/api/v1"
    reader = Store(m.store.directory, startup=False)
    assert reader.get("retention_days") == 7
    reader.close()


def test_settings_save_preserves_default_provider_and_explicit_owner_choice(console):
    m,_=console
    assert m.store.get('default_model')=='openai/gpt-6-astra'
    assert request(m,'/manage/settings',{**m.state()['settings'],'startup':False})[0]==200
    assert m.store.get('default_model')=='openai/gpt-6-astra'
    m.store.set('default_model','anthropic/claude-haiku-4.5')
    assert request(m,'/manage/settings',{**m.state()['settings'],'startup':False})[0]==200
    assert m.store.get('default_model')=='anthropic/claude-haiku-4.5'


def test_filters_export_clear_and_pause(console):
    m, done = console
    import time
    for rid, status, provider in (("a", "completed", "claude"), ("b", "failed", "codex"), ("c", "running", "claude")):
        m.store.insert_request({"id":rid, "created_ts":time.time(), "status":status, "provider":provider, "model":"=formula"})
    assert request(m, "/manage/logs?status=completed&provider=claude")[1]["logs"][0]["id"] == "a"
    assert len(request(m, "/manage/logs?provider=codex")[1]["logs"]) == 1
    code, csv, _ = request(m, "/manage/export?provider=codex")
    assert code == 200 and b"codex" in csv and b"claude" not in csv and b"'=formula" in csv
    assert request(m, "/manage/accepting", {"accepting":False})[0] == 200
    assert m.store.get("accepting") is False
    assert request(m, "/manage/accepting", {"accepting":"false"})[0] == 400
    assert request(m, "/manage/logs/clear", {})[0] == 200
    assert [r["id"] for r in m.store.logs()] == ["c"]
    assert request(m, "/manage/shutdown", {})[0] == 200 and done.is_set()


def test_inference_port_cannot_manage(console):
    m, _ = console
    _, token = m.store.create_key("inference only")
    req = urllib.request.Request(f"http://127.0.0.1:{m.api.port}/manage/state", headers={"Authorization":"Bearer " + token})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with pytest.raises(urllib.error.HTTPError) as error: opener.open(req, timeout=5)
    assert error.value.code == 404


def test_connection_uses_real_client_api_and_keeps_only_metadata(console):
    m, _ = console
    m.runtime.runner = lambda *_: ('PONG', {'prompt_tokens':1,'completion_tokens':1}, 'stop')
    _, key = m.store.create_key('test client')
    before = m.store.keys()
    for model in m.store.get('models'):
        code, result, _ = request(m, '/manage/test-connection', {
            'key': key, 'provider': model['provider'], 'model': model['id'], 'endpoint': m.state()['endpoint']})
        assert code == 200 and result['success'] and result['http_status'] == 200
        assert result['elapsed_ms'] >= 0 and result['endpoint'] == m.state()['endpoint']
        assert key not in json.dumps(result)
    assert m.store.keys() == before
    assert len(m.store.logs()) == 2
    persisted = '\n'.join(m.store.db.iterdump())
    assert key not in persisted and 'Reply exactly PONG.' not in persisted
    assert 'PONG' not in json.dumps(m.state())


def test_connection_rejects_bad_keys_scopes_and_unconfigured_targets(console, monkeypatch):
    m, _ = console
    def forbidden_probe(*_): raise AssertionError('Unexpected outbound request')
    monkeypatch.setattr('desktop_bridge.management.probe', forbidden_probe)
    kid, key = m.store.create_key('claude only', ['claude'])
    model = next(mo for mo in m.store.get('models') if mo['provider'] == 'codex')
    body = {'key': key, 'provider': 'codex', 'model': model['id'], 'endpoint': m.state()['endpoint']}
    assert request(m, '/manage/test-connection', body)[1]['code'] == 'scope_denied'
    assert request(m, '/manage/test-connection', {**body, 'key':'bad'})[1]['code'] == 'invalid_key'
    m.store.revoke(kid)
    assert request(m, '/manage/test-connection', body)[1]['code'] == 'invalid_key'
    for changes in ({'endpoint':'https://other.example/api/v1'}, {'model':'not-registered'}, {'provider':'other'}, {'key':''}):
        assert request(m, '/manage/test-connection', {**body, **changes})[0] == 400
    assert request(m, '/manage/test-connection', body, {'Authorization':''})[0] == 401
    assert request(m, '/manage/test-connection', body, {'Origin':'https://other.example'})[0] == 403
    assert not m.store.logs()


def test_connection_does_not_block_management_and_prevents_duplicate_probe(console, monkeypatch):
    m, _ = console
    _, key = m.store.create_key('probe lock')
    model = m.store.get('models')[0]
    body = {'key':key, 'provider':model['provider'], 'model':model['id'], 'endpoint':m.state()['endpoint']}
    started, release = threading.Event(), threading.Event()
    def slow_probe(*_):
        started.set(); release.wait(3)
        return {'success':False, 'code':'timeout', 'message':'Timed out'}
    monkeypatch.setattr('desktop_bridge.management.probe',slow_probe)
    t = threading.Thread(target=lambda: request(m,'/manage/test-connection',body))
    t.start()
    try:
        assert started.wait(2)
        assert request(m)[0] == 200
        assert request(m,'/manage/accepting',{'accepting':False})[0] == 200
        assert request(m,'/manage/test-connection',body)[1]['code'] == 'busy'
    finally: release.set(); t.join(3)


def test_probe_blocks_redirects_and_does_not_leak_response_data():
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from desktop_bridge.connection_test import probe
    paths = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_): pass
        def do_POST(self):
            paths.append(self.path)
            self.send_response(307)
            self.send_header('Location','/stolen')
            self.end_headers()
        def do_GET(self):
            paths.append(self.path)
            self.send_response(200); self.end_headers()
    server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread = threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    try:
        result=probe(f'http://127.0.0.1:{server.server_port}','model','test-secret')
        assert result['code']=='redirect_blocked' and not result['success']
        assert paths==['/chat/completions']
        assert 'test-secret' not in json.dumps(result)
    finally: server.shutdown(); server.server_close(); thread.join()


@pytest.mark.parametrize('status,body,expected', [
    (200,b'not json secret','unexpected_response'),
    (200,b'{"choices":[{"message":{"content":"wrong response secret"}}]}','unexpected_response'),
    (401,b'secret','unauthorized'), (403,b'secret','forbidden'),
    (429,b'secret','rate_limited'), (503,b'secret','unavailable'),
])
def test_probe_error_classification_is_sanitized(monkeypatch,status,body,expected):
    from desktop_bridge.connection_test import probe
    import io
    class Response(io.BytesIO): pass
    class Opener:
        def open(self,*args,**kwargs):
            response=Response(body); response.status=status
            return response
    monkeypatch.setattr('desktop_bridge.connection_test.urllib.request.build_opener',lambda *_:Opener())
    result=probe('https://bridge.example/api/v1','model','test-secret')
    assert result['code']==expected and not result['success']
    assert 'secret' not in json.dumps(result)
