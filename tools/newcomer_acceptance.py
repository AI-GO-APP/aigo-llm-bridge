"""Windows repo -> isolated install -> BYO -> independent HTTPS consumer.

Uses the owner's sole logged-in Cloudflare account only when this live test is
authorized. Never modifies the existing install or provider login. No saved I/O.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
import argparse

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import byo_clean_acceptance as privacy

RESULT={'method':'Windows source installer and independent HTTPS consumer subprocess','complete':False,
        'computer_use_used':False,'macos':'pending_real_machine_validation','cases':[]}
OPENER=urllib.request.build_opener(urllib.request.ProxyHandler({}))


def check(name,ok,**data):
    row={'case':name,'success':bool(ok),**data};RESULT['cases'].append(row);print(json.dumps(row),flush=True)
    if not ok:raise RuntimeError(name)


def command(args,*,input=None,timeout=400):
    process=subprocess.run(list(map(str,args)),input=input,capture_output=True,timeout=timeout,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if process.returncode:raise RuntimeError('Command failed; raw diagnostics withheld')
    return process.stdout.decode('utf-8-sig')


def metadata(data):
    with sqlite3.connect((Path(data)/'bridge.sqlite').as_uri()+'?mode=ro',uri=True) as db:
        settings=dict(db.execute('select name,value from settings'))
        return {k:settings.get(k) for k in ('device_id','public_url','cloudflare_account_id','cloudflare_worker_name')}|{
            'keys':db.execute('select id,digest,revoked_ts from api_keys order by id').fetchall()}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--work-root',type=Path);args=parser.parse_args()
    work=args.work_root.resolve() if args.work_root else ROOT/'.desktop-build'/('newcomer-'+uuid.uuid4().hex[:10])
    if not work.is_relative_to(ROOT/'.desktop-build') or not work.name.startswith('newcomer-'):raise ValueError('Only isolated newcomer test profiles are accepted')
    work.mkdir(exist_ok=True)
    evidence=ROOT/'docs/byo-evidence/newcomer-windows-0.5.0.json'
    root=work/'installed device';data=work/'device profile'
    shell=privacy.current_shell();before_cli=privacy.cli_snapshot()
    original_manifest=Path(os.environ['LOCALAPPDATA'])/'AIGO LLM Bridge/install.json'
    manifest_before=original_manifest.read_bytes() if original_manifest.exists() else None
    process=None;installed=None;key_id=None;key=None
    marker='NEWCOMER_CHECK_'+uuid.uuid4().hex
    def setup(action,*args):
        return json.loads(command([installed['python'],Path(installed['app'])/'tools/byo_setup.py',action,'--data-dir',data,*args]).splitlines()[-1])
    def http(path,token=None):
        req=urllib.request.Request(path,headers={'User-Agent':'llm-bridge-newcomer/1.0',**({'Authorization':'Bearer '+token} if token else {})})
        try:response=OPENER.open(req,timeout=8)
        except urllib.error.HTTPError as error:response=error
        with response:return response.status,json.loads(response.read())
    def launch():
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        p=subprocess.Popen([installed['python'],installed['launcher'],'--headless','--port',str(port)],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        deadline=time.monotonic()+25
        while time.monotonic()<deadline:
            try:
                if http(f'http://127.0.0.1:{port}/health')[1].get('version')==installed['version']:return p
            except OSError:pass
            if p.poll() is not None:break
            time.sleep(.3)
        stop(p);raise RuntimeError('Installed source runtime did not start')
    def stop(p):
        if p and p.poll() is None:p.terminate();p.wait(timeout=20)
    def ready(url):
        deadline=time.monotonic()+75
        attempts=[]
        while time.monotonic()<deadline:
            try:
                code,body=http(url+'/api/v1/models',key)
                attempts.append({'status':code,'error_type':body.get('error',{}).get('metadata',{}).get('error_type')})
                if code==200:
                    RESULT.setdefault('readiness',[]).append(attempts);return
            except OSError as e:attempts.append({'error_class':type(e).__name__,'reason_class':type(getattr(e,'reason',None)).__name__})
            time.sleep(1)
        RESULT.setdefault('readiness',[]).append(attempts)
        raise RuntimeError('Public key/model readiness failed')
    def consume(created,phase):
        result=json.loads(command([sys.executable,ROOT/'tools/consumer_probe.py'],input=json.dumps(created).encode(),timeout=120))
        check(phase,result.get('synthetic_reply_matches') is True,**result)
    try:
        installed=json.loads(command([sys.executable,ROOT/'tools/install.py','--install-root',root,'--data-dir',data]))
        # Python on a fresh Windows profile may lack a populated system CA store.
        # Use the installed public CA bundle, never disable certificate verification.
        cafile=command([installed['python'],'-c','import certifi; print(certifi.where())']).strip()
        os.environ['SSL_CERT_FILE']=cafile
        global OPENER
        OPENER=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=cafile)))
        initial=setup('status')
        check('existing_isolated_profile_reused' if args.work_root else 'clean_repo_install_has_no_default_endpoint_or_keys',bool(initial['public_url']) if args.work_root else not initial['public_url'] and not initial['active_api_keys'],version=installed['version'])
        doctor=setup('doctor');check('prerequisites_and_codex_subscription_ready',doctor['node_22_or_newer'] and doctor['wrangler_installed'] and doctor['subscriptions']['codex'])
        wrangler=Path(os.environ['APPDATA'])/'npm/node_modules/wrangler/bin/wrangler.js'
        who=json.loads(command([shutil.which('node'),wrangler,'whoami','--json']))
        accounts=who.get('accounts',[])
        if len(accounts)!=1:raise RuntimeError('Live acceptance requires a single explicitly selected owner account')
        setup('plan','--account-id',accounts[0]['id']);setup('deploy');deployed=setup('status');url=deployed['public_url']
        RESULT['url']=url;RESULT['installation_root']=str(root)
        check('new_owner_worker_paired',deployed['device_paired'] and deployed['device_id']!=initial.get('unknown','') and url.startswith('https://'+deployed['worker_name']+'.'))
        created=setup('key-create','--label','Newcomer acceptance only','--providers','codex','--handoff')
        key_id=created['id'];key=created['key'];info=created['integration']
        check('one_time_message_has_own_endpoint_key_and_codex',key in info['prompt'] and info['contains_key'] and info['config']['base_url']==url+'/api/v1' and info['request']['model'].startswith('openai/'))
        # Same generated contract, with a unique synthetic marker so the agent's
        # own historical documentation containing PONG cannot cause false hits.
        created['_expected']=marker
        info['request']['messages'][0]['content']='Return only this exact token: '+marker
        plain=setup('handoff','--providers','codex')
        check('later_message_cannot_read_key',key not in json.dumps(plain) and not plain['contains_key'])
        identity=metadata(data);process=launch();ready(url)
        consume(created,'independent_consumer_real_https')
        stop(process);process=None
        reinstalled=json.loads(command([sys.executable,ROOT/'tools/install.py','--install-root',root]))
        check('source_update_reuses_profile',reinstalled['data_dir']==installed['data_dir'] and reinstalled['app']!=installed['app'] and metadata(data)==identity)
        installed=reinstalled;setup('deploy');process=launch();ready(url)
        check('update_redeploy_restart_preserves_url_and_same_key',metadata(data)==identity and setup('status')['public_url']==url)
        consume(created,'same_consumer_after_update_and_redeploy')
        setup('key-revoke','--key-id',key_id)
        check('revoked_consumer_key_is_401',http(url+'/api/v1/models',key)[0]==401)
        key_id=None
        # DB/log metadata, DPAPI bytes, and pricing snapshots contain no synthetic content or API key.
        hits=[];files=0
        for file in data.rglob('*'):
            if file.is_file():
                files+=1;raw=file.read_bytes()
                if key.encode() in raw or marker.encode() in raw:hits.append(file.name)
        check('profile_contains_neither_plain_key_nor_request',not hits,files_scanned=files)
        privacy.RESULT={'cases':[]}
        privacy.cli_privacy(before_cli,marker)
        RESULT['cli_privacy']=privacy.RESULT['cases']
        after=privacy.current_shell()
        check('existing_startup_shortcuts_and_claude_untouched',shell[:2]==after[:2] and shell[2].issubset(after[2]),claude_processes_preserved=len(shell[2]))
        check('production_windows_install_manifest_unchanged',manifest_before==original_manifest.read_bytes() if manifest_before else not original_manifest.exists())
        RESULT['complete']=True
    except Exception as error:
        RESULT['failure_type']=type(error).__name__
        if isinstance(error,RuntimeError):RESULT['failure_gate']=str(error)
    finally:
        if key_id:
            try:setup('key-revoke','--key-id',key_id)
            except Exception:pass
        if installed:
            try:
                for item in setup('key-list')['keys']:
                    if item['label']=='Newcomer acceptance only' and not item['revoked_ts']:
                        setup('key-revoke','--key-id',item['id'])
            except Exception:pass
        stop(process);evidence.parent.mkdir(exist_ok=True)
        evidence.write_text(json.dumps(RESULT,indent=2),encoding='utf-8')
        print(json.dumps({'complete':RESULT['complete'],'evidence':str(evidence)}),flush=True)
    return 0 if RESULT['complete'] else 1


if __name__=='__main__':raise SystemExit(main())
