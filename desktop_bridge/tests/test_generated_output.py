import json
import threading
from types import SimpleNamespace

import pytest

from desktop_bridge import providers
from desktop_bridge.decision_contract import DecisionSpec
from desktop_bridge.decisions import answer
from desktop_bridge.errors import BridgeError
from desktop_bridge.service import Runtime
from desktop_bridge.store import Store


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
    assert command[command.index('--max-turns')+1]=='2'
    assert 'private-state' in captured['payload'] and 'private-instruction' in captured['payload']
    assert '--no-session-persistence' in command and '--tools' in command and '--restricted' in command


def test_generated_schema_requires_native_structured_output(monkeypatch,tmp_path):
    question={'type':'noul','instructions':'synthetic'}
    spec=DecisionSpec({'native':'test'},'synthetic',{'q':question}).inference(question)
    raw=json.dumps({'type':'result','result':'{"noul":0.9}','usage':{'input_tokens':1,'output_tokens':1},'modelUsage':{'test':{}}}).encode()
    monkeypatch.setattr(providers,'status',lambda *_,**kwargs:{'ready':True})
    monkeypatch.setattr(providers,'executable',lambda *_:'synthetic-cli')
    monkeypatch.setattr(providers,'Child',lambda *_:SimpleNamespace(proc=SimpleNamespace(returncode=0),communicate=lambda *_:raw,close=lambda:None))
    text,usage,*_=providers.call_claude(spec,{'timeout_s':2},threading.Event(),tmp_path)
    assert text=='' and usage['prompt_tokens']==usage['completion_tokens']==1
    with pytest.raises(BridgeError) as error:answer(text,question,spec.schema)
    assert error.value.status==502 and error.value.category=='invalid_structured_output'
    store=Store(tmp_path/'profile')
    model=next(m for m in store.get('models') if m['provider']=='claude')
    raw=json.dumps({'type':'result','result':'{"noul":0.9}','usage':{'input_tokens':1,'output_tokens':1},'modelUsage':{model['native']:{}}}).encode()
    store.set('models',[model]);kid,key=store.create_key('synthetic')
    runtime=Runtime(store,runner=lambda spec,settings,cancel:providers.call_claude(spec,settings,cancel,tmp_path))
    try:
        task=runtime.submit({'model':model['id'],'state':'synthetic','questions':{'q':question}},store.authenticate(key),100,protocol='decisions')
        assert task.done.wait(2) and task.error.category=='invalid_structured_output'
        row=store.request(task.id,kid)
        assert row['calls_started']==row['calls_completed']==row['billing_complete']==1
        assert row['cost_usd']>0
    finally:runtime.stop();store.close()
