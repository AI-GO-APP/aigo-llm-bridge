import json
import time
import uuid
import pytest
from desktop_bridge.store import Store
from desktop_bridge.service import Runtime
from desktop_bridge.errors import BridgeError
from desktop_bridge.contract import validate

BODY={'model':'openai/gpt-6-astra','messages':[{'role':'user','content':'synthetic'}]}
TOOLS=[{'type':'function','function':{'name':'sum','parameters':{'type':'object','properties':{'a':{'type':'integer'}},'required':['a'],'additionalProperties':False}}}]

@pytest.mark.parametrize('option',[None,{}, {'data_collection':'deny'},{'data_collection':'allow'}])
def test_provider_metadata_does_not_gate_inference(option,tmp_path):
    store=Store(tmp_path);_,key=store.create_key('cloud');calls=[]
    def runner(*args):calls.append(1);return 'ok',{'prompt_tokens':10,'completion_tokens':1},'stop'
    rt=Runtime(store,runner)
    try:
        request={**BODY,'provider':option}
        rt.preflight(request,store.authenticate(key))
        task=rt.submit(request,store.authenticate(key),20)
        assert task.done.wait(5) and not task.error and len(calls)==1
    finally:rt.stop();store.close()

@pytest.mark.parametrize('override',[
    {'tools':[{'type':'function','function':{'name':'sum','parameters':True}}]},
    {'tool_choice':{'type':'function','function':{'name':[]}}},
    {'messages':[{'role':'tool','tool_call_id':[],'content':'4'}]},
    {'messages':[{'role':'assistant','tool_calls':42}]},
])
def test_malformed_tools_return_contract_error(override,tmp_path):
    store=Store(tmp_path);_,key=store.create_key('contract')
    try:
        with pytest.raises(BridgeError) as error:validate({**BODY,'tools':TOOLS,**override},store,store.authenticate(key))
        assert error.value.status==400
    finally:store.close()

def test_idempotent_call_and_conflict_survive_restart(tmp_path):
    store=Store(tmp_path);_,key=store.create_key('cloud');caller=store.authenticate(key);calls=[]
    def runner(*args):calls.append(1);return 'ok',{'prompt_tokens':10,'completion_tokens':1},'stop'
    rt=Runtime(store,runner);rid=str(uuid.uuid4())
    task=rt.submit(BODY,caller,20,rid);assert task.done.wait(5)
    assert rt.submit(BODY,caller,20,rid) is task and len(calls)==1
    with pytest.raises(BridgeError) as conflict:rt.submit({**BODY,'messages':[{'role':'user','content':'different'}]},caller,20,rid)
    assert conflict.value.status==409
    rt.stop();store.close();store=Store(tmp_path);rt=Runtime(store,runner)
    with pytest.raises(BridgeError) as prior:rt.submit(BODY,store.authenticate(key),20,rid)
    assert prior.value.status==409 and len(calls)==1
    rt.stop();store.close()

def test_preflight_validates_without_inference_or_billing(tmp_path):
    s=Store(tmp_path);_,key=s.create_key('cloud');rt=Runtime(s,lambda *_:pytest.fail('inference'))
    assert rt.preflight(BODY,s.authenticate(key)).model['id']==BODY['model']
    assert s.db.execute('select count(*) from requests').fetchone()[0]==0
    s.set('accepting',False)
    with pytest.raises(BridgeError) as err:rt.preflight(BODY,s.authenticate(key))
    assert err.value.status==503;rt.stop();s.close()


def test_receipt_recovers_ram_result_and_durable_billing_without_reinference(tmp_path):
    s=Store(tmp_path);_,key=s.create_key('cloud');_,other=s.create_key('other');calls=[]
    def runner(*_):calls.append(1);return 'ok',{'prompt_tokens':10,'completion_tokens':1},'stop'
    rt=Runtime(s,runner);caller=s.authenticate(key);rid=str(uuid.uuid4())
    t=rt.submit(BODY,caller,20,rid);assert t.done.wait(5)
    receipt=rt.receipt(rid,caller)
    assert receipt['result']==t.result and receipt['billing']['usage']['cost']==t.result['usage']['cost']
    with pytest.raises(BridgeError):rt.receipt(rid,s.authenticate(other))
    rt.tasks.clear()
    expired=rt.receipt(rid,caller)
    assert 'result' not in expired and expired['billing']==receipt['billing'] and len(calls)==1
    assert all(name not in dict(s.db.execute('select * from requests').fetchone()) for name in ('messages','response','content'))
    rt.stop();s.close()

def test_deadline_expired_before_execution(tmp_path):
    s=Store(tmp_path);_,key=s.create_key('cloud');rt=Runtime(s,lambda *_:pytest.fail('inference'))
    t=rt.submit(BODY,s.authenticate(key),20,deadline=time.time()-1);assert t.done.wait(3)
    assert t.error.status==408;rt.stop();s.close()

def test_tool_proposals_and_history_are_validated_and_never_executed(tmp_path):
    s=Store(tmp_path);_,key=s.create_key('cloud');seen=[]
    def runner(spec,*_):seen.append(spec);return json.dumps({'content':None,'calls':[{'name':'sum','arguments':{'a':4}}]}),{'prompt_tokens':10,'completion_tokens':1},'stop'
    rt=Runtime(s,runner)
    t=rt.submit({**BODY,'tools':TOOLS,'tool_choice':'required','parallel_tool_calls':False},s.authenticate(key),30)
    assert t.done.wait(5) and not t.error
    msg=t.result['choices'][0]['message'];assert t.result['choices'][0]['finish_reason']=='tool_calls'
    call=msg['tool_calls'][0];assert json.loads(call['function']['arguments'])=={'a':4}
    follow={**BODY,'tools':TOOLS,'messages':BODY['messages']+[msg,{'role':'tool','tool_call_id':call['id'],'content':'4'}]}
    assert validate(follow,s,s.authenticate(key)).tool_proposals
    # Enforced output schema prevents an unregistered function from escaping.
    rt.runner=lambda *_:(json.dumps({'content':None,'calls':[{'name':'shell','arguments':{}}]}),{'prompt_tokens':1,'completion_tokens':1},'stop')
    bad=rt.submit({**BODY,'tools':TOOLS},s.authenticate(key),20);assert bad.done.wait(5) and bad.error.status==502
    rt.stop();s.close()
