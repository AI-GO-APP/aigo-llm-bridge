// No request/response payload is written to Durable Object storage or logs.
const MAX_BODY = 3_000_000;
const INFERENCE_CAPACITY=64, CONTROL_CAPACITY=8;
const BATCH_LIMIT=8, BATCH_BYTES=6_100_000;
const inferencePath=(method,path)=>method==="POST"&&["/api/v1/chat/completions","/v1/chat/completions","/api/alpha/decisions","/bridge/v1/jobs","/bridge/v1/models/probe"].includes(path);
const COST_HEADERS=["X-Bridge-Cost-Source","X-Bridge-Pricing-Model","X-Bridge-Pricing-Fetched-At"];
const error = (code, type, message) => Response.json({error:{code,message,metadata:{error_type:type}}},
  {status:code,headers:{"Cache-Control":"no-store"}});
const hash = async text => [...new Uint8Array(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(text)))].map(b=>b.toString(16).padStart(2,"0")).join("");
const envelope=(batch,works)=>{
  const raw=JSON.stringify(batch?{requests:works}:{request:works[0]||null});
  if(new TextEncoder().encode(raw).byteLength>BATCH_BYTES)return error(502,"response_too_large","Relay envelope too large.");
  return new Response(raw,{headers:{'Content-Type':'application/json'}});
};

export default {
  async fetch(request, env) {
    if (!env.DEVICE_KEY) return error(503,"not_configured","Relay is not paired.");
    const id=env.DEVICE.idFromName("primary-device");
    const response=await env.DEVICE.get(id).fetch(request);
    const headers=new Headers(response.headers);
    headers.set('X-Bridge-Relay-Version','0.9.5-relay');
    return new Response(response.body,{status:response.status,headers});
  }
};

export class DeviceRelay {
  constructor(ctx, env) {
    this.ctx=ctx; this.env=env;
    this.pending=new Map(); this.reading=0; this.readingInference=0; this.readingControl=0; this.waiter=null; this.lastSeen=0; this.keys=new Set();this.agentSession=null;
  }
  async body(request,max=MAX_BODY) {
    const length=Number(request.headers.get("content-length")||0);
    if(length>max) throw new Error("size");
    const reader=request.body?.getReader();
    if(!reader) return "";
    let size=0; const parts=[];
    let timer;
    const expired=new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('body timeout')),15_000);});
    try {
      for(;;){ const {done,value}=await Promise.race([reader.read(),expired]); if(done)break;
        size+=value.byteLength; if(size>max)throw new Error('size'); parts.push(value); }
    } catch(error) {reader.cancel().catch(()=>{});throw error;}
    finally {clearTimeout(timer);}
    const all=new Uint8Array(size); let pos=0;
    for(const part of parts){all.set(part,pos);pos+=part.byteLength;}
    return new TextDecoder().decode(all);
  }
  async fetch(request) {
    const path=new URL(request.url).pathname;
    try {
      if(path.startsWith("/agent/")) {
        const supplied=request.headers.get("Authorization")||"";
        // Hash both secrets before comparison; never emit either value.
        if(await hash(supplied)!==await hash("Bearer "+this.env.DEVICE_KEY))return error(401,"authentication","Invalid device key.");
        if(request.method!=="POST")return error(405,"invalid_request","POST required.");
        const data=JSON.parse(await this.body(request,4_100_000));
        if(path==="/agent/poll") {
          const batch=Object.hasOwn(data,'batch_size');
          if(batch&&(!Number.isInteger(data.batch_size)||data.batch_size<1||data.batch_size>BATCH_LIMIT))
            return error(400,"invalid_request","Invalid batch size.");
          if(!Array.isArray(data.key_digests)||data.key_digests.length>1000||data.key_digests.some(k=>typeof k!=="string"||!/^[a-f0-9]{64}$/.test(k)))return error(400,"invalid_request","Invalid key metadata.");
          if(data.agent_session!==undefined&&(typeof data.agent_session!=="string"||!/^[a-f0-9]{32}$/.test(data.agent_session)))return error(400,"invalid_request","Invalid agent session.");
          // A closed local process can leave an HTTP poll alive at the edge. Never
          // send new work to that stale waiter, or replay a dispatched inference.
          if(this.waiter)this.waiter(null);
          const session=data.agent_session||"legacy";
          if(this.agentSession!==null&&this.agentSession!==session){
            for(const [id,item] of this.pending){
              if(!item.dispatched)continue;
              this.pending.delete(id);clearTimeout(item.timer);item.work=null;
              item.resolve(error(503,"device_restarted","Local agent restarted; request was not replayed."));
            }
          }
          this.agentSession=session;
          this.keys=new Set(data.key_digests); this.lastSeen=Date.now();
          const selected=[];
          const limit=batch?data.batch_size:1;
          let bytes=new TextEncoder().encode(batch?'{"requests":[]}':'{"request":null}').byteLength;
          for(const item of this.pending.values()){
            if(item.dispatched)continue;
            const size=new TextEncoder().encode(JSON.stringify(item.work)).byteLength;
            if(selected.length&&bytes+size+1>BATCH_BYTES)break;
            if(bytes+size+1>BATCH_BYTES)return error(502,"response_too_large","Relay envelope too large.");
            selected.push(item);bytes+=size+1;
            if(selected.length>=limit)break;
          }
          if(selected.length){
            const works=selected.map(item=>item.work);
            const response=envelope(batch,works);
            if(!response.ok)return response;
            for(const item of selected)item.dispatched=true;
            return response;
          }
          // One device, one long poll. Never use timers as durable storage.
          const response=await new Promise(resolve=>{
            let completed=false;
            const finish=value=>{
              if(completed)return;
              const response=envelope(batch,value?[value]:[]);
              if(value&&response.ok){const item=this.pending.get(value.id);if(item)item.dispatched=true;}
              completed=true;clearTimeout(timer);this.waiter=null;resolve(response);
            };
            const timer=setTimeout(()=>finish(null),20_000);
            this.waiter=finish;
          });
          this.lastSeen=Date.now();
          return response;
        }
        if(path==="/agent/result") {
          this.lastSeen=Date.now();
          const item=this.pending.get(data.id);
          if(!item)return Response.json({accepted:false});
          if(!Number.isInteger(data.status)||data.status<200||data.status>599||typeof data.body!=="string"||data.body.length>4_000_000)return error(400,"invalid_request","Invalid response.");
          this.pending.delete(data.id);clearTimeout(item.timer);
          const headers={"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"};
          for(const name of COST_HEADERS){const value=data.headers?.[name];if(typeof value==="string"&&/^[\x20-\x7e]{1,200}$/.test(value))headers[name]=value;}
          item.resolve(new Response(data.body,{status:data.status,headers}));
          item.work=null;
          return Response.json({accepted:true});
        }
        return error(404,"not_found","Unknown agent endpoint.");
      }
      if(path==="/health")return Response.json({ok:true,device_online:Date.now()-this.lastSeen<35_000,version:"0.9.5-relay",max_concurrent_requests:INFERENCE_CAPACITY,shared_provider_capacity:true,relay_protocol:'batch8-v1',max_batch_size:BATCH_LIMIT,max_batch_bytes:BATCH_BYTES},{headers:{"Cache-Control":"no-store"}});
      const allowed=(request.method==="POST"&&["/api/v1/chat/completions","/v1/chat/completions","/api/alpha/decisions","/bridge/v1/jobs","/bridge/v1/preflight","/bridge/v1/models/refresh","/bridge/v1/models/probe"].includes(path))
        ||(request.method==="GET"&&(["/api/v1/models","/v1/models","/bridge/v1/model-capabilities"].includes(path)||/^\/bridge\/v1\/jobs\/[a-f0-9]{32}$/.test(path)||/^\/bridge\/v1\/receipts\/[a-f0-9-]{36}$/i.test(path)));
      if(!allowed)return error(404,"not_found","Unknown API endpoint.");
      const authorization=request.headers.get("Authorization")||"";
      if(!authorization.startsWith("Bearer ")||authorization.length>263)return error(401,"authentication","Invalid API key.");
      if(Date.now()-this.lastSeen>=35_000)return error(503,"device_offline","Local computer is offline.");
      if(!this.keys.has(await hash(authorization.slice(7))))return error(401,"authentication","Invalid or revoked API key.");
      const inference=inferencePath(request.method,path);
      const active=[...this.pending.values()].filter(item=>item.inference===inference).length;
      const reading=inference?this.readingInference:this.readingControl;
      if(active+reading>=(inference?INFERENCE_CAPACITY:CONTROL_CAPACITY))return error(429,"queue_full","Device concurrent capacity reached.");
      // Reserve synchronously before yielding to body I/O; count in-flight reads.
      this.reading++; if(inference)this.readingInference++;else this.readingControl++;
      let body;
      try {body=request.method==="POST"?await this.body(request):"";}
      finally {this.reading--;if(inference)this.readingInference--;else this.readingControl--;}
      const id=crypto.randomUUID();
      const deadline=Math.min(Date.now()+90_000,Number(request.headers.get("X-Bridge-Deadline"))||Date.now()+90_000);
      const requestId=request.headers.get("X-AIEA-Request-Id");
      if(requestId&&!/^[a-f0-9-]{36}$/i.test(requestId))return error(400,"invalid_request","Invalid request ID.");
      const work={id,path,method:request.method,authorization,body,deadline,request_id:requestId};
      return await new Promise(resolve=>{
        const timer=setTimeout(()=>{
          const item=this.pending.get(id);this.pending.delete(id);
          if(item)item.work=null;
          resolve(error(408,"timeout","Device response timed out."));
        },Math.max(1,deadline-Date.now()+2000));
        const item={work,resolve,timer,dispatched:false,inference};this.pending.set(id,item);
        if(this.waiter)this.waiter(work);
      });
    } catch {return error(400,"invalid_request","Invalid or oversized request.");}
  }
}
