"""Real Windows Setup -> A -> native Velopack B. No Cloud/production profile access."""
import argparse
import base64
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from desktop_bridge import secret
from desktop_bridge.store import Store
from desktop_bridge.windows_release import atomic_json
from desktop_bridge.windows_updates import control


def run(command, **kwargs):
    return subprocess.run(list(map(str,command)),check=True,timeout=kwargs.pop('timeout',180),**kwargs)


def cli(exe,*args,**kwargs):
    try:
        value=run([exe,*args],capture_output=True,text=True,**kwargs)
    except subprocess.CalledProcessError as error:
        # Native CLI emits sanitized UpdateError messages. Do not emit arbitrary
        # process output; match only literal errors from the maintained source.
        import ast
        tree=ast.parse((ROOT/'desktop_bridge/windows_updates.py').read_text())
        known=[node.args[0].value for node in ast.walk(tree) if isinstance(node,ast.Call)
            and isinstance(node.func,ast.Name) and node.func.id=='UpdateError' and node.args
            and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str)]
        known.append('Operation failed; check the selected profile and installer guide.')
        raw=error.stderr or ''
        if isinstance(raw,bytes):raw=raw.decode('utf-8','replace')
        category=next((message for message in known if message in raw),'Unknown native CLI failure')
        print(json.dumps({'native_cli_failed':True,'return_code':error.returncode,'safe_error':category}),flush=True)
        raise
    if not value.stdout.strip() and args[:2]==('update','apply'):
        return {'native_handoff':True}
    return json.loads(value.stdout.strip().splitlines()[-1])


def wait(predicate,seconds=45):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        try:
            result=predicate()
            if result:return result
        except (OSError,ValueError):pass
        time.sleep(.25)
    raise RuntimeError('Acceptance condition timed out.')


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--vpk',required=True)
    p.add_argument('--skip-renderer',action='store_true',help='Local non-desktop acceptance; CI still exercises the real renderer and clipboard.')
    args=p.parse_args();root=Path(args.output).resolve()
    if root.exists():raise ValueError('Use a new isolated acceptance output directory.')
    root.mkdir(parents=True);data=root/'profile';installed=root/'installed';web=root/'web';web.mkdir()
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    signing=Ed25519PrivateKey.generate();public=base64.b64encode(signing.public_key().public_bytes_raw()).decode()
    package_id='AIGO.LLMBridge.Probe.'+uuid.uuid4().hex[:12]
    class Handler(SimpleHTTPRequestHandler):
        def log_message(self,*_):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(web)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    origin='http://127.0.0.1:'+str(server.server_port)
    spec=importlib.util.spec_from_file_location('sign_update',ROOT/'packaging/windows/sign_update.py')
    signer=importlib.util.module_from_spec(spec);spec.loader.exec_module(signer)
    checks={};successful=False
    try:
        for label,version in [('a','0.7.0'),('b','0.7.1')]:
            print('BUILD '+label.upper(),flush=True)
            run([sys.executable,ROOT/'packaging/windows/build_installer.py','--local-probe',
                '--pack-id',package_id,'--probe-data-dir',data,'--version',version,'--public-key',public,
                '--policy-url',origin+'/policy.json','--vpk',args.vpk,'--output',root/label],timeout=600)
            # The native updater downloads an immutable release directory, not a mutable latest feed.
            import shutil
            shutil.copytree(root/label/'Releases',web/label)
        policy_a=signer.sign(root/'a',origin+'/a',1,'0.7.0',signing)
        policy_b=signer.sign(root/'b',origin+'/b',2,'0.7.0',signing)
        atomic_json(web/'policy.json',policy_a)
        print('INSTALL A (silent, isolated)',flush=True)
        setup=next((root/'a/Releases').glob('*Setup.exe'))
        run([setup,'--silent','--installto',installed])
        executable=installed/'current/aigo-bridge.exe'
        checks['setup_created_native_install']=(installed/'Update.exe').is_file() and executable.is_file()
        assert cli(executable,'version')['version']=='0.7.0'
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        store=Store(data);store.set('port',port);store.set('public_url','https://isolated-device.example.invalid')
        device=store.get('device_id');store.close()
        created=cli(executable,'byo','key-create','--data-dir',data,'--label','isolated-acceptance','--providers','codex')
        kid,key=created['id'],created['key']
        checks['frozen_cli_key_creation']=True
        store=Store(data,startup=False)
        rid=uuid.uuid4().hex
        store.insert_request({'id':rid,'key_id':kid,'provider':'codex','model':'synthetic',
            'status':'completed','http_status':200,'created_ts':time.time(),'prompt_tokens':17,'completion_tokens':9,'cost_usd':.012345})
        store.close();credential=uuid.uuid4().hex+uuid.uuid4().hex;secret.save(data,credential)
        legacy=root/'legacy-install.json';atomic_json(legacy,{'data_dir':str(data),'exe':str(root/'legacy/bridge.exe')})
        checks['legacy_adoption_preserves_identity']=cli(executable,'adopt','--manifest',legacy,'--data-dir',data)['device_id']==device
        checks['profile_binding_preserved']=json.loads((installed/'windows-profile.json').read_text())['data_dir']==str(data)
        guided=run([executable,'setup','--data-dir',data],input='\n',capture_output=True,text=True,timeout=60)
        checks['cli_setup_cancel_without_deploy']='BYO Cloudflare setup' in guided.stdout
        cli(executable,'start','--data-dir',data)
        wait(lambda:(data/'windows-control.dpapi').is_file())
        checks['fresh_install_requires_onboarding']=cli(executable,'onboarding','status','--data-dir',data)['required'] is True
        installation=(installed/'windows-installation.json').read_bytes()
        import urllib.request
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        def models():
            req=urllib.request.Request('http://127.0.0.1:'+str(port)+'/api/v1/models',headers={'Authorization':'Bearer '+key})
            with opener.open(req,timeout=5) as response:return json.load(response)
        checks['a_original_key_authenticates']=bool(wait(models)['data'])
        schema_request=urllib.request.Request('http://127.0.0.1:'+str(port)+'/bridge/v1/preflight',
            data=json.dumps({'messages':[{'role':'user','content':'synthetic schema preflight'}],
                'response_format':{'type':'json_schema','json_schema':{'name':'probe','schema':{'type':'object'}}}}).encode(),
            headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        with opener.open(schema_request,timeout=15) as response:
            checks['frozen_schema_helper_preflight']=json.load(response)['ready'] is True
        if not args.skip_renderer:
            run([installed/'current/AIGO-LLM-Bridge.exe','--console-probe','--data-dir',data],
                capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
            console_report=json.loads((data/'windows-console-probe.json').read_text())
            assert console_report['success'],console_report['stage']
            checks.update({'console_'+k:v for k,v in console_report['checks'].items()})
            checks['closed_console_keeps_same_key_service']=bool(models()['data'])
        # Fixture marks only local lifecycle completion. It does not claim Cloud/login/power acceptance.
        onboarding_path=data/'windows-onboarding.json'
        onboard=json.loads(onboarding_path.read_text());onboard['completed_at']=time.time()
        onboard['acceptance_fixture']=True;atomic_json(onboarding_path,onboard)
        onboarding_bytes=onboarding_path.read_bytes()
        checks['completed_profile_daily_bypass']=cli(executable,'onboarding','status','--data-dir',data)['required'] is False
        atomic_json(web/'policy.json',policy_b)
        checks['new_version_detected']=cli(executable,'update','check','--data-dir',data)['latest']=='0.7.1'
        def rejected_update():
            failed=subprocess.run([str(executable),'update','apply','--data-dir',str(data),'--timeout','1'],capture_output=True,timeout=60)
            assert failed.returncode!=0
            assert models()['data']
        tampered={**policy_b,'signature':base64.b64encode(b'0'*64).decode()}
        atomic_json(web/'policy.json',tampered);rejected_update()
        checks['bad_signature_keeps_a_available']=True
        atomic_json(web/'policy.json',policy_b)
        feed=web/'b'/('releases.'+json.loads((root/'b/artifacts.json').read_text())['config']['framework_channel']+'.json')
        original_feed=feed.read_bytes();feed.write_bytes(original_feed+b' ')
        rejected_update();checks['bad_feed_keeps_a_available']=True;feed.write_bytes(original_feed)
        busy_id=uuid.uuid4().hex
        store=Store(data,startup=False)
        store.insert_request({'id':busy_id,'key_id':kid,'provider':'codex','model':'synthetic',
                              'status':'running','created_ts':time.time()});store.close()
        rejected_update()
        store=Store(data,startup=False)
        checks['busy_timeout_restores_accepting']=store.get('accepting') is True
        store.update_request(busy_id,status='completed',http_status=200,finished_ts=time.time());store.close()
        # Announce a mandatory B after exercising the optional-update failures.
        mandatory=signer.sign(root/'b',origin+'/b',3,'0.7.1',signing)
        atomic_json(web/'policy.json',mandatory)
        control(data,'check',pack_id=package_id)
        def blocked():
            store=Store(data,startup=False)
            try:return store.get('accepting') is False
            finally:store.close()
        checks['mandatory_policy_pauses_new_work']=bool(wait(blocked))
        try:
            req=urllib.request.Request('http://127.0.0.1:'+str(port)+'/api/v1/chat/completions',
                data=json.dumps({'model':models()['data'][0]['id'],'messages':[{'role':'user','content':'synthetic update gate'}]}).encode(),
                headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
            opener.open(req,timeout=5)
            raise AssertionError('Mandatory update accepted inference.')
        except urllib.error.HTTPError as error:
            checks['mandatory_policy_rejects_inference']=error.code==503
        # Normal stop and restart must retain the required state and management access.
        control(data,'drain',pack_id=package_id);control(data,'shutdown',pack_id=package_id)
        wait(lambda:not (data/'windows-control.dpapi').exists());time.sleep(1)
        cli(executable,'start','--data-dir',data)
        wait(lambda:(data/'windows-control.dpapi').is_file())
        checks['mandatory_policy_survives_restart']=bool(wait(blocked)) and bool(models()['data'])
        try:
            marker=json.loads(secret.protect((data/'windows-control.dpapi').read_bytes(),decrypt=True))
            req=urllib.request.Request(marker['origin']+'/manage/accepting',data=b'{"accepting":true}',
                headers={'Authorization':'Bearer '+marker['token'],'Content-Type':'application/json'})
            opener.open(req,timeout=5)
            raise AssertionError('Management bypassed the minimum version.')
        except urllib.error.HTTPError as error:
            checks['mandatory_policy_cannot_resume_old_version']=error.code==400 and blocked()
        print('APPLY B (native download and restart)',flush=True)
        view=None
        if not args.skip_renderer:
            view=subprocess.Popen([str(installed/'current/AIGO-LLM-Bridge.exe'),'--console','--console-hidden',
                '--data-dir',str(data)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            wait(lambda:json.loads((data/'windows-console.json').read_text()).get('mode')=='webview2')
        cli(executable,'update','apply','--data-dir',data,timeout=180)
        result=wait(lambda:json.loads((data/'updates/last-result.json').read_text()) if (data/'updates/last-result.json').is_file() else None,90)
        checks['native_restarted_to_b']=result['target']=='0.7.1' and cli(executable,'version')['version']=='0.7.1'
        if view:
            checks['open_console_exits_for_update']=(view.wait(timeout=30)==0 and
                json.loads((data/'windows-console.json').read_text())['mode']=='closed')
        checks['b_same_key_authenticates']=bool(wait(models)['data'])
        store=Store(data,startup=False)
        checks['same_device']=store.get('device_id')==device
        checks['same_url']=store.get('public_url')=='https://isolated-device.example.invalid'
        checks['same_key_hash']=store.authenticate(key)['id']==kid
        row=store.request(rid,kid)
        checks['metadata_and_cost_retained']=row['prompt_tokens']==17 and row['completion_tokens']==9 and row['cost_usd']==.012345
        checks['accepting_restored']=store.get('accepting') is True
        store.close()
        checks['dpapi_retained']=secret.load(data)==credential
        checks['installation_id_survives_update']=(installed/'windows-installation.json').read_bytes()==installation
        checks['onboarding_receipt_survives_restart_update']=onboarding_path.read_bytes()==onboarding_bytes
        checks['updated_profile_daily_bypass']=cli(executable,'onboarding','status','--data-dir',data)['required'] is False
        checks['onboarding_receipt_backed_up']=(data/'updates/before-0.7.1/windows-onboarding.json').read_bytes()==onboarding_bytes
        checks['database_backup']=(data/'updates/before-0.7.1/bridge.sqlite').is_file()
        checks['key_not_stored_plaintext']=all(key.encode() not in path.read_bytes() for path in data.rglob('*') if path.is_file())
        control(data,'drain',pack_id=package_id);control(data,'shutdown',pack_id=package_id)
        wait(lambda:not (data/'windows-control.dpapi').exists())
        time.sleep(1)
        run([installed/'Update.exe','--silent','uninstall'])
        wait(lambda:not executable.exists())
        store=Store(data,startup=False)
        checks['uninstall_preserves_profile']=store.authenticate(key)['id']==kid and store.get('device_id')==device
        store.revoke(kid)
        checks['test_key_revoked']=store.authenticate(key) is None
        store.close()
        assert all(checks.values()),checks
        successful=True
    finally:
        try:control(data,'drain',pack_id=package_id);control(data,'shutdown',pack_id=package_id)
        except Exception:pass
        server.shutdown();server.server_close()
        report={'checks':checks,'success':successful,'package_id':package_id,
            'native_renderer_tested':not args.skip_renderer,
            'external_https_tested':False,'provider_inference_tested':False,'production_modified':False,
            'notes':'Real Setup and native A-to-B update; URL is a retained synthetic fixture. No Cloud change.'}
        atomic_json(root/'acceptance.json',report)
        print(json.dumps(report),flush=True)


if __name__=='__main__':main()
