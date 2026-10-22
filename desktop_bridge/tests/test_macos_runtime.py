"""Regression coverage for Mac privacy, launch paths and billing metadata."""
import json
import os
from pathlib import Path
import plistlib

import pytest

from desktop_bridge.store import Store


@pytest.mark.skipif(os.name == 'nt', reason='POSIX permissions')
def test_profile_and_sqlite_are_owner_only(tmp_path):
    profile = tmp_path / 'private data'
    store = Store(profile)
    try:
        assert profile.stat().st_mode & 0o777 == 0o700
        for name in ('bridge.sqlite','bridge.sqlite-wal','bridge.sqlite-shm'):
            assert (profile / name).stat().st_mode & 0o077 == 0
    finally: store.close()


def test_launch_agent_follows_installed_manifest_after_update(tmp_path, monkeypatch):
    from desktop_bridge import windows
    monkeypatch.setattr(windows.sys, 'platform', 'darwin')
    monkeypatch.setattr(windows.Path, 'home', lambda: tmp_path)
    root = tmp_path / 'installation with spaces'
    module = root / 'versions/old/desktop_bridge/windows.py'
    module.parent.mkdir(parents=True); module.touch()
    data = root / 'data'
    manifest = {'python':str(root / 'runtime/bin/python'), 'app':str(root / 'versions/new'), 'data_dir':str(data)}
    (root / 'source-install.json').write_text(json.dumps(manifest))
    monkeypatch.setattr(windows, '__file__', str(module))
    windows.set_startup(True, data)
    value = plistlib.loads(windows.mac_startup_path(data).read_bytes())
    assert value['ProgramArguments'] == [manifest['python'], str(root/'Bridge.pyw'), '--background']
    assert value['KeepAlive'] == {'SuccessfulExit':False}
    assert value['StandardErrorPath'] == '/dev/null'


def test_token_detail_migration_preserves_identity_and_keys(tmp_path):
    store = Store(tmp_path); device = store.get('device_id'); kid, token = store.create_key('service',['codex'])
    store.insert_request({'id':'test','key_id':kid,'status':'completed','prompt_tokens':42,'completion_tokens':12,
                          'cached_tokens':10,'reasoning_tokens':2,'cost_usd':0.1})
    store.close()
    store = Store(tmp_path)
    try:
        assert store.get('device_id') == device and store.authenticate(token)['id'] == kid
        assert store.logs()[0]['cached_tokens'] == 10
        assert store.logs()[0]['reasoning_tokens'] == 2
    finally: store.close()


def test_codex_inference_overrides_never_modify_personal_config():
    from desktop_bridge.providers import codex_command
    command = codex_command({})
    assert 'history.persistence="none"' in command
    assert 'features.shell_snapshot=false' in command
    assert 'features.hooks=false' in command
    assert 'features.code_mode_host=false' in command
    assert 'service_tier="default"' in command


def test_native_handoff_keeps_secret_in_stdin_and_out_of_output(tmp_path, monkeypatch, capsys):
    import io
    from types import SimpleNamespace
    from tools import mac_key_handoff
    repo=Path(__file__).resolve().parents[2]
    data=tmp_path/'data'
    (tmp_path/'source-install.json').write_text(json.dumps({'app':str(repo),'data_dir':str(data)}))
    store=Store(data);store.set('public_url','https://mac.example.test')
    store.set('models',[{'id':'openai/gpt-6-luna','native':'gpt-6-luna','provider':'codex'}]);store.set('default_model','openai/gpt-6-luna');store.close()
    monkeypatch.setattr(mac_key_handoff.sys,'platform','darwin')
    def network(request,**kwargs):
        body={'data':[]} if request.full_url.endswith('/models') else {
            'model':'openai/gpt-6-luna','choices':[{'message':{'content':'OWNER_SERVICE_READY'}}],
            'usage':{'prompt_tokens':1,'completion_tokens':1,'cost':0.01}}
        return io.BytesIO(json.dumps(body).encode())
    monkeypatch.setattr(mac_key_handoff.urllib.request,'urlopen',network)
    scripts=[]
    def dialog(command,**kwargs):
        assert command==['/usr/bin/osascript','-']
        scripts.append(kwargs['input'].decode())
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(mac_key_handoff.subprocess,'run',dialog)
    assert mac_key_handoff.deliver(tmp_path,'owner service',60)==0
    output=capsys.readouterr().out
    import re
    key=re.search(r'sk-br-[A-Za-z0-9_-]+',scripts[0])[0]
    assert key not in output
    store=Store(data,startup=False)
    assert store.authenticate(key)['providers']==['codex']
    assert key not in '\n'.join(store.db.iterdump())
    store.close()
