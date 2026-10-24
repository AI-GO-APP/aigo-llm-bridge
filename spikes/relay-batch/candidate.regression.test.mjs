// Replay the unchanged production Worker regression suite against the candidate.
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';

const original="import worker,{DeviceRelay} from '../src/worker.js';";
let source=await readFile(new URL('../../cloudflare/test/relay.test.js',import.meta.url),'utf8');
assert.equal(source.split(original).length,2);
source=source.replace(original,`import worker from ${JSON.stringify(new URL('../../cloudflare/src/worker.js',import.meta.url).href)};
import {candidateClass} from ${JSON.stringify(new URL('./candidate.mjs',import.meta.url).href)};
const DeviceRelay=await candidateClass();`);
await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
