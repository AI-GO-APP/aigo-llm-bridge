"""Synthetic loopback queue/schema benchmark. Never starts a subscription CLI.

Run separately against baseline/candidate source. Output is aggregate metadata only.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import hashlib
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid


def percentile(values,p):
    return round(sorted(values)[max(0,math.ceil(len(values)*p)-1)],4) if values else None


class Resources:
    def __init__(self):
        self.stop=threading.Event();self.rss=0;self.cpu=0;self.children=0;self.fds=0
        self.thread=threading.Thread(target=self.sample,daemon=True)

    def sample(self):
        while not self.stop.is_set():
            # comm is executable name, never argv, headers, prompts or credentials.
            rows=subprocess.check_output(['ps','-axo','pid=,ppid=,rss=,%cpu='],text=True)
            processes=[line.split() for line in rows.splitlines()]
            family={os.getpid()}
            for _ in range(8):
                family.update(int(p[0]) for p in processes if len(p)==4 and int(p[1]) in family)
            owned=[p for p in processes if len(p)==4 and int(p[0]) in family]
            self.rss=max(self.rss,sum(int(p[2]) for p in owned))
            self.cpu=max(self.cpu,sum(float(p[3]) for p in owned))
            self.children=max(self.children,len(owned)-1)
            self.fds=max(self.fds,len(os.listdir('/dev/fd')))
            self.stop.wait(.1)

    def start(self):self.thread.start()

    def finish(self):
        self.stop.set();self.thread.join()
        return {'peak_tree_rss_kib':self.rss,'peak_tree_cpu_percent_one_core':round(self.cpu,1),
                'peak_descendants_including_sampler':self.children,'peak_bridge_fds':self.fds}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--workers',default='32,48,64')
    parser.add_argument('--kinds',default='chat,decisions,mixed')
    parser.add_argument('--questions',default='1,3')
    parser.add_argument('--rounds',type=int,default=3)
    parser.add_argument('--waves',type=int,default=1)
    parser.add_argument('--delay',type=float,default=.5)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    workers=[int(v) for v in args.workers.split(',')];questions=[int(v) for v in args.questions.split(',')]
    kinds=args.kinds.split(',')
    if (any(not 1<=v<=64 for v in workers) or any(not 1<=v<=3 for v in questions)
        or set(kinds)-{'chat','decisions','mixed'} or not 1<=args.rounds<=10 or not 1<=args.waves<=3 or not .01<=args.delay<=5):
        parser.error('Bounded benchmark: workers 1–64, questions 1–3, rounds 1–10, waves 1–3, delay .01–5.')
    sys.path.insert(0,str(args.source.resolve()))
    from desktop_bridge.service import Runtime,ApiServer
    from desktop_bridge.store import Store
    from desktop_bridge.pricing import Quote
    from types import SimpleNamespace

    def runner(spec,settings,cancel):
        if cancel.wait(min(args.delay,settings.get('timeout_s'))):
            from desktop_bridge.errors import BridgeError
            raise BridgeError(499,'cancelled','Synthetic cancellation.')
        return ('{"noul":0.9}' if spec.schema else 'OK'),{'prompt_tokens':10,'completion_tokens':2},'stop'

    quote=Quote('openai/gpt-6-astra',time.time(),{'prompt':'0.000001','completion':'0.000002'})
    pricing=SimpleNamespace(quote=lambda *_:quote)
    models=SimpleNamespace(generation=lambda *_:'synthetic',observe=lambda *_:None)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    results=[]
    for count in workers:
        for kind in kinds:
            for question_count in (questions if kind!='chat' else [1]):
                for round_no in range(1,args.rounds+1):
                    with tempfile.TemporaryDirectory(prefix='bridge-synthetic-benchmark-') as directory:
                        store=Store(directory);_,key=store.create_key('synthetic-benchmark')
                        rt=Runtime(store,runner,pricing,models,max_workers=count,max_pending=64)
                        api=ApiServer(rt,0);api.start();samples=Resources();samples.start()
                        start=time.monotonic();values=[]
                        def call(index):
                            decisions=kind=='decisions' or kind=='mixed' and index%2==1
                            body=({'model':'openai/gpt-6-astra','state':'synthetic',
                                   'questions':{str(q):{'type':'noul','instructions':'Synthetic?'} for q in range(question_count)}}
                                  if decisions else {'model':'openai/gpt-6-astra','messages':[{'role':'user','content':'Reply OK.'}]})
                            request_id=str(uuid.uuid4())
                            req=urllib.request.Request(f'http://127.0.0.1:{api.port}'+('/api/alpha/decisions' if decisions else '/api/v1/chat/completions'),
                                data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','X-AIEA-Request-Id':request_id})
                            began=time.monotonic()
                            try:response=opener.open(req,timeout=100)
                            except urllib.error.HTTPError as error:response=error
                            with response:
                                data=json.loads(response.read());status=response.status
                            elapsed=time.monotonic()-began
                            expected_calls=question_count if decisions else 1
                            receipt=rt.receipt(request_id,store.authenticate(key))
                            expected_cost=float(quote.usage({'prompt_tokens':10*expected_calls,'completion_tokens':2*expected_calls})['cost'])
                            valid=(status==200 and data.get('model')=='openai/gpt-6-astra'
                                and receipt['billing_status']=={'complete':True,'calls_started':expected_calls,'calls_completed':expected_calls}
                                and data['usage']['cost']==receipt['billing']['usage']['cost']==expected_cost)
                            if valid:
                                valid=(len(data['answers'])==question_count and all(a['noul']==.9 for a in data['answers'].values())) if decisions else data['choices'][0]['message']['content']=='OK'
                            return {'kind':'decisions' if decisions else 'chat','seconds':elapsed,'valid':valid,'status':status}
                        try:
                            for wave in range(args.waves):
                                with ThreadPoolExecutor(max_workers=64) as clients:values.extend(clients.map(call,range(64)))
                            elapsed=time.monotonic()-start
                            logs=store.logs(limit=1000)
                            row={'workers':count,'kind':kind,'questions':question_count,'round':round_no,'waves':args.waves,
                                'requests':len(values),'correct':sum(v['valid'] for v in values),
                                'wall_s':round(elapsed,4),'good_rpm':round(60*sum(v['valid'] for v in values)/elapsed,2),
                                'within_38s':sum(v['valid'] and v['seconds']<=38 for v in values),
                                'p50_s':percentile([v['seconds'] for v in values],.5),
                                'p95_s':percentile([v['seconds'] for v in values],.95),'max_s':round(max(v['seconds'] for v in values),4),
                                'http_counts':{str(status):sum(v['status']==status for v in values) for status in sorted({v['status'] for v in values})},
                                **samples.finish()}
                            for protocol in ('chat','decisions'):
                                group=[v['seconds'] for v in values if v['kind']==protocol]
                                row[protocol+'_p50_s']=percentile(group,.5)
                                row[protocol+'_p95_s']=percentile(group,.95)
                                row[protocol+'_max_s']=max(group) if group else None
                            row['timing_medians_ms']={name:statistics.median(r[name] for r in logs if r.get(name) is not None)
                                for name in ('validation_ms','schema_wait_ms','schema_execution_ms','queue_wait_ms','output_validation_ms','total_ms') if any(r.get(name) is not None for r in logs)}
                            results.append(row);print(json.dumps(row),flush=True)
                        finally:
                            if samples.thread.is_alive():samples.finish()
                            rt.stop();api.stop();store.revoke(store.authenticate(key)['id']);store.close()
    report={'method':'synthetic loopback HTTP; deterministic runner; real isolated schema children; no subscription CLI',
            'platform':platform.system(),'machine':platform.machine(),'python':platform.python_version(),
            'delay_s':args.delay,'cpu_percent_scale':'100% = one logical core; ps lifetime-average samples, not instantaneous peak',
            'source_hashes':{name:hashlib.sha256((args.source/'desktop_bridge'/name).read_bytes()).hexdigest()
                for name in ('service.py','schema_guard.py','decision_contract.py','decisions.py','process.py','providers.py','store.py','execution_budget.py')
                if (args.source/'desktop_bridge'/name).is_file()},'results':results}
    if args.output:args.output.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
