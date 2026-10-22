"""Real ZIP/installer/Cloudflare acceptance. Product operations use packaged tools only.

No desktop automation, repo imports, provider login changes, or saved payloads/keys.
Requires explicit user authorization to create device Workers in their logged-in account.
"""
import argparse
import ctypes
from ctypes import wintypes
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import ssl
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request
import uuid
import winreg
import zipfile

ROOT=Path(__file__).resolve().parent.parent
OPENER=urllib.request.build_opener(urllib.request.ProxyHandler({}))
RESULT={'method':'actual extracted ZIP, PowerShell installer, native setup EXE, HTTPS', 'cases':[]}


def check(name,ok,**metadata):
    row={'case':name,'success':bool(ok),**metadata}
    RESULT['cases'].append(row);print(json.dumps(row),flush=True)
    if not ok:raise RuntimeError(name)


def ps(script,*args):
    result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass',*args,'-Command',script],
                          capture_output=True,timeout=45)
    if result.returncode:raise RuntimeError('PowerShell operation failed (diagnostics withheld)')
    return result.stdout.decode('utf-8-sig','replace').strip()


def current_shell():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
            startup=winreg.QueryValueEx(key,'AigoLlmBridge')[0]
    except FileNotFoundError:startup=''
    # Hash the personal shortcut files; never rewrite them during isolated acceptance.
    paths=json.loads(ps("@([Environment]::GetFolderPath('Desktop'),[Environment]::GetFolderPath('Programs')) | ConvertTo-Json -Compress"))
    shortcuts=[hashlib.sha256((Path(p)/'LLM Bridge.lnk').read_bytes()).hexdigest() if (Path(p)/'LLM Bridge.lnk').exists() else None for p in paths]
    raw=ps("@(Get-CimInstance Win32_Process -Filter \"Name='claude.exe'\" | Select-Object ProcessId,CreationDate) | ConvertTo-Json -Compress")
    processes=json.loads(raw or '[]')
    return startup,shortcuts,{(p['ProcessId'],p['CreationDate']) for p in processes}


def http(url,key=None,body=None,timeout=100):
    headers={'Content-Type':'application/json','User-Agent':'aigo-llm-bridge-acceptance/0.3.1'}
    if key:headers['Authorization']='Bearer '+key
    request=urllib.request.Request(url,headers=headers,data=json.dumps(body).encode() if body is not None else None)
    try:
        with OPENER.open(request,timeout=timeout) as response:return response.status,json.loads(response.read())
    except urllib.error.HTTPError as error:return error.code,json.loads(error.read())


def wait_models(url,key):
    started=time.monotonic();deadline=started+65;attempts=0;last_code=None
    while time.monotonic()<deadline:
        try:
            attempts+=1;code,body=http(url+'/api/v1/models',key,timeout=8);last_code=code
            if code==200:
                RESULT.setdefault('public_readiness',[]).append({'attempts':attempts,'elapsed_s':round(time.monotonic()-started,2)})
                return body
        except OSError:pass
        time.sleep(1)
    raise RuntimeError('Public models not ready; last HTTP status='+str(last_code))


def extracted(archive,destination):
    with zipfile.ZipFile(archive) as package:
        for name in package.namelist():
            if not (destination/name).resolve().is_relative_to(destination.resolve()):raise RuntimeError('Unsafe package path')
        package.extractall(destination)
    package=destination/'AIGO-LLM-Bridge-BYO'
    check('package_guidance_present',all((package/p).is_file() for p in ['USER-GUIDE.md','AGENT-SETUP.md','AGENTS.md',
          'app/docs/DEVICE-IDENTITY.md','app/skills/byo-cloudflare/SKILL.md']))
    return package


def install(package,root,shortcuts,**extra):
    command=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(package/'Install.ps1'),
             '-InstallRoot',str(root),'-ShortcutDirectory',str(shortcuts)]
    for name,value in extra.items():command.extend(['-'+name,str(value)])
    result=subprocess.run(command,capture_output=True,timeout=90)
    if result.returncode:raise RuntimeError('Packaged installer failed (diagnostics withheld)')
    manifest=json.loads((root/'install.json').read_text(encoding='utf-8-sig'))
    manifest['exe']=Path(manifest['exe']);manifest['data_dir']=Path(manifest['data_dir'])
    # Read the COM shortcut through CLI only; do not launch it or invoke a browser.
    path=str(shortcuts/'LLM Bridge.lnk').replace("'","''")
    shortcut=json.loads(ps("$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"+path+"'); @{target=$s.TargetPath; args=$s.Arguments}|ConvertTo-Json -Compress"))
    check('installed_shortcut_uses_same_profile',os.path.samefile(shortcut['target'],manifest['exe']) and
          shortcut['args']=='--data-dir "'+str(manifest['data_dir'])+'"',version=manifest['version'])
    return manifest


def cli(installation,action,*args):
    executable=installation['exe'].parent/'BYO-Setup/AIGO-Bridge-Setup.exe'
    result=subprocess.run([str(executable),action,'--data-dir',str(installation['data_dir']),*args],
                          cwd=executable.parent,capture_output=True,timeout=400)
    if result.returncode:raise RuntimeError('Packaged setup action failed: '+action+' (diagnostics withheld)')
    rows=[json.loads(line) for line in result.stdout.decode('utf-8').splitlines() if line.startswith('{')]
    return rows[-1]


def relay_fingerprint(data,*,raw=False):
    class Blob(ctypes.Structure):_fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_byte))]
    raw=(data/'relay-device.dpapi').read_bytes();buffer=ctypes.create_string_buffer(raw)
    source=Blob(len(raw),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_byte)));target=Blob()
    crypt=ctypes.WinDLL('crypt32');fn=crypt.CryptUnprotectData
    fn.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    if not fn(ctypes.byref(source),None,None,None,None,1,ctypes.byref(target)):raise RuntimeError('DPAPI verification failed')
    try:
        token=ctypes.string_at(target.data,target.size)
        return token if raw else hashlib.sha256(token).digest()
    finally:
        free=ctypes.WinDLL('kernel32').LocalFree;free.argtypes=[ctypes.c_void_p];free(target.data)


def metadata(data):
    with sqlite3.connect((data/'bridge.sqlite').as_uri()+'?mode=ro',uri=True) as database:
        settings={name:json.loads(value) for name,value in database.execute('select name,value from settings')}
        keys=database.execute('select id,digest,revoked_ts from api_keys order by id').fetchall()
    return (settings.get('device_id'),settings.get('public_url'),settings.get('cloudflare_worker_name'),
            settings.get('cloudflare_account_id'),keys,relay_fingerprint(data))


def launch(installation):
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
    process=subprocess.Popen([str(installation['exe']),'--headless','--data-dir',str(installation['data_dir']),'--port',str(port)],
                             cwd=installation['exe'].parent,startupinfo=startup)
    deadline=time.monotonic()+25
    while time.monotonic()<deadline:
        try:
            code,body=http(f'http://127.0.0.1:{port}/health')
            if code==200 and body.get('version')==installation['version']:
                process.bridge_port=port;return process
        except OSError:pass
        if process.poll() is not None:break
        time.sleep(.3)
    stop(process);raise RuntimeError('Installed application did not become healthy')


def stop(process):
    # Only handles returned by this harness, never process-name termination.
    if process and process.poll() is None:process.terminate();process.wait(timeout=20)


def stale_poll_acceptance(installation,url,key):
    """Simulate a dead local process after it consumed a work item, over real HTTPS."""
    token=relay_fingerprint(installation['data_dir'],raw=True).decode()
    session=uuid.uuid4().hex
    process=None
    with ThreadPoolExecutor(max_workers=3) as pool:
        poll=pool.submit(http,url+'/agent/poll',token,{'key_digests':[hashlib.sha256(key.encode()).hexdigest()],
                                                     'agent_session':session},30)
        waiting=None;deadline=time.monotonic()+20
        while not poll.done() and time.monotonic()<deadline:
            if waiting is None or waiting.done():waiting=pool.submit(http,url+'/api/v1/models',key,None,20)
            time.sleep(.05)
        status,work=poll.result(timeout=5)
        if status!=200 or not work.get('request') or waiting is None:raise RuntimeError('Failed to stage dead agent poll')
        try:
            started=time.monotonic();process=launch(installation)
            code,body=waiting.result(timeout=15)
            check('live_stale_poll_fails_without_replay',code==503 and body.get('error',{}).get('metadata',{}).get('error_type')=='device_restarted',
                  http_status=code,recovery_seconds=round(time.monotonic()-started,2))
            wait_models(url,key);return process
        except Exception:
            stop(process);raise


def privacy(data,forbidden):
    violations=0;files=0
    for path in data.rglob('*'):
        if path.is_file():
            files+=1;content=path.read_bytes()
            violations+=sum(value.encode() in content for value in forbidden)
    with sqlite3.connect((data/'bridge.sqlite').as_uri()+'?mode=ro',uri=True) as database:
        columns=[row[1] for row in database.execute('pragma table_info(requests)')]
        rows=database.execute('select count(*) from requests').fetchone()[0]
    check('profile_metadata_only',not violations and not {'prompt','messages','body','response','content'}&set(columns),
          scanned_files=files,request_rows=rows)


def cli_snapshot():
    result={}
    for directory in (Path.home()/'.claude',Path(os.environ.get('CODEX_HOME',Path.home()/'.codex'))):
        candidates=list(directory.glob('*'))
        for folder in ('projects','debug','sessions','session-env','logs','sqlite','archived_sessions'):
            candidates.extend((directory/folder).rglob('*'))
        for path in candidates:
            try:
                if path.is_file() and path.suffix in {'.json','.jsonl','.txt','.log','.db','.sqlite','.sqlite-wal','.sqlite-shm'}:
                    stat=path.stat();result[path]=(stat.st_mtime_ns,stat.st_size)
            except OSError:pass
    return result


def cli_privacy(before,marker):
    after=cli_snapshot();changed=[path for path,signature in after.items() if before.get(path)!=signature]
    hits=0;needle=marker.encode()
    for path in changed:
        try:
            with path.open('rb') as stream:
                carry=b''
                while part:=stream.read(1024*1024):
                    raw=carry+part
                    if needle in raw:hits+=1;break
                    carry=raw[-128:]
        except OSError:raise RuntimeError('CLI privacy scan could not read changed file') from None
    check('no_synthetic_prompt_in_changed_cli_files',hits==0,changed_files_scanned=len(changed),marker_hits=hits)


def main():
    global OPENER
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--candidate',type=Path,required=True)
    args=parser.parse_args()
    directory=ROOT/'.desktop-build'/('clean-byo-'+uuid.uuid4().hex[:10]);directory.mkdir()
    evidence=directory/'results.json';RESULT['acceptance_directory']=str(directory)
    baseline_shell=current_shell()
    try:before_current=http('http://127.0.0.1:8920/health',timeout=2)
    except OSError:before_current=None
    wrangler=Path(os.environ['APPDATA'])/'npm/node_modules/wrangler/bin/wrangler.js'
    who=subprocess.run([shutil.which('node'),str(wrangler),'whoami','--json'],capture_output=True,timeout=60)
    account_data=json.loads(who.stdout);accounts=account_data.get('accounts',[])
    if who.returncode or len(accounts)!=1:raise RuntimeError('Need one explicitly selected own Cloudflare account')
    account=accounts[0]['id'];process=None;created_keys=[];secrets=[];installation=None
    marker='BYO_PRIVATE_'+uuid.uuid4().hex
    before_cli=cli_snapshot()
    try:
        package=extracted(args.baseline,directory/'baseline-package')
        OPENER=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPSHandler(
            context=ssl.create_default_context(cafile=str(package/'app/_internal/certifi/cacert.pem'))))
        root=directory/'installed device';data=directory/'device data';shortcuts=directory/'shortcuts'
        check('clean_device_profile',not root.exists() and not data.exists())
        installation=install(package,root,shortcuts,DataDir=data)
        initial=cli(installation,'status');check('fresh_has_no_endpoint_or_keys',not initial['public_url'] and initial['active_api_keys']==0)
        cli(installation,'plan','--account-id',account);planned=cli(installation,'status')
        cli(installation,'deploy');deployed=cli(installation,'status');url=deployed['public_url'];RESULT['url']=url
        check('first_byo_deployment_paired',deployed['device_paired'] and url.startswith('https://'+planned['worker_name']+'.'))
        created=cli(installation,'key-create','--label','Clean acceptance only');created_keys.append(created['id']);key=created['key'];secrets.append(key)
        # A migration baseline prepares persistent state and proves its existing
        # key locally. All current-cloud/CLI acceptance belongs to the new release.
        process=launch(installation)
        code,old_models=http(f'http://127.0.0.1:{process.bridge_port}/api/v1/models',key,timeout=5)
        check('baseline_key_valid_before_upgrade',code==200 and len(old_models['data'])==2,version=installation['version'])
        identity=metadata(data);stop(process);process=None
        new_package=extracted(args.candidate,directory/'new-package')
        previous_exe=installation['exe'];installation=install(new_package,root,shortcuts)
        check('actual_version_update_preserves_profile',installation['exe']!=previous_exe and installation['version']!=initial['version'] and metadata(data)==identity,
              before_version=initial['version'],after_version=installation['version'])
        cli(installation,'deploy')
        check('upgraded_worker_keeps_original_identity',metadata(data)==identity)
        process=launch(installation);models=wait_models(url,key)
        check('first_public_models_get',len(models['data'])==2,version=installation['version'])
        code,body=http(url+'/api/v1/chat/completions',key,{'model':'anthropic/claude-haiku-4.5','messages':[{'role':'user','content':marker+' Reply OK only.'}],'stream':False})
        check('public_claude_subscription_post',code==200 and body.get('object')=='chat.completion' and bool(body.get('choices')),
              http_status=code,error_type=body.get('error',{}).get('metadata',{}).get('error_type'))
        code,job=http(url+'/bridge/v1/jobs',key,{'model':'openai/gpt-6-astra','messages':[{'role':'user','content':marker+' Reply OK only.'}],'stream':False})
        check('public_codex_async_post',code==202,http_status=code)
        deadline=time.monotonic()+190
        while time.monotonic()<deadline:
            code,body=http(url+'/bridge/v1/jobs/'+job['id'],key)
            if body.get('status') in {'completed','failed','cancelled','interrupted','succeeded'}:break
            time.sleep(1)
        check('public_codex_job_get',code==200 and body.get('status')=='completed' and body.get('response',body.get('result',{})).get('object')=='chat.completion',
              http_status=code,job_status=body.get('status'))
        code,error=http(url+'/api/v1/chat/completions',key,{'model':'anthropic/claude-haiku-4.5','messages':[{'role':'user','content':marker}],'temperature':.4})
        check('unsupported_parameter_explicit_error',code==400 and error.get('error',{}).get('metadata',{}).get('error_type')=='unsupported_parameter',http_status=code)
        identity=metadata(data);stop(process);process=launch(installation);wait_models(url,key)
        check('restart_same_url_key_and_device',metadata(data)==identity)
        cli(installation,'pause');cli(installation,'wait-idle');cli(installation,'deploy');cli(installation,'resume');wait_models(url,key)
        check('repeated_deployment_same_url_key_and_transport',metadata(data)==identity)
        code,body=http(url+'/api/v1/chat/completions',key,{'model':'anthropic/claude-haiku-4.5','messages':[{'role':'user','content':marker+' Reply OK only.'}],'stream':False})
        check('updated_exe_same_key_real_inference',code==200 and body.get('object')=='chat.completion' and metadata(data)==identity,http_status=code)
        cli(installation,'pause');cli(installation,'wait-idle');cli(installation,'deploy');cli(installation,'resume');wait_models(url,key)
        check('updated_worker_redeploy_keeps_identity',metadata(data)==identity)
        stop(process);process=None;process=stale_poll_acceptance(installation,url,key)
        recovery=[]
        for attempt in range(5):
            stop(process);started=time.monotonic();process=launch(installation);wait_models(url,key)
            recovery.append(round(time.monotonic()-started,2))
        check('five_consecutive_updated_process_restarts',max(recovery)<15 and metadata(data)==identity,
              recovery_seconds=recovery)
        # Latest release must also pass a truly empty second device profile.
        latest=install(new_package,directory/'latest clean install',directory/'latest shortcuts')
        latest_status=cli(latest,'status');check('latest_clean_install_empty',not latest_status['public_url'] and not latest_status['active_api_keys'],version=latest_status['version'])
        cli(latest,'plan','--account-id',account);cli(latest,'deploy');latest_status=cli(latest,'status')
        check('latest_first_deploy_distinct_device',latest_status['public_url']!=url and latest_status['device_id']!=deployed['device_id'])
        second=cli(latest,'key-create','--label','Latest clean acceptance only')
        other=None
        try:
            other=launch(latest);wait_models(latest_status['public_url'],second['key'])
            check('latest_clean_package_public_get',True)
        finally:
            cli(latest,'key-revoke','--key-id',second['id'])
            if other:check('latest_test_key_revoked',http(latest_status['public_url']+'/api/v1/models',second['key'])[0]==401)
            stop(other)
        check('latest_profile_metadata_only',second['key'].encode() not in (latest['data_dir']/'bridge.sqlite').read_bytes())
        RESULT['latest_clean_url']=latest_status['public_url']
        cli(installation,'key-revoke','--key-id',created['id']);check('test_key_revoked',http(url+'/api/v1/models',key)[0]==401)
        created_keys.clear();privacy(data,[marker,*secrets]);cli_privacy(before_cli,marker)
        # Reinstall latest into same root, deliberately omitting data-dir.
        stop(process);process=None
        keys_before=metadata(data);installation=install(new_package,root,shortcuts)
        check('same_version_reinstall_preserves_identity',metadata(data)==keys_before)
        after_shell=current_shell();check('existing_shortcuts_and_startup_unchanged',baseline_shell[:2]==after_shell[:2])
        check('existing_claude_processes_undisturbed',baseline_shell[2].issubset(after_shell[2]),initial_process_count=len(baseline_shell[2]))
        if before_current is not None:
            check('existing_bridge_still_healthy',http('http://127.0.0.1:8920/health',timeout=2)==before_current)
        else:
            check('existing_bridge_not_started_or_managed',True,not_running_at_start=True)
        with zipfile.ZipFile(args.candidate) as archive:
            check('distribution_contains_no_device_credentials',not any(n.endswith(('.sqlite','.dpapi')) or '/byo-worker/' in n or '/.wrangler/' in n for n in archive.namelist()))
        RESULT['candidate_sha256']=hashlib.sha256(args.candidate.read_bytes()).hexdigest();RESULT['complete']=True
    except Exception as error:
        # Error types and named gates only, never request bodies or provider diagnostics.
        RESULT['complete']=False;RESULT['failure_type']=type(error).__name__
        if isinstance(error,RuntimeError):RESULT['failure_gate']=str(error)
        print(json.dumps({'acceptance_failed':True,'type':type(error).__name__}),flush=True)
    finally:
        if installation:
            for kid in created_keys:
                try:cli(installation,'key-revoke','--key-id',kid)
                except Exception:pass
        stop(process);evidence.write_text(json.dumps(RESULT,indent=2),encoding='utf-8')
        print(json.dumps({'evidence':str(evidence),'complete':RESULT.get('complete',False)}),flush=True)
    return 0 if RESULT.get('complete') else 1


if __name__=='__main__':raise SystemExit(main())
