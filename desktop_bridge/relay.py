"""Outbound HTTPS poll relay. Bodies and authorization headers stay in RAM."""
import json
import threading
import urllib.request
import urllib.error
import ssl
import certifi
import uuid
import random
from concurrent.futures import ThreadPoolExecutor

COST_HEADERS=('X-Bridge-Cost-Source','X-Bridge-Pricing-Model','X-Bridge-Pricing-Fetched-At')
MAX_CLOUD_BODY=6_100_000  # A 3 MB request JSON string can double during relay encoding.


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*_args,**_kwargs):
        return None


def read_cloud(response,limit=MAX_CLOUD_BODY):
    raw=response.read(limit+1)
    if len(raw)>limit:raise ValueError('Relay response too large')
    value=json.loads(raw)
    if not isinstance(value,dict):raise ValueError('Invalid relay response')
    return value

from . import secret
from .capacity import STANDARD_CONCURRENCY, CONTROL_CONCURRENCY, is_inference_request


class Relay:
    def __init__(self,store,port):
        self.store,self.port=store,port
        self.agent_session=uuid.uuid4().hex
        self.stop_event=threading.Event(); self.thread=None; self.state="未連線"
        self.pool=ThreadPoolExecutor(max_workers=STANDARD_CONCURRENCY,thread_name_prefix="relay-forward")
        self.control_pool=ThreadPoolExecutor(max_workers=CONTROL_CONCURRENCY,thread_name_prefix="relay-control")
        self.cloud_opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
        self.cloud_opener.addheaders=[("User-Agent","local-token-buffet-bridge/0.2.0")]
    def start(self):
        if self.thread and self.thread.is_alive(): self.stop_event.clear(); return
        if not self.store.get("public_url"):
            raise ValueError("請先填入已部署的固定 HTTPS 網址。")
        if not secret.load(self.store.directory):
            raise ValueError("請先設定雲端轉接的裝置配對 key。")
        self.stop_event.clear()
        self.thread=threading.Thread(target=self.loop,daemon=True,name="bridge-relay"); self.thread.start()
    def stop(self):
        self.stop_event.set(); self.state="已停止"
    def loop(self):
        backoff=1
        while not self.stop_event.is_set():
            try:
                base=self.store.get("public_url").rstrip("/")
                device_key=secret.load(self.store.directory)
                with self.store.lock:
                    digests=[r[0] for r in self.store.db.execute("select digest from api_keys where revoked_ts is null")]
                def cloud(path,body):
                    raw=json.dumps(body,separators=(",",":")).encode()
                    req=urllib.request.Request(base+path,data=raw,headers={"Authorization":"Bearer "+device_key,"Content-Type":"application/json"})
                    with self.cloud_opener.open(req,timeout=30) as res: return read_cloud(res)
                item=cloud("/agent/poll",{"key_digests":digests,"agent_session":self.agent_session})
                self.state="已連線"; backoff=1
                work=item.get("request")
                if not work: continue
                pool=self.pool if is_inference_request(work.get("method"),work.get("path")) else self.control_pool
                pool.submit(self.forward,work,base,device_key)
                work=None; item=None
            except Exception:
                # Never log urllib exceptions: they may contain headers, paths or payloads.
                self.state="離線／重連中"
                self.stop_event.wait(backoff+random.uniform(0,backoff*.25)); backoff=min(20,backoff*2)

    def forward(self,work,base,device_key):
            local_opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            try:
                path=work.get("path","")
                allowed=(path in {"/api/v1/models","/v1/models","/api/v1/chat/completions","/v1/chat/completions","/api/alpha/decisions","/bridge/v1/jobs","/bridge/v1/preflight","/bridge/v1/model-capabilities","/bridge/v1/models/refresh","/bridge/v1/models/probe"}
                         or path.startswith("/bridge/v1/jobs/") or path.startswith('/bridge/v1/receipts/'))
                if not allowed or work.get("method") not in {"GET","POST"}: raise ValueError("Invalid relay request")
                req=urllib.request.Request(f"http://127.0.0.1:{self.port}"+path,
                    data=work.get("body","").encode() if work["method"]=="POST" else None,
                    method=work["method"],headers={"Authorization":work.get("authorization",""),"Content-Type":"application/json",
                        **({"X-AIEA-Request-Id":work["request_id"]} if work.get("request_id") else {}),
                        **({"X-Bridge-Deadline":str(work["deadline"])} if work.get("deadline") else {})})
                try:
                    with local_opener.open(req,timeout=self.store.get("timeout_s")+10) as res:
                        result={"id":work["id"],"status":res.status,"body":res.read(4_000_001).decode(),
                                "headers":{name:res.headers[name] for name in COST_HEADERS if res.headers.get(name)}}
                except urllib.error.HTTPError as error:
                    result={"id":work["id"],"status":error.code,"body":error.read(4_000_001).decode()}
                work=None
                if len(result["body"])>4_000_000:
                    result={"id":result["id"],"status":502,"body":'{"error":{"code":502,"message":"Response too large"}}'}
                req=urllib.request.Request(base+"/agent/result",data=json.dumps(result,separators=(",",":")).encode(),
                    headers={"Authorization":"Bearer "+device_key,"Content-Type":"application/json"})
                with self.cloud_opener.open(req,timeout=30) as response: read_cloud(response,1000)
                result=None
            except Exception:
                self.state="回傳中斷／等待下一筆請求"
