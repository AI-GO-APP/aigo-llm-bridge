"""Exercise the actual BYO EXEs in an isolated profile, without UI automation."""
import hashlib
import json
import re
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import uuid
import zipfile

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from desktop_bridge.store import Store


def main():
    package=ROOT/'dist/AIGO-LLM-Bridge-BYO';app=package/'app'
    setup=app/'BYO-Setup/AIGO-Bridge-Setup.exe';exe=app/'AIGO-LLM-Bridge.exe'
    directory=ROOT/'.desktop-build'/('byo-package-'+uuid.uuid4().hex[:8]);directory.mkdir()
    data=directory/'data'
    def run(action,*args):
        proc=subprocess.run([str(setup),action,'--data-dir',str(data),*args],capture_output=True,timeout=30)
        if proc.returncode:raise RuntimeError('Packaged CLI failed')
        return [json.loads(line) for line in proc.stdout.decode('utf-8').splitlines() if line.startswith('{')][-1]
    first=run('status');plan=run('plan','--account-id','a'*32);second=run('status')
    config=json.loads((data/'byo-worker/wrangler.json').read_text())
    result={'native_setup_plan':True,'device_identity_stable':first['device_id']==plan['device_id']==second['device_id'],
            'no_default_publisher_endpoint':not first['public_url'] and not first['device_paired'],
            'per_device_worker_name':config['name'].endswith(first['device_id'][:20]),
            'template_matches':(data/'byo-worker/src/worker.js').read_bytes()==(ROOT/'cloudflare/src/worker.js').read_bytes(),
            'guidance_and_skill_included':all((app/p).is_file() for p in ['AGENTS.md','CLAUDE.md','skills/byo-cloudflare/SKILL.md','docs/AI-AGENT-SETUP.md','docs/DEVICE-IDENTITY.md'])}
    broken=[]
    for document in package.rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',document.read_text(encoding='utf-8-sig')):
            if ':' not in target and not target.startswith('#') and not (document.parent/target.split('#')[0]).is_file():
                broken.append(str(document.relative_to(package))+':'+target)
    result['packaged_document_links_resolve']=not broken
    store=Store(data,startup=False);kid,key=store.create_key('Package smoke only');store.close()
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
    process=subprocess.Popen([str(exe),'--headless','--port',str(port),'--data-dir',str(data)],startupinfo=startup)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        deadline=time.monotonic()+20
        while True:
            try:
                with opener.open(f'http://127.0.0.1:{port}/health',timeout=2) as response:health=json.loads(response.read())
                break
            except OSError:
                if time.monotonic()>deadline:raise RuntimeError('Packaged API did not start')
                time.sleep(.25)
        req=urllib.request.Request(f'http://127.0.0.1:{port}/api/v1/models',headers={'Authorization':'Bearer '+key})
        with opener.open(req,timeout=30) as response:models=json.loads(response.read())
        capabilities=urllib.request.Request(f'http://127.0.0.1:{port}/bridge/v1/model-capabilities',headers={'Authorization':'Bearer '+key})
        with opener.open(capabilities,timeout=30) as response:caps=json.loads(response.read())
        result.update(packaged_api_version=health['version'],
                      packaged_api_auth=models.get('object')=='list' and isinstance(models.get('data'),list),
                      capability_query_is_non_inference=caps.get('inference_performed') is False,
                      decisions_guidance_included=(app/'docs/JEV-COMPATIBILITY.md').is_file())
    finally:
        if process.poll() is None:process.terminate();process.wait(timeout=10)
        store=Store(data,startup=False);store.revoke(kid);store.close()
    artifact=ROOT/'dist/AIGO-LLM-Bridge-BYO-Windows.zip'
    with zipfile.ZipFile(artifact) as archive:
        names=archive.namelist()
        result['no_installer_credentials_or_database_in_zip']=not any(n.endswith(('.sqlite','.dpapi')) or '/.wrangler/' in n or '/byo-worker/' in n for n in names)
    result['zip_sha256']=hashlib.sha256(artifact.read_bytes()).hexdigest()
    result['computer_use_used']=False
    (ROOT/'.desktop-build/byo-package-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
    return int(any(value is False for name,value in result.items() if name!='computer_use_used'))


if __name__=='__main__':raise SystemExit(main())
