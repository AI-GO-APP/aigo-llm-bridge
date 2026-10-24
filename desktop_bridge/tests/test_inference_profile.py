"""No subscription calls: profile isolation, effective-policy gates and accounting."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import json
import threading
import time

import pytest

from desktop_bridge import providers, inference_profile as p
from desktop_bridge.contract import Inference
from desktop_bridge.codex_session import CodexSession
from desktop_bridge.errors import BridgeError
from desktop_bridge.execution_budget import Budget, scope
from desktop_bridge.store import Store
from desktop_bridge.warm_pool import SingleUsePool


def spec():
    return Inference({'id':'alias','provider':'codex','native':'gpt-6.1-sol'},
        [{'role':'user','parts':[{'type':'text','text':'synthetic'}]}], 'caller system', None, 'text', None)


def verified_config():
    return {'config':{'model_catalog_json':str(p.CATALOG.resolve()),
        **{k:False for k in p.CONTEXT_FLAGS},
        'features':{**{k:False for k in ('shell_tool','apps','plugins','multi_agent',
            'browser_use','computer_use','image_generation','view_image','goals')},
            'code_mode':{'enabled':False}}, 'mcp_servers':{}},
        'origins':{'tools.experimental_request_user_input.enabled':{'name':{'type':'sessionFlags'}}}}


def wait_for(test):
    until=time.monotonic()+3
    while not test():
        assert time.monotonic()<until
        time.sleep(.01)


def test_catalog_is_pinned_and_contains_no_agent_templates():
    assert hashlib.sha256(p.CATALOG.read_bytes()).hexdigest()==p.CATALOG_SHA256
    models=json.loads(p.CATALOG.read_text())['models']
    assert len(models)==1 and models[0]['slug']=='gpt-6.1-sol'
    assert models[0]['model_messages']=={'instructions_template':''}
    assert models[0]['tool_mode']=='direct' and models[0]['shell_type']=='disabled'
    assert models[0]['apply_patch_tool_type'] is None and models[0]['experimental_supported_tools']==[]


@pytest.mark.parametrize('change',[
    {'generated_schema':True}, {'schema':{}}, {'tool_proposals':True}, {'format':'json_object'},
    {'messages':[{'role':'user','parts':[{'type':'image_url'}]}]},
])
def test_decisions_schema_tools_images_never_select_minimal(monkeypatch,change):
    monkeypatch.setattr(p,'availability',lambda *_:pytest.fail('must reject before CLI check'))
    assert p.select(replace(spec(),**change),{}).name==p.STANDARD


def test_unknown_model_and_provider_do_not_probe_cli(monkeypatch):
    monkeypatch.setattr(p,'availability',lambda *_:pytest.fail('not eligible'))
    assert p.select(replace(spec(),model={'provider':'codex','native':'other'}),{}).reason=='model_unverified'
    assert p.select(replace(spec(),model={'provider':'claude'}),{}).reason=='provider_standard'


def test_binary_change_and_catalog_corruption_fall_back_before_inference(tmp_path,monkeypatch):
    monkeypatch.setattr(p.sys,'platform','darwin')
    cli=tmp_path/'native';cli.write_bytes(b'verified synthetic native')
    monkeypatch.setattr(p,'CLI_SHA256',hashlib.sha256(cli.read_bytes()).hexdigest())
    monkeypatch.setattr(p,'CLI_SIZE',cli.stat().st_size)
    settings={'codex_path':str(cli)}
    assert p.select(spec(),settings).name==p.MINIMAL
    cli.write_bytes(b'upgraded native')
    assert p.select(spec(),settings).reason=='cli_unverified'
    monkeypatch.setattr(p,'CLI_SHA256',hashlib.sha256(cli.read_bytes()).hexdigest())
    monkeypatch.setattr(p,'CLI_SIZE',cli.stat().st_size)
    catalog=tmp_path/'catalog.json';catalog.write_bytes(p.CATALOG.read_bytes())
    monkeypatch.setattr(p,'CATALOG',catalog)
    assert p.select(spec(),settings).name==p.MINIMAL
    catalog.write_text('{}')
    assert p.select(spec(),settings).reason=='catalog_unavailable'


def test_platform_gate_and_hash_cancel(tmp_path,monkeypatch):
    monkeypatch.setattr(p.sys,'platform','win32')
    assert p.select(spec(),{}).reason=='platform_unverified'
    cancel=threading.Event();cancel.set()
    with pytest.raises(BridgeError) as e:p.digest(tmp_path/'missing',cancel)
    assert e.value.category=='cancelled'


@pytest.mark.parametrize('mutation', ['catalog','environment','shell','mcp','ask_origin','origin_shape','missing'])
def test_managed_effective_setting_conflicts_fail_closed(mutation):
    r=verified_config()
    if mutation=='catalog':r['config']['model_catalog_json']='/managed/catalog.json'
    if mutation=='environment':r['config']['include_environment_context']=True
    if mutation=='shell':r['config']['features']['shell_tool']=True
    if mutation=='mcp':r['config']['mcp_servers']={'required':{'enabled':True}}
    if mutation=='ask_origin':r['origins']['tools.experimental_request_user_input.enabled']['name']['type']='system'
    if mutation=='origin_shape':r['origins']['tools.experimental_request_user_input.enabled']['name']=True
    if mutation=='missing':r={}
    assert not p.verify_config(r)


def test_opaque_configuration_values_are_never_profile_metadata():
    r=verified_config();assert p.verify_config(r)
    budget=Budget(time.monotonic()+3,threading.Event())
    budget.profile={'inference_profile':p.MINIMAL,'profile_reason':'verified','raw_config':r}
    assert budget.metadata()['inference_profile']==p.MINIMAL
    assert 'raw_config' not in budget.metadata()
    budget.profile={'inference_profile':'arbitrary caller text','profile_reason':'caller secret'}
    assert 'inference_profile' not in budget.metadata() and 'profile_reason' not in budget.metadata()


class FakeSession:
    def __init__(self,profile):
        self.profile=profile;self.generation=None;self.closed=False;self.sent=[]
        self.responses=[{'method':'thread/tokenUsage/updated','params':{'tokenUsage':{'total':{'inputTokens':1,'outputTokens':1}}}},
            {'method':'turn/completed','params':{'turn':{'status':'completed'}}}]
    def verify_profile(self,*_,**__):pass
    def inference_config(self,*_):return {}
    def claim(self,*_):pass
    def send(self,method,params,*_,**__):self.sent.append((method,params));return len(self.sent)
    def response(self,*_):return {'model':'gpt-6.1-sol','thread':{'id':'synthetic','ephemeral':True,'path':None}}
    def receive(self,*_):
        return self.responses.pop(0)
    def close(self):self.closed=True


def test_caller_system_history_and_order_survive_without_bridge_prefix(monkeypatch):
    monkeypatch.setattr(p,'availability',lambda *_:'verified')
    monkeypatch.setattr(providers,'inference_status',lambda *_:{'ready':True})
    s=FakeSession(p.MINIMAL)
    value=replace(spec(),messages=[{'role':'user','parts':[{'type':'text','text':'prior user'}]},
        {'role':'assistant','parts':[{'type':'text','text':'prior answer'}]},*spec().messages])
    providers.call_codex(value,{'timeout_s':3},threading.Event(),'/synthetic',session=s,profile=p.Profile(p.MINIMAL,'verified'))
    start=dict(s.sent)['thread/start'];history=dict(s.sent)['thread/inject_items']['items']
    assert start['baseInstructions']=='caller system' and start['developerInstructions']==''
    assert start['approvalPolicy']=='never' and start['sandbox']=='read-only' and start['dynamicTools']==[]
    assert [(m['role'],m['content'][0]['text']) for m in history]==[('user','prior user'),('assistant','prior answer')]
    assert dict(s.sent)['turn/start']['input']==[{'type':'text','text':'synthetic'}]
    assert s.closed


def test_wrong_session_profile_is_closed_without_a_turn(monkeypatch):
    monkeypatch.setattr(p,'availability',lambda *_:'verified')
    monkeypatch.setattr(providers,'inference_status',lambda *_:{'ready':True})
    s=FakeSession(p.STANDARD)
    with pytest.raises(BridgeError):
        providers.call_codex(spec(),{'timeout_s':3},threading.Event(),'/synthetic',session=s,profile=p.Profile(p.MINIMAL,'verified'))
    assert s.closed and not s.sent


def test_binary_change_after_warm_ready_closes_session_before_a_turn(monkeypatch):
    monkeypatch.setattr(p,'availability',lambda *_:'cli_unverified')
    s=FakeSession(p.MINIMAL)
    with pytest.raises(BridgeError):
        providers.call_codex(spec(),{'timeout_s':3},threading.Event(),'/synthetic',session=s,profile=p.Profile(p.MINIMAL,'verified'))
    assert s.closed and not s.sent


def test_legacy_store_migrates_nullable_profile_columns_without_key_changes(tmp_path):
    store=Store(tmp_path);kid,key=store.create_key('synthetic');before=dict(store.authenticate(key))
    for name in ('inference_profile','profile_reason'):store.db.execute('alter table requests drop column '+name)
    store.db.commit();store.close();store=Store(tmp_path,startup=False)
    try:
        columns={row[1] for row in store.db.execute('pragma table_info(requests)')}
        assert {'inference_profile','profile_reason'}<=columns
        assert dict(store.authenticate(key))==before
    finally:store.close()


class Resource:
    warm_hit=False
    def __init__(self,profile):self.profile=profile;self.closed=False
    def healthy(self):return not self.closed
    def close(self):self.closed=True


def test_profile_pool_shares_total_budget_and_never_leases_wrong_profile():
    created=[]
    def factory(cancel,deadline,profile):
        r=Resource(profile);created.append(r);return r
    pool=SingleUsePool(lambda *_:pytest.fail('wrong factory'),lambda:'a',target=2,limit=4,
        profile_factory=factory,resident_profiles=lambda:(p.MINIMAL,p.STANDARD))
    try:
        wait_for(lambda:pool.snapshot()['idle']==2)
        assert pool.snapshot()['idle_profiles']=={p.MINIMAL:1,p.STANDARD:1}
        def request(i):
            wanted=p.MINIMAL if i%2 else p.STANDARD
            with pool.lease(threading.Event(),time.monotonic()+5,profile=wanted) as r:
                assert r.profile==wanted and not r.closed
                assert pool.snapshot()['total']<=4
                time.sleep(.003)
        with ThreadPoolExecutor(max_workers=8) as executor:list(executor.map(request,range(40)))
        wait_for(lambda:pool.snapshot()['idle']==2)
        assert pool.snapshot()['peak']<=4
        pool.pause();assert not pool.entries;pool.configure(0,1);pool.resume()
        with pool.lease(threading.Event(),time.monotonic()+3,profile=p.MINIMAL) as r:assert r.profile==p.MINIMAL
        assert pool.snapshot()['total']==0
    finally:pool.close()
    assert all(r.closed for r in created)


def test_single_slot_retires_mismatch_and_auth_generation_invalidates_both():
    generation=['a'];created=[];profiles=[p.MINIMAL]
    def factory(cancel,deadline,profile):
        r=Resource(profile);created.append(r);return r
    pool=SingleUsePool(lambda *_:None,lambda:generation[0],target=1,limit=1,
        profile_factory=factory,resident_profiles=lambda:tuple(profiles))
    try:
        wait_for(lambda:pool.snapshot()['idle']==1)
        first=created[0]
        with pool.lease(threading.Event(),time.monotonic()+3,profile=p.STANDARD) as r:
            assert r.profile==p.STANDARD and first.closed and pool.snapshot()['total']==1
        wait_for(lambda:pool.snapshot()['idle']==1);old=list(created);generation[0]='b';profiles[:]=[p.STANDARD]
        wait_for(lambda:pool.snapshot()['idle_profiles'].get(p.STANDARD)==1)
        assert all(r.closed for r in old) and pool.snapshot()['peak']==1
    finally:pool.close()


@pytest.mark.parametrize('close_fails',[False,True])
def test_effective_policy_failure_keeps_root_owned_until_cleanup(close_fails):
    r=Resource(p.MINIMAL)
    def prepare(*_):raise p.unavailable()
    def close():
        if close_fails:raise OSError('synthetic cleanup failure')
        r.closed=True
    r.prepare=prepare;r.close=close
    pool=SingleUsePool(lambda *_:None,lambda:'a',target=0,limit=1,
        profile_factory=lambda *_:r)
    try:
        with pytest.raises((BridgeError,OSError)):
            with pool.lease(threading.Event(),time.monotonic()+3,profile=p.MINIMAL):pytest.fail('must not lease')
        if close_fails:
            assert pool.snapshot()['quarantined']==1 and pool.snapshot()['unavailable']
            r.close=lambda:setattr(r,'closed',True)
        else:assert r.closed and pool.snapshot()['total']==0
    finally:pool.close()
