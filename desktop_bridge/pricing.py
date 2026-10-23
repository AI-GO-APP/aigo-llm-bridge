"""OpenRouter list-price equivalents; no inference or credentials go to OpenRouter."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
import ssl
import threading
import time
import urllib.request

import certifi

from .errors import BridgeError

CATALOG_URL='https://openrouter.ai/api/v1/models'
TTL=900
RATE_KEYS={'prompt','completion','request','input_cache_read','input_cache_write','input_cache_write_1h'}


def amount(value):
    try:result=Decimal(str(value))
    except (InvalidOperation,ValueError,TypeError):raise ValueError('Invalid catalog price') from None
    if not result.is_finite() or result<0:raise ValueError('Invalid catalog price')
    return result


def catalog_model(model):
    native=model['native']
    if model['provider']=='codex':return 'openai/'+native
    match=re.fullmatch(r'claude-(haiku|sonnet|opus)-(\d+)-(\d+)(?:-\d{8})?',native)
    if match:return 'anthropic/claude-'+match[1]+'-'+match[2]+'.'+match[3]
    if model['provider']=='claude' and native==model['id'].removeprefix('anthropic/'):return model['id']
    raise BridgeError(503,'pricing_unavailable','無法對應實際 CLI 模型的 OpenRouter 牌價；未執行推論。','model')


def fetch_catalog():
    opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
    request=urllib.request.Request(CATALOG_URL,headers={'User-Agent':'local-token-buffet-bridge-pricing/1.0','Accept':'application/json'})
    with opener.open(request,timeout=12) as response:
        raw=response.read(20_000_001)
    if len(raw)>20_000_000:raise ValueError('Catalog too large')
    return json.loads(raw)


def clean_rates(data):
    if not isinstance(data,dict) or not {'prompt','completion'}<=set(data):raise ValueError('Missing rates')
    rates={key:str(amount(value)) for key,value in data.items() if key in RATE_KEYS}
    overrides=[]
    for row in data.get('overrides',[]):
        minimum=row.get('min_prompt_tokens')
        if isinstance(minimum,bool) or not isinstance(minimum,int) or minimum<0:raise ValueError('Invalid tier')
        overrides.append({'min_prompt_tokens':minimum,**{k:str(amount(v)) for k,v in row.items() if k in RATE_KEYS}})
    if overrides:rates['overrides']=sorted(overrides,key=lambda r:r['min_prompt_tokens'])
    return rates


@dataclass(frozen=True)
class Quote:
    model: str
    fetched_at: float
    pricing: dict

    @property
    def headers(self):
        return {'X-Bridge-Cost-Source':'openrouter-list-price-estimate',
                'X-Bridge-Pricing-Model':self.model,
                'X-Bridge-Pricing-Fetched-At':str(int(self.fetched_at))}

    def usage(self,usage):
        if not isinstance(usage,dict) or not {'prompt_tokens','completion_tokens'}<=set(usage):
            raise BridgeError(502,'usage_unavailable','CLI 未回報完整 token 用量，無法換算牌價。')
        def count(value):
            if isinstance(value,bool) or not isinstance(value,int) or value<0:raise ValueError('Invalid usage')
            return value
        try:
            prompt=count(usage['prompt_tokens']);completion=count(usage['completion_tokens'])
            detail=usage.get('prompt_tokens_details') or {}
            cached=count(detail.get('cached_tokens',0));written=count(detail.get('cache_write_tokens',0))
            long_write=count(detail.get('cache_write_1h_tokens',0))
            if cached+written>prompt or long_write>written:raise ValueError('Inconsistent token counts')
            rates=dict(self.pricing)
            for tier in rates.pop('overrides',[]):
                if prompt>=tier['min_prompt_tokens']:rates.update({k:v for k,v in tier.items() if k in RATE_KEYS})
            base=amount(rates['prompt']);out=amount(rates['completion'])
            cost=(prompt-cached-written)*base+cached*amount(rates.get('input_cache_read',base))
            cost+=(written-long_write)*amount(rates.get('input_cache_write',base))
            cost+=long_write*amount(rates.get('input_cache_write_1h',rates.get('input_cache_write',base)))
            cost+=completion*out+amount(rates.get('request',0))
            result={'prompt_tokens':prompt,'completion_tokens':completion,'total_tokens':prompt+completion,
                    'cost':float(cost.quantize(Decimal('0.000000000001')))}
            if detail:
                # OpenRouter's public detail names; the 1h split is only an internal billing input.
                result['prompt_tokens_details']={'cached_tokens':cached,'cache_write_tokens':written}
            if 'completion_tokens_details' in usage:
                reasoning=count(usage['completion_tokens_details'].get('reasoning_tokens',0))
                if reasoning>completion:raise ValueError('Inconsistent reasoning count')
                result['completion_tokens_details']={'reasoning_tokens':reasoning}
            return result
        except (ValueError,TypeError,InvalidOperation,AttributeError):
            raise BridgeError(502,'usage_unavailable','CLI token 明細無法核對，未捏造金額。') from None


def combine_usage(previous, current):
    """Aggregate already priced calls; request fees and tiered rates apply per call."""
    if previous is None: return dict(current)
    result = {key: previous[key]+current[key] for key in ('prompt_tokens','completion_tokens','total_tokens')}
    result['cost'] = float(Decimal(str(previous['cost']))+Decimal(str(current['cost'])))
    for field in ('prompt_tokens_details','completion_tokens_details'):
        a, b = previous.get(field,{}), current.get(field,{})
        if a or b: result[field] = {k:a.get(k,0)+b.get(k,0) for k in set(a)|set(b)}
    return result


class Catalog:
    def __init__(self,directory,*,loader=None,clock=time.time):
        self.path=Path(directory)/'openrouter-pricing.json';self.loader=loader or fetch_catalog
        self.clock=clock;self.lock=threading.RLock();self.models={};self.fetched_at=0
        try:
            saved=json.loads(self.path.read_text(encoding='utf-8'))
            if saved.get('source')==CATALOG_URL:
                self.fetched_at=float(saved['fetched_at'])
                self.models={key:clean_rates(value) for key,value in saved['models'].items()}
        except (OSError,ValueError,TypeError,KeyError,AttributeError):self.models={};self.fetched_at=0

    def quote(self,model):
        name=catalog_model(model)
        with self.lock:
            now=self.clock()
            if not self.models or not 0<=now-self.fetched_at<TTL:
                try:
                    data=self.loader();models={}
                    for item in data['data']:
                        try:models[item['id']]=clean_rates(item['pricing'])
                        except (ValueError,KeyError,TypeError):continue
                    if not models:raise ValueError('Empty price catalog')
                    self.models=models;self.fetched_at=now
                    # Only public price metadata is persisted; never a request, response or key.
                    saved={'source':CATALOG_URL,'fetched_at':now,'models':models}
                    self.path.parent.mkdir(parents=True,exist_ok=True)
                    pending=self.path.with_suffix('.pending')
                    pending.write_text(json.dumps(saved,separators=(',',':')),encoding='utf-8');os.replace(pending,self.path)
                except Exception:
                    raise BridgeError(503,'pricing_unavailable','OpenRouter 牌價暫時不可用；未執行推論，請稍後再試。') from None
            if name not in self.models:
                raise BridgeError(503,'pricing_unavailable','OpenRouter 沒有此實際模型的可用牌價；未執行推論。','model')
            return Quote(name,self.fetched_at,dict(self.models[name]))
