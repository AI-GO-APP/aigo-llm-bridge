"""Independent HTTPS consumer. Credentials and synthetic I/O arrive over stdin only."""
import json
import math
import os
import ssl
import sys
import urllib.error
import urllib.request


def run(info):
    config=info['integration']['config'];payload=info['integration']['request'];key=info['key']
    base=config['base_url'];opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=os.environ.get('SSL_CERT_FILE'))))
    def request(path,body=None):
        req=urllib.request.Request(base+path,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json',
            'User-Agent':'llm-bridge-independent-consumer/1.0'},data=json.dumps(body).encode() if body is not None else None)
        try:response=opener.open(req,timeout=config['timeout_seconds'])
        except urllib.error.HTTPError as error:response=error
        with response:return response.status,json.loads(response.read())
    code,models=request('/models')
    if code!=200 or not any(m['id']==config['model'] for m in models.get('data',[])):raise ValueError('models')
    code,reply=request('/chat/completions',payload)
    usage=reply.get('usage',{});cost=usage.get('cost')
    if code!=200 or reply.get('choices',[{}])[0].get('message',{}).get('content','').strip()!=info.get('_expected','PONG'):raise ValueError('chat')
    if isinstance(cost,bool) or not isinstance(cost,(int,float)) or not math.isfinite(cost) or cost<=0:raise ValueError('cost')
    unsupported,error=request('/chat/completions',{**payload,'temperature':0.3})
    if unsupported!=400 or error.get('error',{}).get('metadata',{}).get('error_type')!='unsupported_parameter':raise ValueError('unsupported')
    return {'models_get':200,'chat_post':code,'synthetic_reply_matches':True,'usage_cost':cost,
            'prompt_tokens':usage['prompt_tokens'],'completion_tokens':usage['completion_tokens'],
            'unsupported_parameter_status':unsupported,'model':config['model']}


if __name__=='__main__':
    try:print(json.dumps(run(json.load(sys.stdin))))
    except Exception:
        print(json.dumps({'success':False,'error':'Consumer verification failed; payloads/credentials withheld.'}));raise SystemExit(1)
