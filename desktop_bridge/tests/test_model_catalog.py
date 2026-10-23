import pytest

from desktop_bridge.model_catalog import ModelCatalog
from desktop_bridge.store import Store
from desktop_bridge.service import Runtime, ApiServer
from desktop_bridge.errors import BridgeError
from desktop_bridge.tests.test_desktop import request


def test_scope_discovery_refresh_expiry_and_account_switch(tmp_path):
    s=Store(tmp_path); _,key=s.create_key('scoped',['codex'])
    clock=[100.]; epoch=['a']; calls=[]
    def discover(p,store):
        calls.append(p)
        return {'ready':True,'models':['gpt-6-astra','gpt-6-luna'],'source':'cli_catalog'}
    cat=ModelCatalog(s,discover=discover,generation=lambda *_:epoch[0],clock=lambda:clock[0])
    caller=s.authenticate(key)
    rows=cat.capabilities(caller)['data']
    assert {m['id'] for m in rows}=={'openai/gpt-6-astra','openai/gpt-6-luna'}
    assert all(m['availability']['state']=='unverified' for m in rows)
    assert calls==['codex']
    cat.capabilities(caller); assert calls==['codex']
    model={'id':'openai/gpt-6-luna','native':'gpt-6-luna','provider':'codex'}
    cat.observe(model,'decisions','a')
    luna=cat.capabilities(caller)['data'][1]
    assert luna['availability']['state']=='verified' and luna['decisions']['verified']
    cat.capabilities(caller,refresh=True); assert len(calls)==1
    clock[0]+=5
    cat.capabilities(caller,refresh=True); assert len(calls)==2
    epoch[0]='b'
    assert all(m['availability']['state']=='unverified' for m in cat.capabilities(caller)['data'])
    cat.observe(model,'chat','a') # Late result from the old login is discarded.
    assert all(m['availability']['state']=='unverified' for m in cat.capabilities(caller)['data'])
    clock[0]+=31;cat.capabilities(caller);assert len(calls)==4
    s.close()


def test_authentication_denial_and_transient_errors_have_different_evidence(tmp_path):
    s=Store(tmp_path);_,key=s.create_key('scoped',['codex']);caller=s.authenticate(key)
    cat=ModelCatalog(s,discover=lambda *_:{'ready':True,'models':[],'source':'cli_catalog'})
    model=s.get('models')[1]; epoch=cat.generation('codex',s)
    assert cat.models(caller)['data'] # Catalog absence alone is not a denial.
    cat.observe(model,'chat',epoch,BridgeError(429,'rate_limit_exceeded','Limited'))
    assert cat.capabilities(caller)['data'][0]['availability']['state']=='unverified'
    cat.observe(model,'chat',epoch,BridgeError(400,'model_not_found','Unavailable'))
    assert not cat.models(caller)['data']
    s.close()


def test_discovery_failure_is_unverified_without_leaking_exception(tmp_path):
    s=Store(tmp_path);_,key=s.create_key('scoped',['codex'])
    def broken(*_):raise RuntimeError('PRIVATE CLI DIAGNOSTIC')
    cat=ModelCatalog(s,discover=broken)
    result=cat.capabilities(s.authenticate(key))
    assert result['data'][0]['availability']['state']=='unverified'
    assert 'PRIVATE' not in str(result)
    s.close()


def test_models_and_capabilities_http_never_infer_and_revoke(tmp_path):
    s=Store(tmp_path);kid,key=s.create_key('scoped',['codex'])
    rt=Runtime(s,lambda *_:pytest.fail('discovery must not infer'));api=ApiServer(rt,0);api.start()
    try:
        status,body=request(api,key,path='/api/v1/models')
        assert status==200 and all(m['owned_by']=='codex' for m in body['data'])
        status,body=request(api,key,path='/bridge/v1/model-capabilities')
        assert status==200 and body['inference_performed'] is False
        assert request(api,key,{},'/bridge/v1/models/refresh')[0]==200
        assert request(api,key,{'model':'bad'},'/bridge/v1/models/refresh')[0]==400
        s.revoke(kid)
        assert request(api,key,path='/bridge/v1/model-capabilities')[0]==401
    finally:rt.stop();api.stop();s.close()


def test_account_change_during_discovery_cannot_reuse_old_verified_evidence(tmp_path):
    s=Store(tmp_path);_,key=s.create_key('scope',['codex']);epoch=['old']
    def discover(*_):
        epoch[0]='new'
        return {'ready':True,'models':['private-old-model'],'source':'cli_catalog'}
    cat=ModelCatalog(s,discover=discover,generation=lambda *_:epoch[0])
    cat.observe(s.get('models')[1],'decisions','old')
    rows=cat.capabilities(s.authenticate(key))['data']
    assert all(r['availability']['state']=='unverified' for r in rows)
    assert not any(r['native']=='private-old-model' for r in rows)
    s.close()
