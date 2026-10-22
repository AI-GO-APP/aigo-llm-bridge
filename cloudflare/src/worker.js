// No request/response payload is written to Durable Object storage or logs.
const MAX_BODY = 3_000_000;
const COST_HEADERS=["X-Bridge-Cost-Source","X-Bridge-Pricing-Model","X-Bridge-Pricing-Fetched-At"];
const error = (code, type, message) => Response.json({error:{code,message,metadata:{error_type:type}}},
  {status:code,headers:{"Cache-Control":"no-store"}});
const hash = async text => [...new Uint8Array(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(text)))].map(b=>b.toString(16).padStart(2,"0")).join("");

export default {
  async fetch(request, env) {
    if (!env.DEVICE_KEY) return error(503,"not_configured","Relay is not paired.");
    const id=env.DEVICE.idFromName("primary-device");
    const response=await env.DEVICE.get(id).fetch(request);
    const headers=new Headers(response.headers);
    headers.set('X-Bridge-Relay-Version','0.3.4-relay');
    return new Response(response.body,{status:response.status,headers});
  }
};

export class DeviceRelay {
  constructor(ctx, env) {
    this.ctx=ctx; this.env=env;
    this.pending=new Map(); this.waiter=null; this.lastSeen=0; this.keys=new Set();this.agentSession=null;
  }
  async body(request,max=MAX_BODY) {
    const length=Number(request.headers.get("content-length")||0);
    if(length>max) throw new Error("size");
    const reader=request.body?.getReader();
    if(!reader) return "";
    let size=0; const parts=[];
    for(;;){ const {done,value}=await reader.read(); if(done)break;
      size+=value.byteLength; if(size>max){ await reader.cancel(); throw new Error("size"); } parts.push(value); }
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
          const next=[...this.pending.values()].find(p=>!p.dispatched);
          if(next){next.dispatched=true;return Response.json({request:next.work});}
          // One device, one long poll. Never use timers as durable storage.
          const work=await new Promise(resolve=>{
            let completed=false;
            const finish=value=>{if(completed)return;completed=true;clearTimeout(timer);this.waiter=null;resolve(value);};
            const timer=setTimeout(()=>finish(null),20_000);
            this.waiter=finish;
          });
          this.lastSeen=Date.now();
          return Response.json({request:work});
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
      if(path==="/health")return Response.json({ok:true,device_online:Date.now()-this.lastSeen<35_000,version:"0.3.4-relay"},{headers:{"Cache-Control":"no-store"}});
      const allowed=(request.method==="POST"&&["/api/v1/chat/completions","/v1/chat/completions","/bridge/v1/jobs","/bridge/v1/preflight"].includes(path))
        ||(request.method==="GET"&&(["/api/v1/models","/v1/models"].includes(path)||/^\/bridge\/v1\/jobs\/[a-f0-9]{32}$/.test(path)||/^\/bridge\/v1\/receipts\/[a-f0-9-]{36}$/i.test(path)));
      if(!allowed)return error(404,"not_found","Unknown API endpoint.");
      const authorization=request.headers.get("Authorization")||"";
      if(!authorization.startsWith("Bearer ")||authorization.length>263)return error(401,"authentication","Invalid API key.");
      if(Date.now()-this.lastSeen>=35_000)return error(503,"device_offline","Local computer is offline.");
      if(!this.keys.has(await hash(authorization.slice(7))))return error(401,"authentication","Invalid or revoked API key.");
      if(this.pending.size>=9)return error(429,"queue_full","Device queue is full.");
      const body=request.method==="POST"?await this.body(request):"";
      const id=crypto.randomUUID();
      const deadline=Math.min(Date.now()+90_000,Number(request.headers.get("X-Bridge-Deadline"))||Date.now()+90_000);
      const requestId=request.headers.get("X-AIEA-Request-Id");
      if(requestId&&!/^[a-f0-9-]{36}$/i.test(requestId))return error(400,"invalid_request","Invalid request ID.");
      const work={id,path,method:request.method,authorization,body,deadline,request_id:requestId};
      return await new Promise(resolve=>{
        const timer=setTimeout(()=>{
          const item=this.pending.get(id);this.pending.delete(id);
          if(item)item.work=null;
          resolve(error(408,"timeout","Device response timed out. Use /bridge/v1/jobs for long work."));
        },Math.max(1,deadline-Date.now()+2000));
        const item={work,resolve,timer,dispatched:false};this.pending.set(id,item);
        if(this.waiter){item.dispatched=true;this.waiter(work);}
      });
    } catch {return error(400,"invalid_request","Invalid or oversized request.");}
  }
}
