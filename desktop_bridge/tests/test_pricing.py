from decimal import Decimal
import json

import pytest

from desktop_bridge.errors import BridgeError
from desktop_bridge.pricing import Catalog,Quote,TTL,catalog_model
from desktop_bridge.service import Runtime
from desktop_bridge.store import Store
from desktop_bridge.providers import claude_usage,codex_usage

MODEL={'id':'my-sol-alias','provider':'codex','native':'gpt-6.1-sol'}
RATES={'prompt':'0.000002','completion':'0.00001','input_cache_read':'0.0000001',
       'input_cache_write':'0.0000025','input_cache_write_1h':'0.000004','request':'0.001',
       'overrides':[{'min_prompt_tokens':272000,'prompt':'0.000004','completion':'0.000015'}]}


def test_actual_native_model_selects_catalog_not_public_alias():
    assert catalog_model(MODEL)=='openai/gpt-6.1-sol'
    assert catalog_model({'provider':'claude','native':'claude-haiku-4-5-20251001','id':'anything'})=='anthropic/claude-haiku-4.5'


def test_native_usage_maps_cache_without_inventing_missing_token_totals():
    assert claude_usage({'input_tokens':10,'output_tokens':5,'cache_read_input_tokens':20,
                         'cache_creation_input_tokens':30})['prompt_tokens']==60
    mapped=codex_usage({'inputTokens':60,'outputTokens':5,'cachedInputTokens':20,'reasoningOutputTokens':3})
    assert mapped['prompt_tokens_details']['cached_tokens']==20
    assert mapped['completion_tokens_details']['reasoning_tokens']==3
    for convert in (claude_usage,codex_usage):
        with pytest.raises(BridgeError) as error:convert({})
        assert error.value.category=='usage_unavailable'
    with pytest.raises(BridgeError):codex_usage({'inputTokens':True,'outputTokens':5})


def test_cache_read_write_and_reasoning_not_counted_twice():
    q=Quote('openai/gpt-6.1-sol',1,RATES)
    u=q.usage({'prompt_tokens':1000,'completion_tokens':200,
              'prompt_tokens_details':{'cached_tokens':100,'cache_write_tokens':50,'cache_write_1h_tokens':20},
              'completion_tokens_details':{'reasoning_tokens':150}})
    expected=Decimal(850)*Decimal('0.000002')+Decimal(100)*Decimal('0.0000001')+Decimal(30)*Decimal('0.0000025')+Decimal(20)*Decimal('0.000004')+Decimal(200)*Decimal('0.00001')+Decimal('0.001')
    assert Decimal(str(u['cost']))==expected and u['total_tokens']==1200
    assert u['completion_tokens_details']['reasoning_tokens']==150
    assert q.headers['X-Bridge-Cost-Source']=='openrouter-list-price-estimate'


def test_long_context_tier_applies_at_boundary():
    q=Quote('openai/gpt-6.1-sol',1,RATES)
    assert q.usage({'prompt_tokens':271999,'completion_tokens':1})['cost']==float(Decimal(271999)*Decimal('0.000002')+Decimal('0.00001')+Decimal('.001'))
    assert q.usage({'prompt_tokens':272000,'completion_tokens':1})['cost']==float(Decimal(272000)*Decimal('0.000004')+Decimal('0.000015')+Decimal('.001'))


def test_cache_survives_restart_refreshes_and_never_reuses_expired_offline_price(tmp_path):
    clock=[1000];calls=[]
    def fetch():calls.append(1);return {'data':[{'id':'openai/gpt-6.1-sol','pricing':RATES,'description':'not persisted'}]}
    first=Catalog(tmp_path,loader=fetch,clock=lambda:clock[0]);first.quote(MODEL);first.quote(MODEL)
    second=Catalog(tmp_path,loader=fetch,clock=lambda:clock[0]);second.quote(MODEL);assert len(calls)==1
    assert 'description' not in (tmp_path/'openrouter-pricing.json').read_text()
    clock[0]+=TTL;second.quote(MODEL);assert len(calls)==2
    clock[0]+=TTL;second.loader=lambda:(_ for _ in ()).throw(OSError('sensitive diagnostic'))
    with pytest.raises(BridgeError) as e:second.quote(MODEL)
    assert e.value.status==503 and 'sensitive' not in str(e.value)


@pytest.mark.parametrize('usage',[{}, {'prompt_tokens':-1,'completion_tokens':1},
    {'prompt_tokens':10,'completion_tokens':1,'prompt_tokens_details':{'cached_tokens':11}},
    {'prompt_tokens':10,'completion_tokens':1,'completion_tokens_details':{'reasoning_tokens':2}}])
def test_missing_or_inconsistent_usage_is_not_free(usage):
    with pytest.raises(BridgeError):Quote('model',1,RATES).usage(usage)


def test_unpriced_model_fails_before_cli_and_keeps_only_metadata(tmp_path):
    store=Store(tmp_path);_,token=store.create_key('pricing gate')
    runner_calls=[];pricing=Catalog(tmp_path,loader=lambda:{'data':[{'id':'unrelated/model','pricing':RATES}]})
    runtime=Runtime(store,lambda *_:runner_calls.append(1),pricing=pricing)
    try:
        task=runtime.submit({'messages':[{'role':'user','content':'PRIVATE_MARKER_PRICING'}]},store.authenticate(token),30)
        assert task.done.wait(3) and task.error.category=='pricing_unavailable' and not runner_calls
        assert store.logs()[0]['error_code']=='pricing_unavailable'
    finally:runtime.stop();store.close()
    for path in tmp_path.iterdir():
        if path.is_file():assert b'PRIVATE_MARKER_PRICING' not in path.read_bytes() and token.encode() not in path.read_bytes()


def test_old_metadata_schema_migrates_without_key_or_device_change(tmp_path):
    store=Store(tmp_path);did=store.get('device_id');_,token=store.create_key('keep')
    store.db.execute('alter table requests drop column cost_usd')
    store.db.execute('alter table requests drop column pricing_model')
    store.db.execute('alter table requests drop column pricing_fetched_ts')
    store.db.commit();store.close()
    store=Store(tmp_path,startup=False)
    assert store.get('device_id')==did and store.authenticate(token)
    assert {'cost_usd','pricing_model','pricing_fetched_ts'}<={r[1] for r in store.db.execute('pragma table_info(requests)')}
    store.close()
