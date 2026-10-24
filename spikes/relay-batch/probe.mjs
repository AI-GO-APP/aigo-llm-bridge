// Synthetic transport-only experiment. No provider, device secret, owner key or deployment.
import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';
import {setTimeout as delay} from 'node:timers/promises';
import {DeviceRelay as Baseline} from './baseline-worker.mjs';
import {candidateClass, decode} from './candidate.mjs';

const device = 'synthetic-device-not-a-real-secret';
const key = 'synthetic-client-not-a-real-key';
const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(key)))].map(x=>x.toString(16).padStart(2,'0')).join('');
const Candidate = await candidateClass();
const post = (path,body,token=device)=>new Request('https://synthetic.invalid'+path,
  {method:'POST',headers:{Authorization:'Bearer '+token},body:JSON.stringify(body)});
const percentile=(values,p)=>Math.round([...values].sort((a,b)=>a-b)[Math.ceil(values.length*p)-1]*1000)/1000;
const report={experiment:'buffered burst transport; actual Worker state machine, imposed RTT',
  production_changed:false,real_network:false,model_inference_calls:0,raw_content_saved:false,rows:[]};

async function run(Class,batch,count,rtt,round){
  const relay=new Class({storage:{put(){throw Error('Payload storage forbidden.');}}},{DEVICE_KEY:device});
  relay.keys.add(digest);relay.lastSeen=Date.now();
  const external=Array.from({length:count},(_,i)=>relay.fetch(post(i%2?'/api/alpha/decisions':'/api/v1/chat/completions',{synthetic:true},key)));
  const deadline=Date.now()+2000;
  while(relay.pending.size!==count){assert.ok(Date.now()<deadline);await delay(1);}
  const times=[];const ids=new Set();let polls=0;let maximum=0;
  const began=performance.now();
  try{
    while(times.length<count){
      await delay(rtt/2);
      const response=await relay.fetch(post('/agent/poll',{key_digests:[digest],agent_session:'a'.repeat(32),...(batch?{batch_size:8}:{})}));
      assert.equal(response.status,200);
      const value=await response.json();
      await delay(rtt/2);
      const works=decode(value);assert.ok(works.length);
      polls++;maximum=Math.max(maximum,works.length);
      for(const work of works){
        assert.ok(!ids.has(work.id));ids.add(work.id);times.push(performance.now()-began);
        await relay.fetch(post('/agent/result',{id:work.id,status:200,body:'{"synthetic":true}'}));
      }
    }
    assert.ok((await Promise.all(external)).every(x=>x.status===200));assert.equal(relay.pending.size,0);
    return {arm:batch?'batch8':'single',count,rtt_ms:rtt,round,polls,maximum_batch:maximum,
      delivered_once:ids.size,dispatch_p50_ms:percentile(times,.5),dispatch_p95_ms:percentile(times,.95),
      dispatch_max_ms:percentile(times,1)};
  }finally{
    if(relay.waiter)relay.waiter(null);
    for(const item of relay.pending.values()){clearTimeout(item.timer);item.resolve(new Response('{}'));item.work=null;}
    relay.pending.clear();await Promise.all(external);
  }
}

for(const [count,rtt,rounds] of [[16,100,3],[64,100,3],[64,500,1]]){
  for(let round=1;round<=rounds;round++){
    for(const batch of (round%2?[false,true]:[true,false])){
      const row=await run(batch?Candidate:Baseline,batch,count,rtt,round);
      report.rows.push(row);console.log(JSON.stringify(row));
    }
  }
}
report.success=true;
if(process.argv[2])await writeFile(process.argv[2],JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({success:true,model_inference_calls:0,real_network:false,production_changed:false}));
