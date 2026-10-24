// Research only. Production Worker and Relay are never modified by this module.
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';

export const BYTE_LIMIT = 6_100_000;
export const BATCH_LIMIT = 8;

export async function candidateClass() {
  let source = await readFile(new URL('../../cloudflare/src/worker.js', import.meta.url), 'utf8');
  // Once integrated, replay the same research invariants against production.
  if(source.includes('const BATCH_LIMIT=8, BATCH_BYTES=6_100_000;'))
    return (await import('../../cloudflare/src/worker.js')).DeviceRelay;
  const changes = [
    ['if(path==="/agent/poll") {', `if(path==="/agent/poll") {
          const batch=Object.hasOwn(data,'batch_size');
          if(batch&&(!Number.isInteger(data.batch_size)||data.batch_size<1||data.batch_size>8))
            return error(400,"invalid_request","Invalid batch size.");`],
    ['const next=[...this.pending.values()].find(p=>!p.dispatched);\n          if(next){next.dispatched=true;return Response.json({request:next.work});}', `const selected=[];
          const limit=batch?data.batch_size:1;
          let bytes=new TextEncoder().encode(batch?'{"requests":[]}':'{"request":null}').byteLength;
          for(const item of this.pending.values()){
            if(item.dispatched)continue;
            const size=new TextEncoder().encode(JSON.stringify(item.work)).byteLength;
            if(selected.length&&(bytes+size+1>6_100_000))break;
            if(bytes+size+1>6_100_000)return error(502,"response_too_large","Relay envelope too large.");
            selected.push(item);bytes+=size+1;
            if(selected.length>=limit)break;
          }
          if(selected.length){
            const works=selected.map(item=>item.work);
            const response=Response.json(batch?{requests:works}:{request:works[0]});
            for(const item of selected)item.dispatched=true;
            return response;
          }`],
    ['return Response.json({request:work});', 'return Response.json(batch?{requests:work?[work]:[]}:{request:work});'],
  ];
  for (const [before, after] of changes) {
    assert.equal(source.split(before).length, 2, 'Production source changed; re-review this candidate.');
    source = source.replace(before, after);
  }
  return (await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'))).DeviceRelay;
}

// Proposed new Relay decoder; old single-work responses remain compatible.
export function decode(value) {
  const works = Object.hasOwn(value,'requests') ? value.requests : value.request ? [value.request] : [];
  if (!Array.isArray(works) || works.length > BATCH_LIMIT) throw Error('Invalid batch.');
  const ids = new Set();
  for (const work of works) {
    if (!work || typeof work !== 'object' || typeof work.id !== 'string' || !work.id || ids.has(work.id))
      throw Error('Invalid or duplicate work.');
    ids.add(work.id);
  }
  return works;
}
