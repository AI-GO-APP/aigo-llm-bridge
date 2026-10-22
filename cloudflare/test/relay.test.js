import {test} from 'node:test';
import assert from 'node:assert/strict';
import worker,{DeviceRelay} from '../src/worker.js';
const device='x'.repeat(48);
const digest=async s=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s)))].map(v=>v.toString(16).padStart(2,'0')).join('');
const req=(path,body,token=device)=>new Request('https://test.workers.dev'+path,{method:'POST',headers:{Authorization:'Bearer '+token},body:JSON.stringify(body)});

test('outer build header preserves the original actor identity and response',async()=>{
 let actor;
 const env={DEVICE_KEY:device,DEVICE:{idFromName(name){actor=name;return 'existing-id';},get(id){
   assert.equal(id,'existing-id');return {fetch:async()=>Response.json({version:'legacy'},{headers:{'Cache-Control':'no-store'}})};
 }}};
 const res=await worker.fetch(new Request('https://test.workers.dev/health'),env);
 assert.equal(actor,'primary-device');
 assert.equal(res.headers.get('X-Bridge-Relay-Version'),'0.3.4-relay');
 assert.equal(res.headers.get('Cache-Control'),'no-store');
 assert.equal((await res.json()).version,'legacy');
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
