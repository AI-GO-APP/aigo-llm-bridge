import copy
import json
import math
import time
import uuid

import pytest

from desktop_bridge.decision_contract import validate
from desktop_bridge.decisions import answer
from desktop_bridge.errors import BridgeError
from desktop_bridge.pricing import Catalog
from desktop_bridge.service import Runtime, ApiServer
from desktop_bridge.store import Store
from desktop_bridge.tests.test_desktop import request

MODEL='openai/gpt-6.1-sol' # Discovered rather than configured in the default registry.
BODY={'model':MODEL,'state':{'me':'Synthetic owner','new_messages':[{'sender':'client','text':'Please quote tomorrow.'}]},
      'questions':{
          'needs_response':{'type':'noul','instructions':'Does the sender need a response?','criteria':{'true':'A request','false':'Only a notice'}},
          'disposition':{'type':'choice','instructions':'How should this be handled?','criteria':{'reply':'Reply','act':'Do work','notify':'Notice','none':'No action'}},
          'tension':{'type':'score','instructions':'How tense?','criteria':['Relaxed','Normal','Pressure','Conflict','Severe conflict']}},
      'provider':{'data_collection':'deny'}}
RAW=[{'noul':.96},{'probabilities':[.1,.8,.1,0]},{'probabilities':[0,.2,.8,0,0]}]


def setup(tmp_path, runner, *, pricing=None):
    s=Store(tmp_path);_,key=s.create_key('synthetic',['codex'])
    rt=Runtime(s,runner,pricing=pricing);return s,key,rt


def test_original_body_per_question_isolation_dynamic_model_and_billing(tmp_path):
    seen=[];original=copy.deepcopy(BODY)
    def runner(spec,settings,cancel):
        seen.append(spec)
        return json.dumps(RAW[len(seen)-1]),{'prompt_tokens':10,'completion_tokens':2},'stop'
    s,key,rt=setup(tmp_path,runner)
    rid=str(uuid.uuid4())
    try:
        task=rt.submit(BODY,s.authenticate(key),100,rid,protocol='decisions')
        assert task.done.wait(5) and task.error is None
        result=task.result
        assert BODY==original and len(seen)==3
        assert set(result)=={'id','model','provider','answers','usage'}
        assert result['model']==MODEL and result['provider']=='codex'
        assert result['answers']['needs_response']=={'type':'noul','noul':.96}
        assert result['answers']['disposition']['choice']=='act'
        assert result['answers']['disposition']['confidence']==pytest.approx(.733333333333)
        score=result['answers']['tension']
        assert score['score']==1.8 and score['confidence']==pytest.approx(5/6)
        assert score['legend']=={str(i):v for i,v in enumerate(BODY['questions']['tension']['criteria'])}
        assert result['usage']=={'input_tokens':30,'output_tokens':6,'cost':.000042}
        for spec,q in zip(seen,BODY['questions'].values()):
            payload=json.loads(spec.messages[0]['parts'][0]['text'])
            assert payload['state']==BODY['state'] and payload['instructions']==q['instructions']
            assert 'questions' not in payload and 'needs_response' not in json.dumps(payload)
        receipt=rt.receipt(rid,s.authenticate(key))
        assert receipt['billing']['model']==MODEL
        assert receipt['billing_status']=={'complete':True,'calls_started':3,'calls_completed':3}
        rows=rt.models.capabilities(s.authenticate(key))['data']
        assert next(r for r in rows if r['id']==MODEL)['decisions']['verified']
        persisted='\n'.join(s.db.iterdump())
        for forbidden in (key,'Please quote tomorrow.','Does the sender need a response?','needs_response'):
            assert forbidden not in persisted
        rt.tasks.clear()
        assert rt.receipt(rid,s.authenticate(key))['billing']==receipt['billing']
    finally:rt.stop();s.close()


@pytest.mark.parametrize('failure,complete,known_calls',[
    ('invalid_json',True,2),('bad_distribution',True,2),('missing_usage',False,1),
    ('transport',False,1),('substituted_model',False,1),('length',True,2)])
def test_partial_failure_preserves_known_cost_and_never_partial_success(tmp_path,failure,complete,known_calls):
    calls=[]
    def runner(*_):
        calls.append(1)
        if len(calls)==1:return json.dumps(RAW[0]),{'prompt_tokens':10,'completion_tokens':2},'stop'
        if failure=='transport':raise BridgeError(503,'provider_unavailable','Unavailable')
        if failure=='missing_usage':return '{}',{},'stop'
        if failure=='substituted_model':return '{}',{'prompt_tokens':10,'completion_tokens':2},'stop','another-model'
        text='invalid' if failure=='invalid_json' else json.dumps({'probabilities':[1,1,1,1]} if failure=='bad_distribution' else RAW[1])
        return text,{'prompt_tokens':10,'completion_tokens':2},'length' if failure=='length' else 'stop'
    s,key,rt=setup(tmp_path,runner);rid=str(uuid.uuid4())
    try:
        task=rt.submit(BODY,s.authenticate(key),100,rid,protocol='decisions')
        assert task.done.wait(5) and task.error and task.result is None and len(calls)==2
        receipt=rt.receipt(rid,s.authenticate(key))
        assert 'result' not in receipt
        assert receipt['billing']['usage']['cost']==pytest.approx(.000014*known_calls)
        assert receipt['billing_status']=={'complete':complete,'calls_started':2,'calls_completed':known_calls}
    finally:rt.stop();s.close()


def test_request_fee_and_tiers_apply_per_actual_call(tmp_path):
    pricing=Catalog(tmp_path,loader=lambda:{'data':[{'id':MODEL,'pricing':{
        'prompt':'.001','completion':'.002','request':'.01',
        'overrides':[{'min_prompt_tokens':20,'prompt':'.9'}]}}]})
    calls=[]
    def runner(*_):
        value=RAW[len(calls)];calls.append(1)
        return json.dumps(value),{'prompt_tokens':10,'completion_tokens':2},'stop'
    s,key,rt=setup(tmp_path,runner,pricing=pricing)
    try:
        task=rt.submit(BODY,s.authenticate(key),100,protocol='decisions')
        assert task.done.wait(5) and not task.error
        assert task.result['usage']['cost']==pytest.approx(3*(.01+.004+.01))
    finally:rt.stop();s.close()


def test_invalid_output_keeps_cache_and_reasoning_billing_metadata(tmp_path):
    def runner(*_):
        return 'invalid-json',{'prompt_tokens':10,'completion_tokens':2,
            'prompt_tokens_details':{'cached_tokens':3,'cache_write_tokens':2},
            'completion_tokens_details':{'reasoning_tokens':1}},'stop'
    s,key,rt=setup(tmp_path,runner);rid=str(uuid.uuid4());caller=s.authenticate(key)
    try:
        task=rt.submit(BODY,caller,100,rid,protocol='decisions')
        assert task.done.wait(8) and task.error and task.result is None
        receipt=rt.receipt(rid,caller)
        assert receipt['billing_status']=={'complete':True,'calls_started':1,'calls_completed':1}
        row=s.request(task.id,caller['id'])
        assert (row['cached_tokens'],row['cache_write_tokens'],row['reasoning_tokens'])==(3,2,1)
        assert receipt['billing']['usage']['cost']==pytest.approx(.000014)
    finally:rt.stop();s.close()


def test_deadline_cancellation_and_revocation_between_questions(tmp_path):
    holder={};calls=[]
    def runner(*_):
        calls.append(1)
        holder['task'].cancel.set()
        return json.dumps(RAW[0]),{'prompt_tokens':10,'completion_tokens':2},'stop'
    import threading
    gate=threading.Event()
    def blocked(*args):assert gate.wait(3);return runner(*args)
    s,key,rt=setup(tmp_path,blocked);rid=str(uuid.uuid4())
    try:
        task=rt.submit(BODY,s.authenticate(key),100,rid,protocol='decisions');holder['task']=task;gate.set()
        assert task.done.wait(5) and task.error.status==499 and len(calls)==1
        assert rt.receipt(rid,s.authenticate(key))['billing']['usage']['cost']==.000014
    finally:rt.stop();s.close()


def test_protocol_is_part_of_idempotency_and_decision_option_order_is_preserved(tmp_path):
    s,key,rt=setup(tmp_path,lambda *_:(json.dumps(RAW[0]),{'prompt_tokens':1,'completion_tokens':1},'stop'))
    one={**BODY,'questions':{'q':BODY['questions']['needs_response']}};caller=s.authenticate(key);rid=str(uuid.uuid4())
    try:
        task=rt.submit(one,caller,10,rid,protocol='decisions');assert task.done.wait(5)
        assert rt.submit(copy.deepcopy(one),caller,10,rid,protocol='decisions') is task
        changed=copy.deepcopy(one);changed['questions']['q']['criteria']={'false':'Only a notice','true':'A request'}
        with pytest.raises(BridgeError) as err:rt.submit(changed,caller,10,rid,protocol='decisions')
        assert err.value.status==409
    finally:rt.stop();s.close()


def test_http_decisions_probe_jobs_scope_and_preflight(tmp_path):
    def runner(spec,*_):
        value={'noul':.9} if 'noul' in spec.schema.get('properties',{}) else {'probabilities':[.25]*4}
        return json.dumps(value),{'prompt_tokens':5,'completion_tokens':1},'stop'
    s,key,rt=setup(tmp_path,runner);api=ApiServer(rt,0);api.start()
    one={**BODY,'questions':{'needs_response':BODY['questions']['needs_response']}}
    try:
        assert request(api,key,one,'/bridge/v1/preflight')[0]==200 and not s.logs()
        code,result=request(api,key,one,'/api/alpha/decisions')
        assert code==200 and result['answers']['needs_response']['noul']==.9
        assert request(api,key,{'model':MODEL,'protocol':'decisions'},'/bridge/v1/models/probe')[0]==200
        assert request(api,key,{'model':MODEL,'state':'forbidden custom probe'},'/bridge/v1/models/probe')[0]==400
        code,job=request(api,key,one,'/bridge/v1/jobs');assert code==202
        assert rt.tasks[job['id']].done.wait(5)
        assert request(api,key,path='/bridge/v1/jobs/'+job['id'])[1]['result']['answers']
        _,other=s.create_key('claude',['claude'])
        assert request(api,other,{**one,'model':'openai/gpt-6-astra'},'/api/alpha/decisions')[0]==403
        assert request(api,key,{**one,'messages':[]},'/api/alpha/decisions')[0]==400
        assert request(api,key,one,'/api/v1/chat/completions')[0]==400
    finally:rt.stop();api.stop();s.close()


@pytest.mark.parametrize('value',[
    None,{}, {'model':None}, {'state':False}, {'questions':{}}, {'questions':[]}, {'model':'auto'},
    {'provider':{'order':['other']}}, {'trace':[]}, {'temperature':0}, {'stream':False},
    {'questions':{'q':{'type':[],'instructions':'x'}}},
    {'questions':{'q':{'type':'score','instructions':'x','criteria':['only one']}}},
    {'questions':{'q':{'type':'choice','instructions':'x','criteria':{}}}},
    {'questions':{'q':{'type':'noul','instructions':False}}},
    {'questions':{'q':{'type':'noul','instructions':'x','criteria':{'maybe':'x'}}}},
    {'state':{'nested':float('nan')}},
])
def test_invalid_contract_never_calls_provider(tmp_path,value):
    s,key,rt=setup(tmp_path,lambda *_:pytest.fail('invalid request inferred'))
    try:
        body=value if value is None else {**BODY,**value}
        # {} by itself is used to check missing required fields.
        if value=={}:body={}
        with pytest.raises(BridgeError) as err:rt.submit(body,s.authenticate(key),100,protocol='decisions')
        assert err.value.status==400
        # Admission now reserves before validation and retains metadata-only rejections.
        rows=s.logs()
        assert len(rows)==1 and rows[0]['status']=='rejected'
        assert rows[0]['calls_started']==0 and rows[0]['validation_ms'] is not None
    finally:rt.stop();s.close()


@pytest.mark.parametrize('kind,criteria,raw',[
    ('noul',None,'{"noul":true}'),('noul',None,'{"noul":NaN}'),('noul',None,'{"noul":1e999}'),
    ('noul',None,'{"noul":0.1,"noul":0.9}'),('noul',None,'{"noul":0.5,"extra":1}'),
    ('choice',{'a':'a','b':'b'},'{"probabilities":[0.1,0.1]}'),
    ('choice',{'a':'a','b':'b'},'{"probabilities":[true,0]}'),
    ('choice',{'a':'a','b':'b'},'{"probabilities":[-0.1,1.1]}'),
    ('score',['a','b'],'{"probabilities":[0,0,1]}')])
def test_invalid_probability_outputs_are_rejected(tmp_path,kind,criteria,raw):
    s=Store(tmp_path);_,key=s.create_key('test')
    try:
        spec=validate({'model':'openai/gpt-6-astra','state':{},'questions':{'q':{
            'type':kind,'instructions':'x',**({'criteria':criteria} if criteria is not None else {})}}},s,s.authenticate(key))
        q=spec.questions['q']
        with pytest.raises(BridgeError) as err:answer(raw,q,spec.inference(q).schema)
        assert err.value.category=='invalid_structured_output'
    finally:s.close()


def test_score_distance_confidence_choice_tie_and_structured_entries(tmp_path):
    s=Store(tmp_path);_,key=s.create_key('test')
    questions={'score':{'type':'score','instructions':{'question':['Rate',None]},'criteria':[None,{'level':'mid'},['high']]},
               'choice':{'type':'choice','instructions':None,'criteria':{'__proto__':{},'other':None}},
               'single':{'type':'choice','instructions':'x','criteria':{'only':'x'}}}
    try:
        spec=validate({'model':'openai/gpt-6-astra','state':['JSON',{}],'questions':questions},s,s.authenticate(key))
        score=questions['score'];schema=spec.inference(score).schema
        assert answer('{"probabilities":[0,0.5,0.5]}',score,schema)['confidence']==.25
        assert answer('{"probabilities":[0.5,0,0.5]}',score,schema)['confidence']==0
        q=questions['choice'];r=answer('{"probabilities":[0.5,0.5]}',q,spec.inference(q).schema)
        prompt=json.loads(spec.inference(q).messages[0]['parts'][0]['text'])
        assert prompt['criteria']==[{'name':'__proto__','description':{}},{'name':'other','description':None}]
        assert r['choice']=='__proto__' and r['confidence']==0
        q=questions['single'];assert answer('{"probabilities":[1]}',q,spec.inference(q).schema)['confidence']==1
    finally:s.close()


@pytest.mark.parametrize('interruption,expected_status',[('cancel',499),('revoke',401),('deadline',408),('account',503)])
def test_no_next_question_after_interrupt_and_known_usage_survives(tmp_path,monkeypatch,interruption,expected_status):
    clock=[100.];epoch=['first'];calls=[];holder={}
    monkeypatch.setattr('desktop_bridge.service.time.time',lambda:clock[0])
    def runner(spec,settings,cancel):
        calls.append(1)
        if interruption=='cancel':cancel.set()
        elif interruption=='revoke':s.revoke(caller['id'])
        elif interruption=='deadline':
            # Admission converts the wall-clock deadline once; subsequent expiry
            # is monotonic and must not depend on clock adjustments.
            from desktop_bridge.execution_budget import current
            current().until=0
        else:epoch[0]='second'
        return json.dumps(RAW[0]),{'prompt_tokens':10,'completion_tokens':2},'stop'
    s,key,rt=setup(tmp_path,runner);caller=s.authenticate(key)
    rt.models.generation=lambda *_:epoch[0]
    try:
        task=rt.submit(BODY,caller,20,protocol='decisions')
        assert task.done.wait(5) and task.error.status==expected_status and len(calls)==1
        row=s.request(task.id,caller['id'])
        assert row['cost_usd']==.000014 and row['calls_started']==row['calls_completed']==1
    finally:rt.stop();s.close()


def test_receipt_never_presents_intermediate_known_usage_as_final(tmp_path,monkeypatch):
    import threading
    from desktop_bridge import service
    entered=threading.Event();release=threading.Event();real_answer=service.decision_answer
    def pause_after_usage(*args):
        entered.set();assert release.wait(5)
        return real_answer(*args)
    monkeypatch.setattr(service,'decision_answer',pause_after_usage)
    s,key,rt=setup(tmp_path,lambda *_:(json.dumps(RAW[0]),{'prompt_tokens':10,'completion_tokens':2},'stop'))
    caller=s.authenticate(key);rid=str(uuid.uuid4())
    body={**BODY,'questions':{'q':BODY['questions']['needs_response']}}
    try:
        task=rt.submit(body,caller,20,rid,protocol='decisions');assert entered.wait(3)
        partial=rt.receipt(rid,caller)
        assert partial['status']=='running' and not partial['billing_status']['complete'] and 'result' not in partial
        assert partial['billing']['usage']['cost']==.000014
        release.set();assert task.done.wait(3)
        assert rt.receipt(rid,caller)['billing_status']['complete']
    finally:release.set();rt.stop();s.close()
