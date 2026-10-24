import {test} from 'node:test';
import assert from 'node:assert/strict';
import {setTimeout as delay} from 'node:timers/promises';
import {DeviceRelay as Baseline} from '../../cloudflare/src/worker.js';
import {candidateClass,decode,BYTE_LIMIT} from './candidate.mjs';

const Candidate=await candidateClass();
const device='synthetic-only-device',key='synthetic-only-client';
const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(key)))].map(x=>x.toString(16).padStart(2,'0')).join('');
const post=(path,body,token=device)=>new Request('https://synthetic.invalid'+path,{method:'POST',headers:{Authorization:'Bearer '+token},body:JSON.stringify(body)});
function make(Class=Candidate){const r=new Class({storage:{put(){throw Error('No storage');}}},{DEVICE_KEY:device});r.keys.add(digest);r.lastSeen=Date.now();return r;}
async function fill(r,n,body={synthetic:true}){const external=Array.from({length:n},()=>r.fetch(post('/api/v1/chat/completions',body,key)));const until=Date.now()+3000;while(r.pending.size<n){assert.ok(Date.now()<until);await delay(1);}return external;}
async function poll(r,batch=8,session='a'.repeat(32)){return r.fetch(post('/agent/poll',{key_digests:[digest],agent_session:session,...(batch===null?{}:{batch_size:batch})}));}
async function finish(r,external){if(r.waiter)r.waiter(null);for(const p of r.pending.values()){clearTimeout(p.timer);p.resolve(new Response('{}'));p.work=null;}r.pending.clear();await Promise.all(external);}

test('eight queued works preserve FIFO and dispatch exactly once',async()=>{
 const r=make();const external=await fill(r,16);const ids=[...r.pending.keys()];
 try{const a=decode(await(await poll(r)).json());const b=decode(await(await poll(r)).json());assert.deepEqual([...a,...b].map(x=>x.id),ids);assert.equal(new Set([...a,...b].map(x=>x.id)).size,16);}finally{await finish(r,external);}
});
test('old agent/new Worker and new agent/old Worker both use single-work compatibility',async()=>{
 for(const Class of [Candidate,Baseline]){const r=make(Class);const external=await fill(r,2);
  try{const value=await(await poll(r,Class===Candidate?null:8)).json();assert.ok(value.request);assert.equal(decode(value).length,1);}finally{await finish(r,external);}}
});
test('empty long poll wakes once and retains remaining works for the next batch',async()=>{
 const r=make();const waiting=poll(r);await delay(10);const external=await fill(r,3);
 try{const one=decode(await(await waiting).json());assert.equal(one.length,1);const next=decode(await(await poll(r)).json());assert.equal(next.length,2);assert.equal(new Set([...one,...next].map(x=>x.id)).size,3);}finally{await finish(r,external);}
});
test('batch size rejects bool, fractions, zero and over-limit without dispatch',async()=>{
 const r=make();const external=await fill(r,1);
 try{for(const n of [true,1.5,0,9,'8'])assert.equal((await poll(r,n)).status,400);assert.ok([...r.pending.values()].every(x=>!x.dispatched));}finally{await finish(r,external);}
});
test('encoded byte cap leaves large remainder undispatched',async()=>{
 const r=make();const external=await fill(r,2,{synthetic:'\\'.repeat(900000)});
 try{const response=await poll(r);const raw=await response.text();assert.ok(Buffer.byteLength(raw)<=BYTE_LIMIT);assert.equal(decode(JSON.parse(raw)).length,1);assert.equal([...r.pending.values()].filter(x=>x.dispatched).length,1);assert.equal(decode(await(await poll(r)).json()).length,1);}finally{await finish(r,external);}
});
test('new session retires every dispatched batch item without replay',async()=>{
 const r=make();const external=await fill(r,8);const works=decode(await(await poll(r)).json());
 const fresh=poll(r,8,'b'.repeat(32));
 try{const results=await Promise.all(external);assert.ok(results.every(x=>x.status===503));assert.equal(r.pending.size,0);for(const work of works)assert.equal((await(await r.fetch(post('/agent/result',{id:work.id,status:200,body:'{}'}))).json()).accepted,false);r.waiter(null);assert.deepEqual(decode(await(await fresh).json()),[]);}finally{await finish(r,external);}
});
test('decoder rejects malformed/duplicate batches before any forwarding',()=>{
 for(const value of [{requests:{}},{requests:Array.from({length:9},(_,i)=>({id:String(i)}))},{requests:[{id:'x'},{id:'x'}]},{requests:[null]}])assert.throws(()=>decode(value));
 assert.deepEqual(decode({request:null}),[]);assert.deepEqual(decode({requests:[]}),[]);
});
