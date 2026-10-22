"""Frozen console entry for Windows install, BYO setup and safe update."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time


def verify_endpoint(store, key, infer=False):
    """Safe GET retries, at most one synthetic POST; only metadata leaves RAM."""
    import ssl
    import urllib.request
    import certifi
    from .connection_test import NoRedirect
    model = next(m['id'] for m in store.get('models') if m['provider']=='codex')
    base = store.get('public_url') + '/api/v1'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
    headers = {'Authorization':'Bearer '+key, 'Content-Type':'application/json', 'User-Agent':'llm-bridge-windows-setup/1'}
    until = time.monotonic()+35
    while True:
        try:
            with opener.open(urllib.request.Request(base+'/models',headers=headers),timeout=10) as response:
                models = json.loads(response.read(65536))['data']
            if not any(item['id']==model for item in models):
                raise ValueError()
            break
        except Exception:
            if time.monotonic() >= until:
                return {'models_verified':False, 'inference_verified':False}
            time.sleep(1)
    result = {'models_verified':True, 'inference_verified':False}
    if not infer:
        return result
    body = {'model':model, 'messages':[{'role':'user','content':'Reply exactly PONG.'}], 'stream':False}
    try:
        with opener.open(urllib.request.Request(base+'/chat/completions',data=json.dumps(body).encode(),headers=headers),timeout=100) as response:
            value = json.loads(response.read(65536))
        usage = value['usage']
        result['inference_verified'] = (value['choices'][0]['message']['content'].strip()=='PONG'
            and type(usage.get('cost')) in (int,float) and usage['cost']>=0)
        result['usage'] = {k:usage[k] for k in ('prompt_tokens','completion_tokens','cost') if k in usage}
    except Exception:
        result['notice'] = 'Inference outcome unknown or invalid; do not automatically retry.'
    return result

from .windows_release import config, profile, stable_entry, atomic_json


def adopt(manifest, directory):
    from .store import Store
    from . import secret
    from .windows import Instance
    value = json.loads(Path(manifest).read_text(encoding='utf-8-sig'))
    selected = Path(value['data_dir']).resolve()
    if selected != Path(directory).resolve() or not (selected / 'bridge.sqlite').is_file():
        raise ValueError('Adoption must explicitly select the existing manifest data directory.')
    instance = Instance(selected)
    primary = instance.primary; instance.close()
    if not primary:
        raise ValueError('Pause and stop the legacy Bridge before adoption; no process was terminated.')
    store = Store(selected, startup=False)
    try:
        if not secret.load(selected) and store.get('relay_enabled'):
            raise ValueError('Original Windows user must restore the paired credential before adoption.')
        atomic_json(selected / 'windows-install.json', {'legacy_manifest': str(Path(manifest).resolve()),
            'data_dir': str(selected), 'device_id': store.get('device_id')})
        install_root = Path(sys.executable).resolve().parent.parent
        if getattr(sys, 'frozen', False) and (install_root / 'Update.exe').is_file():
            atomic_json(install_root / 'windows-profile.json', {'pack_id':config()['pack_id'], 'data_dir':str(selected)})
        return {'adopted': True, 'device_id': store.get('device_id'), 'data_dir': str(selected)}
    finally:
        store.close()


def setup(cfg, directory):
    from . import byo
    print('BYO Cloudflare setup: credentials remain in their official CLIs.', flush=True)
    if byo.main(['doctor', '--data-dir', str(directory)]):
        return 1
    print('If a subscription is not ready, finish its official CLI login yourself. No account will be changed.', flush=True)
    print('Official login commands when needed: codex login / wrangler.cmd login. Node.js 22+ and Wrangler are required for deployment.', flush=True)
    account = input('Your Cloudflare account ID (blank to stop): ').strip()
    if not account:
        return 0
    if byo.main(['plan', '--data-dir', str(directory), '--account-id', account]):
        return 1
    if input('Deploy this device to that account? [yes/NO]: ').strip() != 'yes':
        return 0
    if byo.main(['deploy', '--data-dir', str(directory)]):
        print('Complete official Wrangler login/workers.dev registration if needed, then rerun setup.', flush=True)
        return 1
    if input('Create a service key for all registered Claude/Codex models, shown once? [yes/NO]: ').strip() == 'yes':
        import contextlib
        import io
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture):
            code = byo.main(['key-create', '--data-dir', str(directory),
                             '--label', 'Web service', '--handoff'])
        if code:
            print('Service key creation was not completed.'); return code
        created = json.loads(capture.getvalue()); capture.close()
        from .store import Store
        store = Store(directory, startup=False)
        try:
            subprocess.Popen([str(stable_entry()), '--data-dir', str(directory), '--background'],
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            infer = input('Run one synthetic Codex inference using your subscription? [yes/NO]: ').strip() == 'yes'
            checked = verify_endpoint(store, created['key'], infer=infer)
            print(json.dumps({'verification':checked},ensure_ascii=False))
        finally:
            store.close()
            # Still deliver the valid long-lived service key if verification fails or is declined.
            print(json.dumps(created,ensure_ascii=False))
        return 0
    return 0


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    cfg = config()
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ['byo']:
        from .byo import main as byo_main
        values = argv[1:]
        selector = argparse.ArgumentParser(add_help=False)
        selector.add_argument('--data-dir')
        selected, _ = selector.parse_known_args(values)
        profile(cfg, selected.data_dir)
        if not selected.data_dir:
            values += ['--data-dir', str(profile(cfg))]
        return byo_main(values)
    p = argparse.ArgumentParser(description='Windows LLM Bridge: installer-owned profile and signed updates.')
    p.add_argument('action', choices=['version', 'setup', 'start', 'status', 'update', 'adopt'])
    p.add_argument('operation', nargs='?', choices=['check', 'apply', 'status', 'recover'])
    p.add_argument('--data-dir')
    p.add_argument('--manifest')
    p.add_argument('--timeout', type=int, default=180)
    args = p.parse_args(argv)
    directory = profile(cfg, args.data_dir)
    try:
        if args.action == 'version':
            result = {k: cfg[k] for k in ('version', 'core_version', 'commit', 'pack_id', 'local_probe')}
        elif args.action == 'adopt':
            if not args.manifest or not args.data_dir:
                raise ValueError('Adoption requires --manifest and the original --data-dir.')
            result = adopt(args.manifest, directory)
        elif args.action == 'setup':
            return setup(cfg, directory)
        elif args.action == 'start':
            subprocess.Popen([str(stable_entry()), '--data-dir', str(directory), '--background'],
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            result = {'starting': True}
        elif args.action == 'status':
            from .byo import main as byo_main
            return byo_main(['status', '--data-dir', str(directory)])
        else:
            from . import windows_updates
            if args.operation == 'apply':
                result = windows_updates.apply(cfg, directory, args.timeout)
            elif args.operation == 'recover':
                result = windows_updates.recover(cfg, directory)
            elif args.operation == 'status':
                path = directory / 'updates' / 'last-result.json'
                result = json.loads(path.read_text()) if path.is_file() else {'installed_verified': False}
            else:
                result = windows_updates.check(cfg, directory)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        # Never expose CLI output, credentials, request content, URLs with query tokens or raw tracebacks.
        from .windows_updates import UpdateError
        print(str(exc) if isinstance(exc, UpdateError) else 'Operation failed; check the selected profile and installer guide.', file=sys.stderr)
        return 1
