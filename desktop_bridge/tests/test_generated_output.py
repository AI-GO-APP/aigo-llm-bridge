import json
import threading
from types import SimpleNamespace

import pytest

from desktop_bridge import providers
from desktop_bridge.decision_contract import DecisionSpec
from desktop_bridge.decisions import answer
from desktop_bridge.errors import BridgeError


@pytest.mark.parametrize('kind,criteria,value',[
    ('noul',None,{'noul':.9}),
    ('choice',{'private-label-a':'private-description','private-label-b':None},{'probabilities':[.2,.8]}),
    ('score',['private-legend-a','private-legend-b'],{'probabilities':[.2,.8]})])
def test_only_fixed_structure_and_count_enter_claude_argv(monkeypatch,tmp_path,kind,criteria,value):
    question={'type':kind,'instructions':'private-instruction','criteria':criteria}
    decision=DecisionSpec({'provider':'claude','native':'test','id':'alias'},'private-state',{'q':question})
    spec=decision.inference(question);captured={}
    class Child:
        proc=SimpleNamespace(returncode=0)
        def __init__(self,command,*_):captured['command']=command
        def communicate(self,payload,*_):
            captured['payload']=payload.decode()
            return json.dumps({'type':'result','structured_output':value,'usage':{'input_tokens':1,'output_tokens':1},'modelUsage':{'test':{}}}).encode()
        def close(self):pass
    monkeypatch.setattr(providers,'status',lambda *_,**kwargs:{'ready':True})
    monkeypatch.setattr(providers,'executable',lambda *_:'synthetic-cli')
    monkeypatch.setattr(providers,'Child',Child)
    text,*_=providers.call_claude(spec,{'timeout_s':2},threading.Event(),tmp_path)
    assert answer(text,question,spec.schema)['type']==kind
    command=captured['command'];schema=json.loads(command[command.index('--json-schema')+1])
    assert schema==spec.schema and 'private-' not in ' '.join(command)
    assert 'private-state' in captured['payload'] and 'private-instruction' in captured['payload']
    assert '--no-session-persistence' in command and '--tools' in command and '--restricted' in command


def test_generated_schema_requires_native_structured_output(monkeypatch,tmp_path):
    question={'type':'noul','instructions':'synthetic'}
    spec=DecisionSpec({'native':'test'},'synthetic',{'q':question}).inference(question)
    raw=json.dumps({'type':'result','result':'{"noul":0.9}','usage':{'input_tokens':1,'output_tokens':1},'modelUsage':{'test':{}}}).encode()
    monkeypatch.setattr(providers,'status',lambda *_,**kwargs:{'ready':True})
    monkeypatch.setattr(providers,'executable',lambda *_:'synthetic-cli')
    monkeypatch.setattr(providers,'Child',lambda *_:SimpleNamespace(proc=SimpleNamespace(returncode=0),communicate=lambda *_:raw,close=lambda:None))
    with pytest.raises(BridgeError) as error:providers.call_claude(spec,{'timeout_s':2},threading.Event(),tmp_path)
    assert error.value.status==502 and error.value.category=='invalid_structured_output'
