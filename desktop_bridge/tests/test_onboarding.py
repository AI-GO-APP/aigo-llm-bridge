import json
import os
from pathlib import Path
import sys

import pytest

from desktop_bridge import secret
from desktop_bridge.byo import main
from desktop_bridge.handoff import integration
from desktop_bridge.store import Store


def test_one_time_handoff_scopes_and_no_secret_readback(tmp_path,capsys):
    store=Store(tmp_path);store.set('public_url','https://my-device.my-owner.workers.dev');store.close()
    assert main(['key-create','--data-dir',str(tmp_path),'--providers','codex','--label','consumer','--handoff'])==0
    once=json.loads(capsys.readouterr().out);info=once['integration']
    assert once['key'] in info['prompt'] and info['contains_key']
    assert info['config']['model']=='openai/gpt-6-astra' and info['config']['max_retries']==0
    assert info['config']['base_url']=='https://my-device.my-owner.workers.dev/api/v1'
    assert info['request']['stream'] is False and set(info['request'])=={'model','messages','stream'}
    assert main(['handoff','--data-dir',str(tmp_path),'--providers','codex'])==0
    public=json.loads(capsys.readouterr().out)
    assert not public['contains_key'] and once['key'] not in json.dumps(public)
    store=Store(tmp_path,startup=False)
    with pytest.raises(ValueError):integration(store,'anthropic/claude-haiku-4.5',['codex'])
    assert once['key'] not in '\n'.join(store.db.iterdump())
    store.close()


def test_failed_handoff_creates_no_orphan_key(tmp_path,capsys):
    assert main(['key-create','--data-dir',str(tmp_path),'--label','missing URL','--handoff'])==1
    store=Store(tmp_path,startup=False);assert not store.keys();store.close();capsys.readouterr()


def test_new_install_default_never_calls_claude_when_model_is_omitted(tmp_path):
    from desktop_bridge.contract import validate
    store=Store(tmp_path);_,key=store.create_key('codex only',['codex'])
    spec=validate({'messages':[{'role':'user','content':'synthetic'}]},store,store.authenticate(key))
    assert spec.model['provider']=='codex'
    store.close()


def test_windows_npm_codex_uses_native_binary_without_running_shell(tmp_path):
    from desktop_bridge.providers import executable
    from desktop_bridge.errors import BridgeError
    shim=tmp_path/'codex.cmd';shim.write_text('Must never execute this shell shim')
    with pytest.raises(BridgeError):executable('codex',{'codex_path':str(shim)})
    native=tmp_path/'node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/codex/codex.exe'
    native.parent.mkdir(parents=True);native.write_bytes(b'native fixture')
    assert executable('codex',{'codex_path':str(shim)})==str(native.resolve())


def test_keychain_pending_commit_stays_out_of_files(tmp_path,monkeypatch):
    values={}
    class FakeKeychain:
        def get(self,key):return values.get(key,'')
        def put(self,key,value):values[key]=value
        def delete(self,key):values.pop(key,None)
    monkeypatch.setattr(secret,'uses_keychain',lambda:True)
    monkeypatch.setattr('desktop_bridge.keychain.Keychain',FakeKeychain)
    token='test-device-'+'x'*48
    secret.save(tmp_path,token,pending=True)
    assert secret.load(tmp_path)=='' and secret.load(tmp_path,pending=True)==token
    secret.commit_pending(tmp_path)
    assert secret.load(tmp_path)==token and secret.load(tmp_path,pending=True)==''
    assert not list(tmp_path.iterdir())
    assert secret.load(tmp_path/'another-profile')==''


@pytest.mark.skipif(os.name=='nt',reason='POSIX profile locks')
def test_posix_single_instance_activation_and_restart(tmp_path):
    from desktop_bridge.windows import Instance
    one=Instance(tmp_path);two=Instance(tmp_path)
    try:
        assert one.primary and not two.primary
        two.notify();assert one.requested() and not one.requested()
    finally:two.close();one.close()
    three=Instance(tmp_path);assert three.primary;three.close()


def test_macos_launch_agent_preserves_arguments_and_has_no_payload_logs(tmp_path,monkeypatch):
    import plistlib
    from desktop_bridge import windows
    monkeypatch.setattr(windows.sys,'platform','darwin')
    monkeypatch.setattr(windows.Path,'home',lambda:tmp_path)
    data=tmp_path/'profile with spaces'
    windows.set_startup(True,data)
    config=plistlib.loads(windows.mac_startup_path(data).read_bytes())
    assert config['ProgramArguments'][-3:]==['--data-dir',str(data.resolve()),'--background']
    assert config['StandardOutPath']==config['StandardErrorPath']=='/dev/null'
    assert config['RunAtLoad'] and windows.startup_enabled(data)
    windows.set_startup(False,data);assert not windows.startup_enabled(data)


def test_source_installer_preserves_identity_across_reinstall(tmp_path,monkeypatch):
    from tools import install as installer
    # Runtime acceptance installs real dependencies; the unit test only verifies profile ownership.
    monkeypatch.setattr(installer.venv.EnvBuilder,'create',lambda self,path:Path(path).mkdir())
    root=tmp_path/'source install 測試';data=tmp_path/'device profile 資料'
    first=installer.install(root,data,dependencies=False)
    if os.name=='nt':(root/'Bridge.cmd').read_text(encoding='ascii')
    store=Store(data);device=store.get('device_id');_,key=store.create_key('preserve');store.set('public_url','https://fixed.example.test');store.close()
    second=installer.install(root,dependencies=False)
    assert second['data_dir']==first['data_dir'] and second['app']!=first['app']
    assert Path(first['app']).is_dir() and Path(second['app']).is_dir()
    store=Store(data);assert store.get('device_id')==device and store.authenticate(key) and store.get('public_url')=='https://fixed.example.test';store.close()
    before=(root/'source-install.json').read_bytes()
    with pytest.raises(ValueError):installer.install(root,tmp_path/'other',dependencies=False)
    assert (root/'source-install.json').read_bytes()==before
