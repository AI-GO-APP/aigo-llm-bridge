from __future__ import annotations

from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import hashlib
import select
import socket
import threading
import time
import uuid

from .capacity import STANDARD_CONCURRENCY
from .schema_guard import validate_instances

from . import __version__, providers
from .contract import validate
from .errors import BridgeError
from .pricing import Catalog, combine_usage
from .model_catalog import ModelCatalog
from .decision_contract import DecisionSpec, strict_loads, validate as validate_decisions
from .decisions import answer as decision_answer


@dataclass
class Task:
    id: str
    key_id: str
    created: float
    done: threading.Event = field(default_factory=threading.Event)
    cancel: threading.Event = field(default_factory=threading.Event)
    result: dict | None = None
    error: BridgeError | None = None
    completed: float | None = None
    pricing_headers: dict = field(default_factory=dict)
    deadline: float | None = None
    protocol: str = "chat"
    usage: dict | None = None
    calls_started: int = 0
    calls_completed: int = 0


class Runtime:
    def __init__(self,store,runner=None,pricing=None,model_catalog=None,*,max_workers=None,max_pending=None):
        self.store=store
        self.runner=runner or providers.infer
        self.pricing=pricing or Catalog(store.directory)
        self.models=model_catalog or ModelCatalog(store)
        workers=store.get('inference_workers') if max_workers is None else max_workers
        pending=workers if max_pending is None else max_pending
        if type(workers) is not int or not 1<=workers<=STANDARD_CONCURRENCY:
            raise ValueError('inference_workers must be an integer from 1 to 64.')
        if type(pending) is not int or not workers<=pending<=STANDARD_CONCURRENCY:
            raise ValueError('max_pending must be an integer between workers and 64.')
        self.max_workers,self.max_pending=workers,pending
        self.pool=ThreadPoolExecutor(max_workers=workers,thread_name_prefix="bridge-inference")
        self.slots=threading.BoundedSemaphore(pending)
        self.lock=threading.RLock()
        self.tasks={}
        self.rate=defaultdict(deque)
        self.stopped=False

    def authorize(self,header):
        token=header[7:] if header.startswith("Bearer ") else ""
        caller=self.store.authenticate(token)
        if caller is None: raise BridgeError(401,"authentication","API key 無效或已撤銷。")
        return caller

    def validate_request(self,body,caller,protocol):
        validator=validate_decisions if protocol=="decisions" else validate
        try: return validator(body,self.store,caller)
        except BridgeError as error:
            if error.category!="model_not_found": raise
        # Discovered native IDs can be called without mutating the owner's model registry.
        registered=self.store.get('models')
        merged=registered+[m for m in self.models.routing_models(caller) if not any(r['id']==m['id'] for r in registered)]
        store=self.store
        class RoutingSettings:
            def get(self,name): return merged if name=='models' else store.get(name)
        return validator(body,RoutingSettings(),caller)

    def preflight(self,body,caller):
        protocol='decisions' if isinstance(body,dict) and ('state' in body or 'questions' in body) else 'chat'
        spec=self.validate_request(body,caller,protocol)
        if self.stopped or not self.store.get("accepting"):
            raise BridgeError(503,"device_paused","服務目前暫停接單。")
        with self.lock:
            if sum(not t.done.is_set() for t in self.tasks.values())>=self.max_pending:
                raise BridgeError(429,"queue_full","同時推論已達裝置容量。")
        return spec

    def submit(self,body,caller,input_bytes,request_id=None,deadline=None,protocol="chat"):
        spec=self.validate_request(body,caller,protocol)
        if self.stopped or not self.store.get("accepting"):
            raise BridgeError(503,"device_paused","本機目前暫停接單。")
        with self.lock:
            self.cleanup()
            if request_id:
                try: request_id=str(uuid.UUID(request_id))
                except (ValueError,TypeError): raise BridgeError(400,"invalid_request","請求識別碼無效。") from None
                digest=hashlib.sha256((caller["id"]+protocol+json.dumps(body,sort_keys=protocol!="decisions",separators=(",",":"))).encode()).hexdigest()
                with self.store.lock:
                    row=self.store.db.execute("select id,request_digest from requests where key_id=? and client_request_id=?",(caller["id"],request_id)).fetchone()
                if row:
                    if row["request_digest"]!=digest:raise BridgeError(409,"request_conflict","請求識別碼已用於其他內容。")
                    task=self.tasks.get(row["id"])
                    if task:return task
                    raise BridgeError(409,"request_already_processed","請求已受理，不會重新執行。")
            now=time.monotonic(); history=self.rate[caller["id"]]
            while history and history[0]<now-60: history.popleft()
            if len(history)>=caller["rpm"]: raise BridgeError(429,"rate_limit_exceeded","這把 key 已達每分鐘上限。")
            if not self.slots.acquire(blocking=False): raise BridgeError(429,"queue_full","同時推論已達裝置容量。")
            history.append(now)
            rid=uuid.uuid4().hex
            task=Task(rid,caller["id"],time.time(),deadline=deadline,protocol=protocol)
            try:
                self.store.insert_request({"id":rid,"key_id":caller["id"],"model":spec.model["id"],"provider":spec.model["provider"],
                    "created_ts":task.created,"status":"queued","input_bytes":input_bytes,"protocol":protocol,
                    "question_count":len(spec.questions) if isinstance(spec,DecisionSpec) else 0,
                    "calls_started":0,"calls_completed":0,"billing_complete":1},(request_id,digest) if request_id else None)
                self.tasks[rid]=task
                self.pool.submit(self.execute,task,spec)
            except Exception:
                self.tasks.pop(rid,None); self.slots.release(); raise
        return task

    def check_execution(self,task,deadline):
        if task.cancel.is_set() or self.stopped: raise BridgeError(499,"cancelled","請求已取消。")
        if time.time()>=deadline: raise BridgeError(408,"timeout","請求期限已過。")
        with self.store.lock:
            key=self.store.db.execute("select revoked_ts from api_keys where id=?",(task.key_id,)).fetchone()
        if key is None or key[0] is not None: raise BridgeError(401,"authentication","API key 已撤銷。")

    def run_call(self,task,spec,quote,deadline,generation):
        self.check_execution(task,deadline)
        if generation!=self.models.generation(spec.model['provider'],self.store):
            raise BridgeError(503,'provider_authentication','推論期間登入或 CLI 設定已變更；不切換來源繼續執行。')
        store=self.store
        class DeadlineSettings:
            def get(self,name):
                return max(.001,min(store.get(name),deadline-time.time())) if name=="timeout_s" else store.get(name)
        task.calls_started+=1
        self.store.update_request(task.id,calls_started=task.calls_started,billing_complete=0)
        result=self.runner(spec,DeadlineSettings(),task.cancel)
        text,usage,finish=result[:3]
        if len(result)==4 and result[3]!=spec.model['native']:
            # Never price a silently substituted model using the requested model's rates.
            raise BridgeError(502,'model_mismatch','CLI 使用的模型與請求不同；此呼叫用量尚未完成核對。')
        usage=quote.usage(usage)
        task.usage=combine_usage(task.usage,usage)
        task.calls_completed+=1
        # Save known usage before validating content, cancellation, or later questions.
        self.store.update_request(task.id,prompt_tokens=task.usage['prompt_tokens'],completion_tokens=task.usage['completion_tokens'],
            cost_usd=task.usage['cost'],pricing_model=quote.model,pricing_fetched_ts=quote.fetched_at,
            cached_tokens=task.usage.get('prompt_tokens_details',{}).get('cached_tokens'),
            cache_write_tokens=task.usage.get('prompt_tokens_details',{}).get('cache_write_tokens'),
            reasoning_tokens=task.usage.get('completion_tokens_details',{}).get('reasoning_tokens'),
            calls_completed=task.calls_completed,billing_complete=1)
        self.check_execution(task,deadline)
        if not isinstance(text,str): raise BridgeError(502,"invalid_provider_response","模型未返回文字內容。")
        return text,task.usage,finish

    def execute(self,task,spec):
        start=time.monotonic()
        generation=None
        try:
            deadline=min(task.deadline or float('inf'),time.time()+self.store.get('timeout_s'))
            self.check_execution(task,deadline)
            self.store.update_request(task.id,status="running",started_ts=time.time())
            generation=self.models.generation(spec.model['provider'],self.store)
            quote=self.pricing.quote(spec.model)
            if isinstance(spec,DecisionSpec):
                answers={}
                for name,question in spec.questions.items():
                    inference=spec.inference(question)
                    text,usage,finish=self.run_call(task,inference,quote,deadline,generation)
                    if finish!='stop': raise BridgeError(502,'invalid_structured_output','Decisions 推論未完整完成。')
                    answers[name]=decision_answer(text,question,inference.schema,task.cancel)
                task.result={'id':'gen-'+task.id,'model':spec.model['id'],'provider':spec.model['provider'],
                    'answers':answers,'usage':{'input_tokens':usage['prompt_tokens'],
                                              'output_tokens':usage['completion_tokens'],'cost':usage['cost']}}
                text=json.dumps(answers,ensure_ascii=False)
            else:
                text,usage,finish=self.run_call(task,spec,quote,deadline,generation)
            if not isinstance(spec,DecisionSpec) and spec.format in {"json_object","json_schema"}:
                try:
                    value=json.loads(text)
                    if not isinstance(value,dict): raise ValueError()
                    if spec.schema and not validate_instances([[spec.schema,value]],task.cancel):raise ValueError()
                except ValueError:
                    raise BridgeError(502,"invalid_structured_output","模型輸出未符合 JSON 格式或指定 schema。") from None
            prompt=usage['prompt_tokens'];completion=usage['completion_tokens']
            task.pricing_headers=quote.headers
            if not isinstance(spec,DecisionSpec):
                if finish not in {"stop","length","content_filter"}: finish="stop"
                message={"role":"assistant","content":text}
                if spec.tool_proposals:
                    from .tool_contract import proposal_message
                    message,finish=proposal_message(json.loads(text),spec.tool_schemas)
                task.result={"id":"gen-"+task.id,"object":"chat.completion","created":int(task.created),"model":spec.model["id"],
                    "system_fingerprint":None,"choices":[{"index":0,"message":message,"finish_reason":finish}],"usage":usage}
            self.models.observe(spec.model,task.protocol,generation)
            self.store.update_request(task.id,status="completed",http_status=200,finished_ts=time.time(),
                duration_ms=round((time.monotonic()-start)*1000),output_bytes=len(text.encode()),prompt_tokens=prompt,completion_tokens=completion,
                cost_usd=usage['cost'],pricing_model=quote.model,pricing_fetched_ts=quote.fetched_at,
                cached_tokens=usage.get('prompt_tokens_details',{}).get('cached_tokens'),
                cache_write_tokens=usage.get('prompt_tokens_details',{}).get('cache_write_tokens'),
                reasoning_tokens=usage.get('completion_tokens_details',{}).get('reasoning_tokens'))
        except BridgeError as error:
            if generation is not None: self.models.observe(spec.model,task.protocol,generation,error)
            task.error=error
            self.store.update_request(task.id,status="cancelled" if error.category=="cancelled" else "failed",http_status=error.status,
                error_code=error.category,finished_ts=time.time(),duration_ms=round((time.monotonic()-start)*1000))
        except Exception:
            # No exception text, traceback, local path, prompt, header or native event is logged.
            task.error=BridgeError(500,"server","服務無法完成此請求；請檢查 CLI 狀態。")
            self.store.update_request(task.id,status="failed",http_status=500,error_code="server",finished_ts=time.time())
        finally:
            spec=None
            task.completed=time.time(); task.done.set(); self.slots.release()

    def get_job(self,rid,caller):
        row=self.store.request(rid,caller["id"])
        if row is None: raise BridgeError(404,"not_found","找不到工作。")
        with self.lock:
            self.cleanup(); task=self.tasks.get(rid)
            result={"id":rid,"status":row["status"],"created":int(row["created_ts"])}
            if task and task.done.is_set():
                if task.error: result.update(task.error.body())
                elif task.result is not None: result["result"]=task.result
            elif row["status"]=="completed":
                result.update({"status":"expired","error":{"code":410,"message":"結果已從記憶體清除；本機未保存內容。"}})
            elif row["status"] in {"interrupted","failed","cancelled"}:
                result["error"]={"code":row["http_status"] or 503,"message":"工作已結束或因程序重啟中斷；本機不保存原始內容。"}
            return result

    def receipt(self,request_id,caller):
        try:request_id=str(uuid.UUID(request_id))
        except ValueError:raise BridgeError(404,"not_found","找不到請求。") from None
        with self.store.lock:
            row=self.store.db.execute('select * from requests where key_id=? and client_request_id=?',
                                      (caller['id'],request_id)).fetchone()
        if row is None:raise BridgeError(404,"not_found","找不到請求。")
        result=self.get_job(row['id'],caller)
        terminal=row['status'] not in {'queued','running'}
        if not terminal:
            # Billing and state must use the same snapshot, even if the task just finished.
            result['status']=row['status'];result.pop('result',None)
        result['billing_status']={'complete':bool(row['billing_complete']) and terminal,
                                  'calls_started':row['calls_started'],'calls_completed':row['calls_completed']}
        if row['cost_usd'] is not None:
            result['billing']={'generation_id':'gen-'+row['id'],'model':row['pricing_model'],
                               'usage':{'prompt_tokens':row['prompt_tokens'],'completion_tokens':row['completion_tokens'],
                                        'cost':row['cost_usd']}}
        return result

    def cleanup(self):
        for rid,task in list(self.tasks.items()):
            if task.completed and task.completed<time.time()-600:
                del self.tasks[rid]

    def cancel_key(self,kid):
        with self.lock:
            for task in self.tasks.values():
                if task.key_id==kid and not task.done.is_set(): task.cancel.set()

    def stop(self):
        self.stopped=True
        with self.lock:
            for task in self.tasks.values():
                if not task.done.is_set(): task.cancel.set()
        self.pool.shutdown(wait=True,cancel_futures=False)
        self.tasks.clear()


class ApiServer:
    def __init__(self,runtime,port=None):
        self.runtime=runtime
        rt=runtime
        class Handler(BaseHTTPRequestHandler):
            protocol_version="HTTP/1.1"
            server_version="LLMBridge"
            def log_message(self,*_): pass
            def reply(self,status,value,extra_headers=None):
                raw=json.dumps(value,ensure_ascii=False,separators=(",",":")).encode()
                self.send_response(status)
                self.send_header("Content-Type","application/json; charset=utf-8")
                self.send_header("Content-Length",str(len(raw)))
                self.send_header("Cache-Control","no-store")
                self.send_header("Connection","close")
                for name,value in (extra_headers or {}).items():self.send_header(name,value)
                if status==429: self.send_header("Retry-After","60")
                self.end_headers(); self.close_connection=True
                try: self.wfile.write(raw)
                except (BrokenPipeError,ConnectionResetError): pass
            def do_GET(self): self.dispatch(False)
            def do_POST(self): self.dispatch(True)
            def do_DELETE(self): self.reply(405,{"error":{"code":405,"message":"Method not allowed"}})
            def dispatch(self,is_post):
                task=None; caller=None; length=0
                try:
                    path=self.path.split("?",1)[0]
                    if not is_post and path=="/health":
                        return self.reply(200,{"ok":True,"version":__version__,"accepting":rt.store.get("accepting"),"max_concurrent_requests":rt.max_workers,"shared_provider_capacity":True})
                    caller=rt.authorize(self.headers.get("Authorization",""))
                    if not is_post and path.startswith('/bridge/v1/receipts/'):
                        return self.reply(200,rt.receipt(path.removeprefix('/bridge/v1/receipts/'),caller))
                    if not is_post and path in {"/api/v1/models","/v1/models"}:
                        return self.reply(200,rt.models.models(caller))
                    if not is_post and path=="/bridge/v1/model-capabilities":
                        return self.reply(200,rt.models.capabilities(caller))
                    if not is_post and path.startswith("/bridge/v1/jobs/"):
                        rid=path.removeprefix("/bridge/v1/jobs/")
                        if not len(rid)==32 or any(c not in "0123456789abcdef" for c in rid):
                            raise BridgeError(404,"not_found","找不到工作。")
                        return self.reply(200,rt.get_job(rid,caller))
                    if not is_post or path not in {"/api/v1/chat/completions","/v1/chat/completions","/api/alpha/decisions","/bridge/v1/jobs","/bridge/v1/preflight","/bridge/v1/models/refresh","/bridge/v1/models/probe"}:
                        raise BridgeError(404,"not_found","找不到端點。")
                    if self.headers.get("Transfer-Encoding"):
                        raise BridgeError(400,"invalid_request","請使用 Content-Length，P1 不接受 chunked request。")
                    try: length=int(self.headers.get("Content-Length","0"))
                    except ValueError: raise BridgeError(400,"invalid_request","Content-Length 無效。") from None
                    if not 0<length<=3_000_000: raise BridgeError(413,"request_too_large","Request body 上限為 3 MB。")
                    if self.headers.get("Content-Type","").split(";",1)[0].strip()!="application/json":
                        raise BridgeError(415,"invalid_request","請使用 application/json。")
                    self.connection.settimeout(20)
                    raw=self.rfile.read(length)
                    if len(raw)!=length: raise BridgeError(400,"invalid_request","Request body 不完整。")
                    try: body=strict_loads(raw)
                    except (ValueError,UnicodeError,RecursionError): raise BridgeError(400,"invalid_request","Request body 不是合法 JSON。") from None
                    if path=="/bridge/v1/models/refresh":
                        if body!={}: raise BridgeError(400,"invalid_request","refresh body 必須是空 object。")
                        return self.reply(200,rt.models.capabilities(caller,refresh=True))
                    protocol='decisions' if path=='/api/alpha/decisions' else 'chat'
                    if path=='/bridge/v1/jobs' and isinstance(body,dict) and ('state' in body or 'questions' in body):
                        protocol='decisions'
                    if path=='/bridge/v1/models/probe':
                        if not isinstance(body,dict) or set(body)-{'model','protocol'} or not isinstance(body.get('model'),str):
                            raise BridgeError(400,'invalid_request','probe 僅接受 model 與可選 protocol。')
                        protocol=body.get('protocol','chat')
                        if protocol not in ('chat','decisions'): raise BridgeError(400,'invalid_request','probe protocol 支援 chat 或 decisions。','protocol')
                        model=body['model']
                        body=({'model':model,'state':'A synthetic object is blue.',
                               'questions':{'blue':{'type':'noul','instructions':'Is the object blue?'}}}
                              if protocol=='decisions' else {'model':model,'messages':[{'role':'user','content':'Reply exactly PONG.'}]})
                    if path=="/bridge/v1/preflight":
                        spec=rt.preflight(body,caller)
                        return self.reply(200,{"ready":True,"model":spec.model["id"],"subscription_verified":False,"expires_in_s":5})
                    deadline=None
                    if self.headers.get("X-Bridge-Deadline"):
                        try:
                            deadline=float(self.headers["X-Bridge-Deadline"])/1000
                            if not 0<deadline<1e14:raise ValueError()
                        except ValueError:raise BridgeError(400,"invalid_request","請求期限無效。") from None
                    task=rt.submit(body,caller,length,self.headers.get("X-AIEA-Request-Id"),deadline,protocol)
                    raw=None; body=None
                    if path=="/bridge/v1/jobs":
                        return self.reply(202,{"id":task.id,"status":"queued","created":int(task.created)})
                    # Separate job API owns asynchronous semantics; chat always yields a completion/error.
                    while not task.done.wait(.2):
                        try:
                            if select.select([self.connection],[],[],0)[0] and self.connection.recv(1,socket.MSG_PEEK)==b"":
                                task.cancel.set(); return
                        except OSError: task.cancel.set(); return
                    if task.error: raise task.error
                    self.reply(200,task.result,task.pricing_headers)
                    if not self.headers.get("X-AIEA-Request-Id"):
                        with rt.lock: rt.tasks.pop(task.id,None)
                except BridgeError as error:
                    if is_post and task is None:
                        # Even rejected inference requests leave only fixed-category metadata.
                        try:
                            rt.store.insert_request({"id":uuid.uuid4().hex,"key_id":caller["id"] if caller else None,
                                "created_ts":time.time(),"finished_ts":time.time(),"status":"rejected",
                                "http_status":error.status,"error_code":error.category,"input_bytes":max(0,min(length,3_000_000))})
                        except Exception: pass
                    error_body=error.body()
                    if task is not None and task.done.is_set() and error.status==408:
                        error_body['error']['metadata']['execution_state']='terminated'
                    self.reply(error.status,error_body)
                except (OSError,TimeoutError): pass
                except Exception: self.reply(500,BridgeError(500,"server","服務無法完成請求。請檢查本機狀態。").body())
        class Server(ThreadingHTTPServer):
            request_queue_size=128
            daemon_threads=True
            allow_reuse_address=True
            def handle_error(self,*_): pass
        self.server=Server(("127.0.0.1",rt.store.get("port") if port is None else port),Handler)
        self.port=self.server.server_port
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True,name="bridge-http")
    def start(self): self.thread.start()
    def stop(self): self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=5)
