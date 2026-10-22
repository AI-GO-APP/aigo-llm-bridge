import importlib.util
import json
import os
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'desktop'))
import aigo_desktop as d


def test_setup_preserves_key_and_refreshes_registration(tmp_path, monkeypatch):
    monkeypatch.setattr(d, 'discover', lambda n: '/bin/' + n)
    monkeypatch.setattr(d, 'login_status', lambda n, p: n == 'codex')
    first = d.setup(tmp_path, 8790)
    second = d.setup(tmp_path, 8792)
    assert first['api_key'] == second['api_key']
    assert second['port'] == 8792
    assert second['providers']['codex']['logged_in']
    if os.name != 'nt':
        assert (tmp_path / d.CONFIG_NAME).stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize('req', [[], {}, {'model': '--bad'}, {'model': 'codex', 'messages': []},
    {'model': 'codex', 'messages': [{'role': 'user', 'content': []}]},
    {'model': 'codex', 'messages': [{'role': 'assistant', 'content': 'hi'}]},
    {'model': 'claude', 'stream': True}])
def test_invalid_requests_rejected(req):
    with pytest.raises(d.DesktopError) as exc:
        d.render_request(req)
    assert exc.value.status == 400


def test_auth_malformed_busy_and_completion(tmp_path, monkeypatch):
    cfg = {'api_key': 'test-key', 'providers': {}, 'port': 8790}
    monkeypatch.setattr(d, 'complete', lambda c, r, h: {'result': 'ok'})
    server = ThreadingHTTPServer(('127.0.0.1', 0), d.make_handler(cfg, tmp_path))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    def request(path, body=None, key='test-key'):
        return urllib.request.urlopen(urllib.request.Request(base + path, data=body,
            headers={'Authorization': 'Bearer ' + key}), timeout=5)
    try:
        for path in ('/', '/v1', '/v1/'):
            with urllib.request.urlopen(base + path, timeout=5) as response:
                page = response.read().decode('utf-8')
                assert response.status == 200
                assert response.headers['Content-Type'].startswith('text/html')
                assert response.headers['Cache-Control'] == 'no-store'
                assert "frame-ancestors 'none'" in response.headers['Content-Security-Policy']
                assert '測試連線' in page and 'http://127.0.0.1:8790/v1' in page
                assert cfg['api_key'] not in page
                assert 'localStorage' not in page and 'sessionStorage' not in page
        for path in ('/v1/models', '/healthz'):
            with pytest.raises(urllib.error.HTTPError) as exc:
                urllib.request.urlopen(base + path, timeout=5)
            assert exc.value.code == 401
        with pytest.raises(urllib.error.HTTPError) as exc:
            request('/v1/models', key='bad')
        assert exc.value.code == 401
        with pytest.raises(urllib.error.HTTPError) as exc:
            request('/v1/chat/completions', b'{bad')
        assert exc.value.code == 400
        body = json.dumps({'model': 'codex', 'messages': [{'role': 'user', 'content': 'hi'}]}).encode()
        with request('/v1/chat/completions', body) as response:
            assert json.load(response) == {'result': 'ok'}
        d.LOCK.acquire()
        try:
            with pytest.raises(urllib.error.HTTPError) as exc:
                request('/v1/chat/completions', body)
            assert exc.value.code == 429
        finally:
            d.LOCK.release()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize('provider', ['claude', 'codex'])
def test_provider_commands_and_failures(provider, tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(d, 'login_status', lambda *_: True)
    def run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        if provider == 'codex':
            Path(cmd[cmd.index('--output-last-message') + 1]).write_text('answer')
        return subprocess.CompletedProcess(cmd, 0, json.dumps({'result': 'answer'}), '')
    monkeypatch.setattr(d, 'run_cli', run)
    cfg = {'providers': {provider: {'executable': '/some path/cli'}}}
    req = {'model': provider, 'messages': [{'role': 'user', 'content': 'hello'}]}
    result = d.complete(cfg, req, tmp_path)
    assert result['choices'][0]['message']['content'] == 'answer'
    cmd, args = calls[0]
    assert args['input'] == '[user]\nhello'
    assert 'hello' not in cmd
    assert list(tmp_path.iterdir()) == []
    if provider == 'codex':
        assert '--ignore-user-config' in cmd and '--sandbox' in cmd
        assert 'features.shell_tool=false' in cmd and 'forced_login_method="chatgpt"' in cmd
    else:
        assert cmd[cmd.index('--tools') + 1] == '' and '--strict-mcp-config' in cmd
    monkeypatch.setattr(d, 'run_cli', lambda *_a, **_k: subprocess.CompletedProcess([], 1, 'bad', 'private'))
    with pytest.raises(d.DesktopError) as exc:
        d.complete(cfg, req, tmp_path)
    assert exc.value.code == 'provider_failed' and 'private' not in exc.value.message


def test_missing_login_fails_before_inference(tmp_path, monkeypatch):
    monkeypatch.setattr(d, 'login_status', lambda *_: False)
    with pytest.raises(d.DesktopError) as exc:
        d.complete({'providers': {}}, {'model': 'codex', 'messages': [{'role': 'user', 'content': 'hi'}]}, tmp_path)
    assert exc.value.code == 'login_required'


def test_api_credentials_are_not_inherited(monkeypatch):
    for name in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'ANTHROPIC_API_KEY', 'CLAUDE_CODE_OAUTH_TOKEN'):
        monkeypatch.setenv(name, 'private')
        assert name not in d.cli_env()


@pytest.mark.parametrize('method,expected', [('claude.ai', True), ('oauth', False), ('api_key', False), ('none', False)])
def test_claude_subscription_login_methods(method, expected, monkeypatch):
    monkeypatch.setattr(d, 'run_cli', lambda *_a, **_kw: subprocess.CompletedProcess([], 0,
        json.dumps({'loggedIn': True, 'authMethod': method}), ''))
    assert d.login_status('claude', '/cli') is expected


def test_package_has_only_selected_platform_and_public_files(tmp_path):
    import zipfile
    spec = importlib.util.spec_from_file_location('desktop_builder', ROOT / 'packaging/build_desktop.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    for target, other in [('macos', 'windows'), ('windows', 'macos')]:
        package = builder.build(target, tmp_path / target)
        with zipfile.ZipFile(package) as z:
            names = z.namelist()
        assert any(f'desktop_platform/{target}/install.py' in p for p in names)
        assert not any(f'desktop_platform/{other}/' in p or p.endswith('desktop.json') for p in names)
