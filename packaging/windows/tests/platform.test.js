const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname,'../../..');

test('browser frontend retains clipboard and CSV download without native dependencies',async()=>{
  let copied, clicked=false;
  const context={window:{},navigator:{clipboard:{writeText:async text=>{copied=text;}}},
    URL:{createObjectURL:()=> 'blob:synthetic',revokeObjectURL:()=>{}},
    document:{createElement:()=>({click(){clicked=this.download==='bridge-request-metadata.csv';}})},setTimeout:()=>{}};
  vm.runInNewContext(fs.readFileSync(path.join(root,'desktop_bridge/web/platform.js'),'utf8'),context);
  await context.window.BridgePlatform.copyText('synthetic-key');
  assert.equal(copied,'synthetic-key');
  assert.equal(await context.window.BridgePlatform.exportLogs('',async()=>({})),true);
  assert.equal(clicked,true);assert.equal(context.window.BridgePlatform.native,false);
});

test('Windows adapter uses explicit native operations and handles cancelled export',async()=>{
  let ready,copied,filter;
  const context={window:{addEventListener:(name,callback)=>{ready=callback;},pywebview:{api:{
    copy_text:async text=>{copied=text;return {ok:true};},
    export_logs:async query=>{filter=query;return {saved:false};},open_browser:async()=>({opened:true})}}},
    document:{createElement:()=>({addEventListener(){}}),querySelector:()=>({prepend(){}})}};
  vm.runInNewContext(fs.readFileSync(path.join(root,'packaging/windows/platform.js'),'utf8'),context);
  ready();assert.equal(context.window.BridgePlatform.native,true);
  await context.window.BridgePlatform.copyText('synthetic-key');assert.equal(copied,'synthetic-key');
  assert.equal(await context.window.BridgePlatform.exportLogs(new URLSearchParams({provider:'codex'}),()=>{throw Error('Browser loader must not run');}),false);
  assert.equal(filter,'provider=codex');
});
