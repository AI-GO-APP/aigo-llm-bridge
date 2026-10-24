"""Real subprocess protocol: catalog failures must prevent inference."""
import sys
import threading
import time

import pytest

from desktop_bridge import providers
from desktop_bridge.codex_session import CodexSession
from desktop_bridge.errors import BridgeError
from desktop_bridge.tests.test_warm_cli_pilot import SCRIPT, spec_for


def connection(tmp_path, listing, *, verify_thread=False):
    script = SCRIPT.replace("result = {'data':[{'cwd':p['cwds'][0],'skills':[], 'errors':[]}]}",
                            'result = ' + repr(listing))
    if verify_thread:
        script = script.replace("model = p['model']", """
        assert p['ephemeral'] and p['sandbox']=='read-only' and p['approvalPolicy']=='never'
        assert p['dynamicTools']==[]
        assert p['config']=={'project_doc_max_bytes':0,'features.goals':False,
            'skills.config':[{'path':PATH,'enabled':False}]}
        model = p['model']""".replace('PATH', repr(str(tmp_path / 'SKILL.md'))))
    # The fake CLI receives its own cwd in skills/list, as the native protocol does.
    script = script.replace("'CWD'", "p['cwds'][0]")
    return CodexSession([sys.executable, '-u', '-c', script], tmp_path, None, threading.Event(), 2)


def test_current_catalog_disabled_on_ephemeral_thread_without_config_write(tmp_path, monkeypatch):
    personal = tmp_path / 'config.toml'
    personal.write_text('[features]\ngoals=true\n')
    monkeypatch.setattr(providers, 'inference_status', lambda *_: {'ready': True})
    session = connection(tmp_path, {'data':[{'cwd':'CWD', 'errors':[], 'skills':[
        {'path':str(tmp_path / 'SKILL.md'), 'enabled':True}]}]}, verify_thread=True)
    assert session.sent['skills/list'] == session.sent['thread/start'] == session.sent['turn/start'] == 0
    result = providers.call_codex(spec_for('synthetic answer'), {'timeout_s':2},
                                  threading.Event(), str(tmp_path), session=session)
    assert result[0] == 'synthetic answer'
    assert session.sent['skills/list'] == session.sent['thread/start'] == session.sent['turn/start'] == 1
    assert session.closed and session.child.proc.poll() is not None
    assert personal.read_text() == '[features]\ngoals=true\n'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['config.toml']


@pytest.mark.parametrize('listing', [
    None, {}, {'data':[]}, {'data':[{}, {}]},
    {'data':[{'cwd':'other', 'errors':[], 'skills':[]}]},
    {'data':[{'cwd':'CWD', 'errors':[{'message':'private error'}], 'skills':[]}]},
    {'data':[{'cwd':'CWD', 'errors':[], 'skills':[{'enabled':True,'path':'relative/SKILL.md'}]}]},
    {'data':[{'cwd':'CWD', 'errors':[], 'skills':[{'path':'/skill/SKILL.md'}]}]},
    {'data':[{'cwd':'CWD', 'errors':[], 'skills':[{'path':'/x\x00','enabled':True}]}]},
    {'data':[{'cwd':'CWD', 'errors':[], 'skills':[None]*513}]},
])
def test_invalid_catalog_stops_before_thread_and_turn(tmp_path, monkeypatch, listing):
    monkeypatch.setattr(providers, 'inference_status', lambda *_: {'ready':True})
    session = connection(tmp_path, listing)
    with pytest.raises(BridgeError) as error:
        providers.call_codex(spec_for('caller private text'), {'timeout_s':2},
                             threading.Event(), str(tmp_path), session=session)
    assert error.value.category == 'codex_context_unavailable'
    assert 'private' not in str(error.value)
    assert session.sent['thread/start'] == session.sent['turn/start'] == 0
    assert session.closed and session.child.proc.poll() is not None


def test_preclaim_rpc_cannot_write_or_query_other_cwd_and_is_single_use(tmp_path):
    session = connection(tmp_path, {'data':[{'cwd':'CWD', 'errors':[], 'skills':[]}]})
    cancel = threading.Event()
    deadline = time.monotonic()+2
    try:
        for method, params in [('skills/config/write', {'enabled':False}),
                               ('thread/start', {}), ('turn/start', {}),
                               ('skills/list', {'cwds':['/other'], 'forceReload':True})]:
            with pytest.raises(BridgeError):
                session.send(method, params, cancel, deadline)
        assert session.inference_config(cancel, deadline)['skills.config'] == []
        with pytest.raises(BridgeError):
            session.inference_config(cancel, deadline)
        session.claim(str(tmp_path))
        with pytest.raises(BridgeError):
            session.inference_config(cancel, deadline)
        assert session.sent['skills/list'] == 1
    finally:
        session.close()


def test_goals_override_is_child_only_and_preserves_personal_settings(tmp_path, monkeypatch):
    personal = tmp_path / 'config.toml'
    original = '[features]\ngoals=true\n[mcp_servers.example]\ncommand="personal"\n'
    personal.write_text(original)
    monkeypatch.setenv('CODEX_HOME', str(tmp_path))
    monkeypatch.setattr(providers, 'executable', lambda *_: 'synthetic-codex')
    command = providers.codex_command({})
    assert 'features.goals=false' in command
    assert 'mcp_servers.example.enabled=false' in command
    assert personal.read_text() == original


@pytest.mark.parametrize('cancelled', [False, True])
def test_catalog_wait_obeys_request_deadline_and_cancellation(tmp_path, monkeypatch, cancelled):
    monkeypatch.setattr(providers, 'inference_status', lambda *_: {'ready':True})
    script = SCRIPT.replace("if method == 'skills/list':", "if method == 'skills/list':\n        time.sleep(30)")
    cancel = threading.Event()
    session = CodexSession([sys.executable,'-u','-c',script],tmp_path,None,cancel,2)
    timer = threading.Timer(.05, cancel.set) if cancelled else None
    if timer:
        timer.start()
    began = time.monotonic()
    try:
        with pytest.raises(BridgeError):
            providers.call_codex(spec_for('private caller'), {'timeout_s':.15}, cancel,
                                 str(tmp_path), session=session)
        assert time.monotonic()-began < 2
        assert session.sent['thread/start'] == session.sent['turn/start'] == 0
        assert session.closed and session.child.proc.poll() is not None
    finally:
        if timer:
            timer.cancel()
        session.close()
