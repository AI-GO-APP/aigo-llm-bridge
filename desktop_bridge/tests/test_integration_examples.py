"""Run generated client examples against the actual loopback HTTP contract."""
import base64
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import urllib.request

import pytest

from desktop_bridge.handoff import integration
from desktop_bridge.service import Runtime, ApiServer
from desktop_bridge.store import Store

ROOT=Path(__file__).resolve().parents[2]
OPERATIONS=('models','capabilities','refresh','decisions','probe','chat')


@pytest.mark.parametrize('operation',OPERATIONS)
@pytest.mark.parametrize('language',('python','powershell','curl'))
def test_generated_client_roundtrips_without_changing_the_body(tmp_path,monkeypatch,operation,language):
    node=shutil.which('node')
    if not node:pytest.skip('Node required for generated examples')
    powershell=shutil.which('powershell.exe')
    if language=='powershell' and not powershell:pytest.skip('Windows PowerShell example')
    s=Store(tmp_path);kid,key=s.create_key('example',['codex']);alias="synthetic'alias"
    s.set('models',[{'id':alias,'provider':'codex','native':'gpt-6-astra'}])
    seen=[]
    def runner(spec,*_):
        seen.append(spec)
        return ('{"noul":0.9}' if spec.schema else 'PONG'),{'prompt_tokens':1,'completion_tokens':1},'stop'
    rt=Runtime(s,runner);api=ApiServer(rt,0);api.start()
    base=f'http://127.0.0.1:{api.port}/api/v1'
    generate='const e=require("./desktop_bridge/web/integration.js");process.stdout.write(e.build(...JSON.parse(process.argv[1])));'
    code=subprocess.check_output([node,'-e',generate,json.dumps([base,alias,language,operation])],cwd=ROOT).decode('utf-8')
    monkeypatch.setenv('LLM_BRIDGE_KEY',key)
    try:
        if language=='python':
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            monkeypatch.setattr(urllib.request,'urlopen',lambda req,timeout,context:opener.open(req,timeout=timeout))
            exec(compile(code,'<generated-client>','exec'),{})
        elif language=='powershell':
            # The key stays in the child environment rather than command arguments.
            encoded=base64.b64encode(code.encode('utf-16-le')).decode('ascii')
            proc=subprocess.run([powershell,'-NoProfile','-NonInteractive','-EncodedCommand',encoded],
                                env=dict(os.environ),capture_output=True,timeout=15)
            assert proc.returncode==0
        else:
            # Parse Bash quoting, then use the resulting URL/body through HTTP without
            # placing even a synthetic key in curl's process arguments.
            args=shlex.split(code[code.index('curl --'):].replace('\\\n',' '))
            url=next(arg for arg in args if arg.startswith('http://'))
            data=args[args.index('--data-raw')+1].encode() if '--data-raw' in args else None
            req=urllib.request.Request(url,data=data,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(req,timeout=5) as response:assert response.status==200
        assert len(seen)==(1 if operation in ('chat','decisions','probe') else 0)
        if seen:assert seen[0].model['id']==alias
    finally:s.revoke(kid);rt.stop();api.stop();s.close()


def test_handoff_uses_device_urls_preserves_original_jev_shape_and_never_reveals_an_old_key(tmp_path):
    s=Store(tmp_path);s.set('public_url','https://synthetic-owner.example')
    try:
        info=integration(s,providers=['codex'])
        assert info['decisions']['url']=='https://synthetic-owner.example/api/alpha/decisions'
        assert set(info['decisions']['request'])=={'model','state','questions','provider'}
        assert info['decisions']['response_path']=='answers' and not info['contains_key']
        assert info['model_capabilities_url']=='https://synthetic-owner.example/bridge/v1/model-capabilities'
        assert not s.keys()
    finally:s.close()
