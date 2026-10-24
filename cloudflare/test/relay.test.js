import {test} from 'node:test';
import assert from 'node:assert/strict';
import worker,{DeviceRelay} from '../src/worker.js';
const device='x'.repeat(48);
const digest=async s=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s)))].map(v=>v.toString(16).padStart(2,'0')).join('');
const req=(path,body,token=device)=>new Request('https://test.workers.dev'+path,{method:'POST',headers:{Authorization:'Bearer '+token},body:JSON.stringify(body)});

test('batch FIFO, legacy envelope and invalid sizes preserve at-most-once dispatch',async()=>{
 const r=new DeviceRelay({storage:{put(){throw Error('payload storage forbidden')}}},{DEVICE_KEY:device});
 const key='synthetic-batch-key',keys=[await digest(key)];r.keys=new Set(keys);r.lastSeen=Date.now();
 const external=Array.from({length:16},()=>r.fetch(req('/api/v1/chat/completions',{},key)));
 await new Promise(resolve=>setTimeout(resolve,20));const ids=[...r.pending.keys()];
 try{
  for(const size of [true,1.5,0,9,'8'])assert.equal((await r.fetch(req('/agent/poll',{key_digests:keys,batch_size:size}))).status,400);
  assert.ok([...r.pending.values()].every(x=>!x.dispatched));
  const first=(await(await r.fetch(req('/agent/poll',{key_digests:keys,batch_size:8}))).json()).requests;
  const legacy=(await(await r.fetch(req('/agent/poll',{key_digests:keys}))).json()).request;
  const rest=(await(await r.fetch(req('/agent/poll',{key_digests:keys,batch_size:8}))).json()).requests;
  assert.deepEqual([...first,legacy,...rest].map(x=>x.id),ids);
  assert.equal(new Set([...first,legacy,...rest].map(x=>x.id)).size,16);
 }finally{for(const item of r.pending.values()){clearTimeout(item.timer);item.resolve(Response.json({ok:true}));}r.pending.clear();await Promise.all(external);}
});

test('batch byte cap counts encoded escaping and leaves remainder queued',async()=>{
 const r=new DeviceRelay({}, {DEVICE_KEY:device}),key='synthetic-byte-key',keys=[await digest(key)];
 r.keys=new Set(keys);r.lastSeen=Date.now();
 const external=Array.from({length:2},()=>r.fetch(req('/api/v1/chat/completions',{synthetic:'\\'.repeat(900000)},key)));
 await new Promise(resolve=>setTimeout(resolve,30));
 try{
  const raw=await(await r.fetch(req('/agent/poll',{key_digests:keys,batch_size:8}))).text();
  assert.ok(new TextEncoder().encode(raw).byteLength<=6_100_000);
  assert.equal(JSON.parse(raw).requests.length,1);
  assert.equal([...r.pending.values()].filter(x=>x.dispatched).length,1);
  assert.equal((await(await r.fetch(req('/agent/poll',{key_digests:keys,batch_size:8}))).json()).requests.length,1);
 }finally{for(const item of r.pending.values()){clearTimeout(item.timer);item.resolve(Response.json({ok:true}));}r.pending.clear();await Promise.all(external);}
});

test('queue reserves capacity before asynchronous body reads and releases failures',async()=>{
 const relay=new DeviceRelay({}, {DEVICE_KEY:device});const key='synthetic-queue-key';
 relay.keys.add(await digest(key));relay.lastSeen=Date.now();
 const release=[];
 relay.body=async()=>new Promise(resolve=>release.push(resolve));
 const work=Array.from({length:67},()=>relay.fetch(req('/api/v1/chat/completions',{},key)));
 await new Promise(resolve=>setTimeout(resolve,20));
 assert.equal(release.length,64);assert.equal(relay.reading,64);
 release.forEach(resolve=>resolve('{}'));
 await new Promise(resolve=>setTimeout(resolve,20));
 assert.equal(relay.pending.size,64);assert.equal(relay.reading,0);
 for(const item of relay.pending.values()){clearTimeout(item.timer);item.resolve(new Response('{}'));}
 relay.pending.clear();const responses=await Promise.all(work);
 assert.equal(responses.filter(r=>r.status===429).length,3);
 relay.body=async()=>{throw Error('synthetic body failure')};
 assert.equal((await relay.fetch(req('/api/v1/chat/completions',{},key))).status,400);
 assert.equal(relay.reading,0);assert.equal(relay.pending.size,0);
});

test('outer build header preserves the original actor identity and response',async()=>{
 let actor;
 const env={DEVICE_KEY:device,DEVICE:{idFromName(name){actor=name;return 'existing-id';},get(id){
   assert.equal(id,'existing-id');return {fetch:async()=>Response.json({version:'legacy'},{headers:{'Cache-Control':'no-store'}})};
 }}};
 const res=await worker.fetch(new Request('https://test.workers.dev/health'),env);
 assert.equal(actor,'primary-device');
 assert.equal(res.headers.get('X-Bridge-Relay-Version'),'0.9.5-relay');
 assert.equal(res.headers.get('Cache-Control'),'no-store');
 assert.equal((await res.json()).version,'legacy');
});

test('64 inference requests share chat and decisions capacity with eight independent controls',async()=>{
 const relay=new DeviceRelay({}, {DEVICE_KEY:device});const key='synthetic-capacity';
 relay.keys.add(await digest(key));relay.lastSeen=Date.now();
 const paths=['/api/v1/chat/completions','/api/alpha/decisions'];
 const work=Array.from({length:64},(_,i)=>relay.fetch(req(paths[i%2],{},key)));
 await new Promise(resolve=>setTimeout(resolve,20));
 assert.equal(relay.pending.size,64);
 assert.equal((await relay.fetch(req(paths[0],{},key))).status,429);
 const controls=Array.from({length:8},()=>relay.fetch(new Request('https://test.workers.dev/api/v1/models',{headers:{Authorization:'Bearer '+key}})));
 await new Promise(resolve=>setTimeout(resolve,20));
 assert.equal(relay.pending.size,72);
 const health=await (await relay.fetch(new Request('https://test.workers.dev/health'))).json();
 assert.equal(health.max_concurrent_requests,64);assert.equal(health.shared_provider_capacity,true);
 for(const item of relay.pending.values()){clearTimeout(item.timer);item.resolve(Response.json({ok:true}));}
 relay.pending.clear();
 assert.ok((await Promise.all([...work,...controls])).every(response=>response.status===200));
});

test('offline and device credentials',async()=>{
 const r=new DeviceRelay({}, {DEVICE_KEY:device});
 assert.equal((await r.fetch(req('/agent/poll',{},'invalid'))).status,401);
 assert.equal((await r.fetch(new Request('https://x/api/v1/models',{headers:{Authorization:'Bearer client'}}))).status,503);
});
test('external POST reaches poll once and response is returned without storage',async()=>{
 const r=new DeviceRelay({storage:{put(){throw Error('payload storage forbidden')}}},{DEVICE_KEY:device});
 const key='client-key';r.keys=new Set([await digest(key)]);r.lastSeen=Date.now();
 const external=r.fetch(req('/api/v1/chat/completions',{messages:[{role:'user',content:'synthetic'}]},key));
 await new Promise(resolve=>setTimeout(resolve,10));
 const poll=await r.fetch(req('/agent/poll',{key_digests:[await digest(key)]}));
 const item=(await poll.json()).request;
 assert.equal(item.path,'/api/v1/chat/completions');
 assert.equal(JSON.parse(item.body).messages[0].content,'synthetic');
 await r.fetch(req('/agent/result',{id:item.id,status:200,body:'{"ok":true}',headers:{
   'X-Bridge-Cost-Source':'openrouter-list-price-estimate','X-Bridge-Pricing-Model':'openai/gpt-6.1-sol','X-Bridge-Pricing-Fetched-At':'1792600000','Set-Cookie':'must-not-forward'}}));
 const result=await external;assert.equal(result.status,200);assert.equal(r.pending.size,0);
 assert.equal(result.headers.get('X-Bridge-Cost-Source'),'openrouter-list-price-estimate');
 assert.equal(result.headers.get('X-Bridge-Pricing-Model'),'openai/gpt-6.1-sol');
 assert.equal(result.headers.get('X-Bridge-Pricing-Fetched-At'),'1792600000');
 assert.equal(result.headers.get('Set-Cookie'),null);
});
test('unknown keys are rejected before dispatch',async()=>{
 const r=new DeviceRelay({}, {DEVICE_KEY:device});r.lastSeen=Date.now();
 assert.equal((await r.fetch(req('/api/v1/chat/completions',{},'invalid'))).status,401);
 assert.equal(r.pending.size,0);
});

test('preflight and request deadline reach the device without inference or storage',async()=>{
 const r=new DeviceRelay({storage:{put(){throw Error('payload storage forbidden')}}},{DEVICE_KEY:device});
 const key='routing-client';r.keys=new Set([await digest(key)]);r.lastSeen=Date.now();
 const request=req('/bridge/v1/preflight',{model:'synthetic'},key);
 const requestId=crypto.randomUUID(),deadline=Date.now()+15_000;
 request.headers.set('X-AIEA-Request-Id',requestId);
 request.headers.set('X-Bridge-Deadline',String(deadline));
 const external=r.fetch(request);
 await new Promise(resolve=>setTimeout(resolve,10));
 const poll=await r.fetch(req('/agent/poll',{key_digests:[await digest(key)]}));
 const item=(await poll.json()).request;
 assert.equal(item.path,'/bridge/v1/preflight');assert.equal(item.request_id,requestId);assert.equal(item.deadline,deadline);
 await r.fetch(req('/agent/result',{id:item.id,status:200,body:'{"ready":true}'}));
 assert.equal((await (await external).json()).ready,true);assert.equal(r.pending.size,0);
});

test('restart releases a stale dispatched request without replay or payload storage',async()=>{
 const r=new DeviceRelay({storage:{put(){throw Error('payload storage forbidden')}}},{DEVICE_KEY:device});
 const key='restart-client';const keys=[await digest(key)];
 const poll1=r.fetch(req('/agent/poll',{key_digests:keys,agent_session:'a'.repeat(32)}));
 await new Promise(resolve=>setTimeout(resolve,10));
 const external=r.fetch(req('/api/v1/chat/completions',{messages:[{role:'user',content:'synthetic restart'}]},key));
 const dispatched=(await (await poll1).json()).request;
 assert.ok(dispatched);assert.equal(r.pending.size,1);
 const poll2=r.fetch(req('/agent/poll',{key_digests:keys,agent_session:'b'.repeat(32)}));
 const interrupted=await external;assert.equal(interrupted.status,503);
 assert.equal((await interrupted.json()).error.metadata.error_type,'device_restarted');
 assert.equal(r.pending.size,0);
 assert.equal((await (await r.fetch(req('/agent/result',{id:dispatched.id,status:200,body:'{}'}))).json()).accepted,false);
 r.waiter(null);assert.equal((await (await poll2).json()).request,null);
});

test('a new process retires the old empty poll before receiving new work',async()=>{
 const r=new DeviceRelay({}, {DEVICE_KEY:device});const key='restart-key';const keys=[await digest(key)];
 const old=r.fetch(req('/agent/poll',{key_digests:keys,agent_session:'a'.repeat(32)}));
 await new Promise(resolve=>setTimeout(resolve,10));
 const fresh=r.fetch(req('/agent/poll',{key_digests:keys,agent_session:'b'.repeat(32)}));
 assert.equal((await (await old).json()).request,null);
 const external=r.fetch(req('/api/v1/chat/completions',{},key));
 const item=(await (await fresh).json()).request;assert.ok(item);
 await r.fetch(req('/agent/result',{id:item.id,status:200,body:'{}'}));
 assert.equal((await external).status,200);
});

for(const [method,path,body] of [
 ['GET','/bridge/v1/model-capabilities',null],
 ['POST','/bridge/v1/models/refresh',{}],
 ['POST','/bridge/v1/models/probe',{model:'synthetic',protocol:'decisions'}],
 ['POST','/api/alpha/decisions',{model:'synthetic',state:{text:'合成'},questions:{q:{type:'noul',instructions:'Synthetic?'}},provider:{data_collection:'deny'}}]
]) test(`new ${method} ${path} forwards unchanged once without storage`,async()=>{
 const r=new DeviceRelay({storage:{put(){throw Error('storage forbidden')}}},{DEVICE_KEY:device});
 const key='synthetic-new-client',keys=[await digest(key)];r.keys=new Set(keys);r.lastSeen=Date.now();
 const request=new Request('https://test.workers.dev'+path,{method,headers:{Authorization:'Bearer '+key},...(body?{body:JSON.stringify(body)}:{})});
 const external=r.fetch(request);
 await new Promise(resolve=>setTimeout(resolve,10));
 const item=(await (await r.fetch(req('/agent/poll',{key_digests:keys}))).json()).request;
 assert.equal(item.path,path);assert.equal(item.method,method);
 assert.deepEqual(item.body,body?JSON.stringify(body):'');
 const response=JSON.stringify({answers:{q:{type:'noul',noul:.9}},usage:{input_tokens:1,output_tokens:1,cost:.01}});
 await r.fetch(req('/agent/result',{id:item.id,status:200,body:response}));
 assert.equal(await (await external).text(),response);assert.equal(r.pending.size,0);
 assert.equal((await r.fetch(new Request('https://x'+path,{method:method==='GET'?'POST':'GET',headers:{Authorization:'Bearer '+key}}))).status,404);
});
