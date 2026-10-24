import io
import json
from types import SimpleNamespace

import pytest

from desktop_bridge import providers
from desktop_bridge.contract import Inference
from desktop_bridge.errors import BridgeError
from desktop_bridge.store import Store
from desktop_bridge.tests.conftest import REAL_MODEL_SNAPSHOT, REAL_AUTH_GENERATION


def test_codex_discovery_handshake_pagination_never_starts_a_thread(tmp_path,monkeypatch):
    stream=b''.join((json.dumps(row)+'\n').encode() for row in [
        {'id':1,'result':{}},
        {'id':2,'result':{'data':[{'model':'first'},{'model':'hidden','hidden':True}],'nextCursor':'page2'}},
        {'id':3,'result':{'data':[{'model':'second'}],'nextCursor':None}}])
    proc=SimpleNamespace(stdin=io.BytesIO(),stdout=io.BytesIO(stream),stderr=io.BytesIO())
    closed=[]
    monkeypatch.setattr(providers,'Child',lambda *_:SimpleNamespace(proc=proc,close=lambda:closed.append(True)))
    monkeypatch.setattr(providers,'codex_command',lambda _:['test-cli'])
    assert providers.list_codex_models({})==['first','second']
    sent=[json.loads(line) for line in proc.stdin.getvalue().splitlines()]
    assert [m['method'] for m in sent]==['initialize','initialized','model/list','model/list']
    assert sent[-1]['params']['cursor']=='page2' and closed


def test_claude_discovery_does_not_use_an_api_key_catalog(monkeypatch):
    # Restore the concrete implementation replaced by the suite's no-network fixture.
    monkeypatch.setattr(providers,'status',lambda *a,**k:{'ready':True})
    monkeypatch.setattr(providers,'list_codex_models',lambda *_:pytest.fail('wrong provider'))
    assert REAL_MODEL_SNAPSHOT('claude',{})=={'ready':True,'models':None,'source':'registration'}


def test_login_file_change_invalidates_evidence_without_reading_credentials(tmp_path,monkeypatch):
    monkeypatch.setenv('CODEX_HOME',str(tmp_path))
    monkeypatch.setattr(providers,'executable',lambda *_:str(tmp_path/'cli.exe'))
    (tmp_path/'cli.exe').write_bytes(b'fake binary')
    first=REAL_AUTH_GENERATION('codex',{'codex_path':''})
    (tmp_path/'auth.json').write_bytes(b'synthetic login metadata')
    second=REAL_AUTH_GENERATION('codex',{'codex_path':''})
    assert first!=second
    assert 'synthetic' not in second


@pytest.mark.parametrize('actual',['expected',None,'unexpected'])
def test_claude_actual_model_is_checked_before_pricing(tmp_path,monkeypatch,actual):
    events=[{'type':'result','result':'synthetic','usage':{'input_tokens':1,'output_tokens':1}}]
    if actual:events.insert(0,{'type':'system','subtype':'init','model':actual})
    raw=b''.join((json.dumps(e)+'\n').encode() for e in events)
    monkeypatch.setattr(providers,'status',lambda *_,**kwargs:{'ready':True})
    monkeypatch.setattr(providers,'executable',lambda *_:'test-cli')
    monkeypatch.setattr(providers,'Child',lambda *_:SimpleNamespace(proc=SimpleNamespace(returncode=0),
                                                                   communicate=lambda *_:raw,close=lambda:None))
    spec=Inference({'provider':'claude','native':'expected','id':'alias'},[{'role':'user','parts':[{'type':'text','text':'synthetic'}]}],'',None,'text',None)
    if actual=='expected':
        assert providers.call_claude(spec,{'timeout_s':1},None,tmp_path)[3]=='expected'
    else:
        with pytest.raises(BridgeError) as error:providers.call_claude(spec,{'timeout_s':1},None,tmp_path)
        assert error.value.category==('model_mismatch' if actual else 'model_identity_unavailable')
