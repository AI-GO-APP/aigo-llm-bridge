"""User-owned Cloudflare deployment and device-profile maintenance. No publisher backend."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import time
import ssl
import urllib.error
import urllib.request
import uuid
import certifi
from urllib.parse import urlsplit

from . import __version__
from . import secret
from .store import Store
from .paths import default_directory
from .handoff import integration
from . import providers


class SetupError(Exception):
    pass


def template_directory():
    if getattr(sys,'frozen',False):return Path(sys.executable).parent.parent/'cloudflare'
    return Path(__file__).resolve().parent.parent/'cloudflare'


def origin(value):
    parsed=urlsplit(value)
    if parsed.scheme!='https' or not parsed.hostname or parsed.path not in {'','/'} or parsed.query or parsed.fragment or parsed.username or parsed.password or parsed.port not in {None,443}:
        raise SetupError('請填 HTTPS origin，不含 /api/v1、帳密、非標準 port 或 query。')
    return value.rstrip('/')


def configure(store,account_id=None,worker_name=None,template=None):
    """Create a stable per-device project. Re-authentication cannot change its target."""
    pinned_account=store.get('cloudflare_account_id')
    account=account_id or pinned_account
    if not isinstance(account,str) or not re.fullmatch('[a-fA-F0-9]{32}',account):
        raise SetupError('請用 --account-id 明確指定安裝者自己的 Cloudflare account ID。')
    account=account.lower()
    if pinned_account and account!=pinned_account:
        raise SetupError('此裝置已綁定其他 Cloudflare 帳戶；拒絕因 CLI 換帳號而遷移網址。請使用原帳戶。')
    pinned_name=store.get('cloudflare_worker_name')
    existing=store.get('public_url')
    host=urlsplit(existing).hostname or ''
    legacy=re.fullmatch(r'([a-z0-9-]+)\.[a-z0-9-]+\.workers\.dev',host)
    name=worker_name or pinned_name or (legacy.group(1) if legacy else 'llm-bridge-'+store.get('device_id')[:20])
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,62}',name):raise SetupError('Worker 名稱需為小寫英數／連字號，最多 63 字。')
    if pinned_name and pinned_name!=name:raise SetupError('此裝置已綁定固定 Worker 名稱，拒絕自動重新配發網址。')
    if legacy and name!=legacy.group(1):raise SetupError('Worker 名稱與既有網址不同；請保留原 Worker。')
    source=Path(template or template_directory())/'src/worker.js'
    if not source.is_file():raise SetupError('找不到 Cloudflare 範本；請保留完整 repo 或安裝包的 cloudflare 目錄。')
    project=store.directory/'byo-worker';(project/'src').mkdir(parents=True,exist_ok=True)
    (project/'src/worker.js').write_bytes(source.read_bytes())
    config={'name':name,'account_id':account,'main':'src/worker.js','compatibility_date':'2026-10-22',
            'workers_dev':True,'observability':{'enabled':False},
            'durable_objects':{'bindings':[{'name':'DEVICE','class_name':'DeviceRelay'}]},
            'migrations':[{'tag':'v1','new_sqlite_classes':['DeviceRelay']}]}
    path=project/'wrangler.json';path.write_text(json.dumps(config,indent=2),encoding='utf-8')
    with store.lock,store.db:
        for field,value in (('cloudflare_account_id',account),('cloudflare_worker_name',name)):
            store.db.execute('insert or replace into settings values (?,?)',(field,json.dumps(value)))
    return path


def wrangler_command(explicit=None):
    node=shutil.which('node')
    if not node:raise SetupError('請先安裝 Node.js，再安裝 Wrangler；不需將 Cloudflare 憑證提供給發布方。')
    candidates=[Path(explicit)] if explicit else []
    candidates.extend([template_directory()/'node_modules/wrangler/bin/wrangler.js',
                       Path(os.environ.get('APPDATA',''))/'npm/node_modules/wrangler/bin/wrangler.js'])
    found=shutil.which('wrangler')
    if found:
        resolved=Path(found).resolve()
        candidates.extend([resolved,resolved.parent/'node_modules/wrangler/bin/wrangler.js'])
    for path in candidates:
        if path.suffix=='.js' and path.is_file():return [node,str(path.resolve())]
    raise SetupError('找不到 Wrangler；可執行 npm install -g wrangler@4.95.0，或使用 --wrangler-js 指定其 JS 入口。')


class Cloudflare:
    def __init__(self,config,account_id,explicit=None):
        self.config=Path(config);self.account_id=account_id;self.command=wrangler_command(explicit)
    def run(self,args,input=None):
        env=dict(os.environ)
        env.update(CLOUDFLARE_ACCOUNT_ID=self.account_id,WRANGLER_SEND_METRICS='false',CI='true')
        try:
            result=subprocess.run(self.command+list(args)+['--config',str(self.config)],
                cwd=self.config.parent,env=env,input=input,capture_output=True,timeout=180,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except (OSError,subprocess.SubprocessError):
            raise SetupError('Wrangler 未完成；請檢查 Node、網路及安裝者自己的 Cloudflare 登入。') from None
        if result.returncode:
            raise SetupError('Cloudflare 操作失敗；請用 wrangler whoami 確認原帳戶權限。未輸出可能含憑證的原始診斷。')
        return result.stdout.decode('utf-8','replace')
    def verify(self):
        try:data=json.loads(self.run(['whoami','--json']))
        except ValueError:raise SetupError('Wrangler 未返回可驗證的登入資訊，請確認版本與登入。') from None
        accounts=data.get('accounts',[]) if isinstance(data,dict) else []
        if self.account_id not in {str(a.get('id','')).lower() for a in accounts if isinstance(a,dict)}:
            raise SetupError('目前 Cloudflare 登入無法管理此裝置原綁定帳戶；拒絕另建入口或改寫網址。')

    def wait_pairing(self,url,token):
        # A fresh Worker/secret can reach the edge after the CLI reports success.
        # Confirm the credential on the actual HTTPS data path before handing out
        # the first endpoint. Existing profiles are never polled by this probe.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*_args,**_kwargs):return None
        opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
        payload=json.dumps({'key_digests':[],'agent_session':uuid.uuid4().hex}).encode()
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            request=urllib.request.Request(url+'/agent/poll',data=payload,headers={
                'Authorization':'Bearer '+token,'Content-Type':'application/json','User-Agent':'aigo-llm-bridge-client/1.0'})
            try:
                with opener.open(request,timeout=25) as response:
                    value=json.loads(response.read(10000))
                    if response.status==200 and isinstance(value,dict) and 'request' in value:return
            except (OSError,ValueError):pass
            time.sleep(2)
        raise SetupError('首次 Worker 配對尚未在 HTTPS 生效；已保留加密 pending 憑證，稍後重跑 deploy，勿刪除資料。')


def publish(store,config,cloud,*,url=None,code=True,repair=False):
    """Retryable pairing: pending credentials are DPAPI encrypted before cloud writes."""
    # Refuse decryption trouble before any cloud mutation, unless repair was explicit.
    try:current=secret.load(store.directory)
    except ValueError:
        if not repair:raise SetupError('裝置 DPAPI 憑證無法解密；先保留原資料，再用 repair-device-key 重新授權配對。') from None
        current=''
    try:pending=secret.load(store.directory,pending=True)
    except ValueError:
        if not repair:raise SetupError('未完成的配對憑證無法解密；請用 repair-device-key。') from None
        pending=''
    token=pending or (secrets.token_urlsafe(48) if repair else current or secrets.token_urlsafe(48))
    cloud.verify()
    existing=store.get('public_url')
    target=origin(url) if url else existing
    if existing and target and existing!=target:raise SetupError('拒絕改變此裝置已保存的 endpoint；Cloudflare 帳戶／網域遷移需另外明確處理。')
    if not code and not existing:raise SetupError('初次配對需先部署並核對該帳戶的固定網址。')
    if target and not re.fullmatch('https://'+re.escape(store.get('cloudflare_worker_name'))+r'\.[a-z0-9-]+\.workers\.dev',target):
        raise SetupError('自動配對只接受此裝置 Worker 的 workers.dev 網址；自訂網域需另外核對路由所有權。')
    if code:
        output=cloud.run(['deploy'])
        pattern=r'https://'+re.escape(store.get('cloudflare_worker_name'))+r'\.[a-z0-9-]+\.workers\.dev\b'
        found=re.findall(pattern,output)
        if not target:
            if len(set(found))!=1:raise SetupError('無法確認固定 workers.dev 網址；保留原設定，請用 pair --url 明確配對。')
            target=found[0]
        elif target.endswith('.workers.dev') and target not in found:
            raise SetupError('部署回報網址與原 endpoint 不同；保留原設定，不自動遷移。')
    if not target:raise SetupError('請先 deploy，或以 pair --url 明確指定自有 Worker。')
    # Only encrypted bytes reach disk; never a plaintext secrets file or argv token.
    secret.save(store.directory,token,pending=True)
    cloud.run(['secret','put','DEVICE_KEY'],input=(token+'\n').encode())
    if not existing and hasattr(cloud,'wait_pairing'):cloud.wait_pairing(target,token)
    secret.commit_pending(store.directory)
    with store.lock,store.db:
        for field,value in (('public_url',target),('relay_enabled',True)):
            store.db.execute('insert or replace into settings values (?,?)',(field,json.dumps(value)))
    return target


def status(store):
    try:paired=bool(secret.load(store.directory));needs_repair=False
    except ValueError:paired=False;needs_repair=True
    with store.lock:
        active=store.db.execute("select count(*) from requests where status in ('queued','running')").fetchone()[0]
    return {'version':__version__,'deployment_mode':'byo','device_id':store.get('device_id'),'public_url':store.get('public_url'),
            'worker_name':store.get('cloudflare_worker_name'),'cloudflare_account_bound':bool(store.get('cloudflare_account_id')),
            'device_paired':paired,'device_repair_required':needs_repair,'accepting':store.get('accepting'),
            'active_requests':active,'active_api_keys':sum(r['revoked_ts'] is None for r in store.keys())}


def main(argv=None):
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr,'reconfigure'):sys.stderr.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description='BYO Cloudflare setup; device identity is independent of provider login.')
    parser.add_argument('action',choices=['status','plan','deploy','pair','repair-device-key','pause','resume','wait-idle',
                                        'key-create','key-list','key-revoke','key-rotate','handoff','doctor'])
    parser.add_argument('--data-dir',default=str(default_directory()))
    parser.add_argument('--account-id');parser.add_argument('--worker-name');parser.add_argument('--url')
    parser.add_argument('--template');parser.add_argument('--wrangler-js');parser.add_argument('--timeout',type=int,default=180)
    parser.add_argument('--label',default='');parser.add_argument('--key-id')
    parser.add_argument('--providers',nargs='+',choices=['claude','codex'],default=['claude','codex'])
    parser.add_argument('--rpm',type=int,default=30)
    parser.add_argument('--model');parser.add_argument('--handoff',action='store_true',help='Include a one-time integration message containing the new key; do not save stdout.')
    args=parser.parse_args(argv);store=None
    try:
        store=Store(args.data_dir,startup=False)
        if args.action=='doctor':
            node=shutil.which('node')
            try:node_ok=bool(node and int(subprocess.check_output([node,'--version'],timeout=10).decode().strip().lstrip('v').split('.')[0])>=22)
            except (ValueError,OSError,subprocess.SubprocessError):node_ok=False
            try:wrangler_command(args.wrangler_js);wrangler=True
            except SetupError:wrangler=False
            ready={p:providers.status(p,store)['ready'] for p in ('codex','claude')}
            print(json.dumps({'platform':sys.platform,'python':sys.version.split()[0],
                'node_22_or_newer':node_ok,'wrangler_installed':wrangler,'subscriptions':ready,
                'deployment':status(store),'notice':'Login/register in the official CLI if not ready; no login was modified.'},ensure_ascii=False));return 0
        if args.action=='handoff':
            print(json.dumps(integration(store,args.model,args.providers),ensure_ascii=False));return 0
        if args.action.startswith('key-'):
            if args.action=='key-list':result={'keys':store.keys()}
            elif args.action=='key-create':
                if args.handoff:integration(store,args.model,args.providers)
                kid,token=store.create_key(args.label,args.providers,args.rpm)
                result={'id':kid,'key':token,'notice':'Shown once; only its hash is stored.'}
                if args.handoff:result['integration']=integration(store,args.model,args.providers,token)
            else:
                if not args.key_id or not any(k['id']==args.key_id for k in store.keys()):
                    raise SetupError('請以 --key-id 指定此裝置存在的 key ID（不是明文 key）。')
                if args.action=='key-rotate':
                    allowed=json.loads(next(k for k in store.keys() if k['id']==args.key_id)['providers'])
                    if args.handoff:integration(store,args.model,allowed)
                    kid,token=store.rotate(args.key_id)
                    result={'id':kid,'key':token,'notice':'Shown once; the previous key is revoked.'}
                    if args.handoff:result['integration']=integration(store,args.model,allowed,token)
                else:
                    store.revoke(args.key_id);result={'revoked_id':args.key_id}
            print(json.dumps(result,ensure_ascii=False));return 0
        elif args.action in {'pause','resume'}:
            store.set('accepting',args.action=='resume')
        elif args.action=='wait-idle':
            deadline=time.monotonic()+max(1,args.timeout)
            while status(store)['active_requests']:
                if time.monotonic()>=deadline:raise SetupError('仍有未完成工作；未自動終止 CLI 或登入其他帳號。')
                time.sleep(.5)
        elif args.action!='status':
            name=args.worker_name
            if args.url and not name:
                match=re.fullmatch(r'([a-z0-9-]+)\.[a-z0-9-]+\.workers\.dev',urlsplit(args.url).hostname or '')
                if match:name=match.group(1)
            config=configure(store,args.account_id,name,args.template)
            if args.action!='plan':
                cloud=Cloudflare(config,store.get('cloudflare_account_id'),args.wrangler_js)
                publish(store,config,cloud,url=args.url,repair=args.action=='repair-device-key')
            else:
                print(json.dumps({'config':str(config),'cloudflare_account_id':store.get('cloudflare_account_id')},ensure_ascii=False))
        print(json.dumps(status(store),ensure_ascii=False));return 0
    except (SetupError,ValueError,OSError):
        # No raw exceptions, CLI stdout/stderr, token or provider credential is printed.
        error=sys.exc_info()[1]
        print(str(error) if isinstance(error,SetupError) else '本機設定未完成；請檢查資料目錄、格式與權限。',file=sys.stderr)
        return 1
    finally:
        if store:store.close()


if __name__=='__main__':raise SystemExit(main())
