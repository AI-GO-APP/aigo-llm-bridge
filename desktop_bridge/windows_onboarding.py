"""Resumable Windows installation workflow; never drives a model CLI as an agent."""
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import uuid
import ssl
import urllib.request
import urllib.error

import certifi

from . import byo, providers, secret
from .handoff import integration
from .windows_release import atomic_json, stable_entry


def installation_marker(root=None):
    root = Path(root) if root else Path(sys.executable).resolve().parent.parent
    return root / 'windows-installation.json'


def record_install(*_args):
    """Velopack after-install hook only; an ordinary update does not reset this ID."""
    atomic_json(installation_marker(), {'schema': 1, 'installation_id': uuid.uuid4().hex})


def installation_id(store, release):
    path = installation_marker()
    if getattr(sys, 'frozen', False) and path.is_file():
        return json.loads(path.read_text(encoding='utf-8'))['installation_id']
    # Portable/legacy adoption: one installation per device profile and package ID.
    return uuid.uuid5(uuid.NAMESPACE_URL, release['pack_id'] + ':' + store.get('device_id')).hex


def cloud_accounts(directory):
    command = byo.wrangler_command()
    env = dict(os.environ, WRANGLER_SEND_METRICS='false', CI='true')
    result = subprocess.run(command + ['whoami', '--json'], capture_output=True, timeout=30,
                            env=env, cwd=directory, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise byo.SetupError('Cloudflare 尚未登入，請先在官方 CLI 完成授權。')
    raw = json.loads(result.stdout)
    accounts = []
    for row in raw.get('accounts', []):
        account = str(row.get('id', '')).lower()
        if re.fullmatch('[a-f0-9]{32}', account):
            accounts.append({'id': account, 'name': str(row.get('name', 'Cloudflare account'))[:100]})
    if not accounts:
        raise byo.SetupError('登入沒有可部署的 Cloudflare 帳戶。')
    return accounts


def verify(store, key, model, public_url=None):
    """One explicit synthetic HTTPS POST; no redirects, raw body, or key on disk."""
    if not store.authenticate(key):
        raise ValueError('Invalid client key.')
    endpoint = byo.origin(public_url if public_url is not None else store.get('public_url')) + '/api/v1'
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *_args, **_kwargs):
            return None
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(
        context=ssl.create_default_context(cafile=certifi.where())))
    request = urllib.request.Request(endpoint + '/chat/completions', data=json.dumps({
        'model': model, 'messages': [{'role': 'user', 'content': 'Reply exactly PONG.'}], 'stream': False}).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
                 'User-Agent': 'local-token-buffet-bridge-onboarding/1.0'})
    started = time.monotonic()
    try:
        sync_deadline = time.monotonic() + 35
        while True:
            try:
                with opener.open(urllib.request.Request(endpoint + '/models', headers={
                        'Authorization': 'Bearer ' + key, 'User-Agent': 'local-token-buffet-bridge-onboarding/1.0'}), timeout=25) as response:
                    catalog = json.loads(response.read(65537))
                    if response.status != 200 or not any(m.get('id') == model for m in catalog.get('data', [])):
                        return {'success': False, 'http_status': response.status, 'code': 'models_unavailable'}
                break
            except urllib.error.HTTPError as error:
                # A fresh key digest propagates on the next poll. Only safe GET retries.
                if error.code != 401 or time.monotonic() >= sync_deadline:
                    raise
                time.sleep(1)
        with opener.open(request, timeout=100) as response:
            raw = response.read(65537)
            value = json.loads(raw) if len(raw) <= 65536 else {}
            cost = value.get('usage', {}).get('cost')
            success = (response.status == 200 and value['choices'][0]['message']['content'].strip() == 'PONG'
                       and type(cost) in (int, float) and math.isfinite(cost) and cost >= 0)
            return {'success': success, 'http_status': response.status,
                    'elapsed_ms': round((time.monotonic() - started) * 1000),
                    'cost_usd': cost if success else None, 'code': 'ok' if success else 'invalid_response'}
    except urllib.error.HTTPError as error:
        return {'success': False, 'http_status': error.code, 'code': 'endpoint_error'}
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError):
        return {'success': False, 'http_status': None, 'code': 'connection_failed'}


class Onboarding:
    state_filename = 'windows-onboarding.json'

    def installation_identity(self):
        return installation_id(self.store, self.owner.release)

    def apply_power(self, admin=False):
        if admin:
            from .windows_power_admin import request
            return request(self.power, 'apply')
        return self.power.apply(consent=True)

    def restore_power(self, admin=False):
        if admin:
            from .windows_power_admin import request
            return request(self.power, 'restore')
        return self.power.restore()

    def __init__(self, owner, power):
        self.owner, self.store, self.power = owner, owner.store, power
        self.path = self.store.directory / self.state_filename
        self.lock = threading.RLock()
        self.busy = threading.Lock()
        self.job = {'status': 'idle'}
        self.accounts = []
        self.subscriptions = {}
        self.login_processes = {}
        self.proof = None
        self.open_requested = False
        self.deployment_identity = (self.store.get('public_url'), self.store.get('relay_enabled'))
        self.installation = self.installation_identity()
        value = self.load()
        if value.get('installation_id') != self.installation:
            # Never touch URL, account binding, pairing secret, API keys or request rows.
            self.save({'schema': 1, 'installation_id': self.installation, 'completed_at': None})

    def load(self):
        if not self.path.is_file():
            return {}
        return json.loads(self.path.read_text(encoding='utf-8'))

    def save(self, value):
        atomic_json(self.path, value)

    def state(self):
        with self.lock:
            value = self.load()
            try:
                power = self.power.inspect()
            except (OSError, ValueError):
                power = {'enabled': False, 'verified': False, 'code': 'read_failed'}
            return {'required': not bool(value.get('completed_at')), 'completed_at': value.get('completed_at'),
                    'open_requested': self.open_requested,
                    'job': dict(self.job), 'subscriptions': self.subscriptions, 'accounts': self.accounts,
                    'bound_account': self.store.get('cloudflare_account_id'),
                    'deployment': byo.status(self.store), 'power': power,
                    'verification': value.get('verification'), 'key_id': value.get('key_id')}

    def task(self, name, work):
        if not self.busy.acquire(blocking=False):
            return {'ok': False, 'code': 'busy'}
        self.job = {'status': 'running', 'action': name}
        def run():
            try:
                work()
                self.job = {'status': 'completed', 'action': name}
            except Exception as error:
                # No CLI stdout/stderr/exception text or credential ever enters state/logs.
                code = 'operation_failed'
                if isinstance(error, OSError) and error.errno in {5, 13}:
                    code = 'permission_required'
                self.job = {'status': 'failed', 'action': name, 'code': code}
            finally:
                self.busy.release()
        threading.Thread(target=run, daemon=True, name='windows-onboarding-' + name).start()
        return {'ok': True, 'status': 'running'}

    def refresh(self):
        self.subscriptions = {p: providers.status(p, self.store)['ready'] for p in ('codex', 'claude')}
        try:
            self.accounts = cloud_accounts(self.store.directory)
        except (byo.SetupError, ValueError, OSError, subprocess.SubprocessError):
            self.accounts = []
        current = (self.store.get('public_url'), self.store.get('relay_enabled'))
        if current != self.deployment_identity and current[0] and current[1] and self.owner.relay:
            self.owner.relay.stop()
            self.owner.relay.start()
        self.deployment_identity = current
        if hasattr(self.owner, 'refresh_auth'):
            self.owner.refresh_auth()

    def login(self, provider):
        if provider not in {'codex', 'claude', 'cloudflare'}:
            raise ValueError()
        if provider == 'cloudflare':
            try:
                self.accounts = cloud_accounts(self.store.directory)
            except (byo.SetupError, ValueError, OSError, subprocess.SubprocessError):
                self.accounts = []
            if self.accounts:
                return  # Never overwrite an existing CLI login to select another account.
            command = byo.wrangler_command() + ['login']
            env = dict(os.environ, WRANGLER_SEND_METRICS='false')
            env.pop('CI', None)
        else:
            if providers.status(provider, self.store)['ready']:
                self.subscriptions[provider] = True
                return
            if self.owner.auth_checking:
                raise ValueError('Wait for the initial login status check.')
            with self.store.lock:
                active = self.store.db.execute("select count(*) from requests where status in ('queued','running')").fetchone()[0]
            if active:
                raise ValueError('Wait for active requests before logging in.')
            command = [providers.executable(provider, self.store)] + (['login'] if provider == 'codex' else ['auth', 'login'])
            env = providers.environment()
        previous = self.login_processes.get(provider)
        if previous and previous.poll() is None:
            return
        # Only an explicit button runs an official authentication command, never a chat/inference.
        self.login_processes[provider] = subprocess.Popen(command, env=env,
            creationflags=getattr(subprocess, 'CREATE_NEW_CONSOLE', 0), cwd=self.store.directory)

    def prompt(self):
        exe = str(stable_entry('aigo-bridge.exe'))
        directory = str(self.store.directory)
        # JSON encoded argument examples make paths with apostrophes safe to paste in PowerShell.
        def quoted(value):
            return "'" + value.replace("'", "''") + "'"
        base = '& ' + quoted(exe)
        arg = ' --data-dir ' + quoted(directory)
        account = self.store.get('cloudflare_account_id') or '<在 whoami 中由我明確選定的 32 位 account ID>'
        resources = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
        return {'prompt': f'''請協助完成這台 Windows LLM Bridge 的 BYO Cloudflare 設定。你是 AI IDE 協作者，不要呼叫 Claude/Codex 的推論 CLI 當作設定 agent。
先讀 {resources / 'docs/ONBOARDING.md'} 及 {resources / 'skills/byo-cloudflare/SKILL.md'}；有 repo 時另讀 docs/README.md。
以原設定檔為準，不使用文件歷史網址／其他人的帳戶。不要更改本機 LLM 登入、正式 Windows 電源設定、現有 endpoint、device_id 或 client KEY，不碰 Mac 或其他 Cloud 專案。
檢查 Node.js 24.22.1+（或 22.23.4+）、Wrangler 4.152.0、wrangler whoami --json。缺少時引導本人安裝與 wrangler login OAuth；不要要求 token、auth.json、DPAPI 檔或 Global API key。
使用者必須明確選定自有 account：{account}。已綁定帳戶必須相同；不能因權限不足改用別的帳戶。
先規劃：{base} byo plan --account-id <明確選定的 account ID>{arg}
展示 Worker 名稱與帳戶後，依本次本人部署授權執行：{base} byo deploy --account-id <同一 account ID>{arg}
沿用原設定檔；重試不刪除資料、不換 URL、不輪替 KEY。不要直接部署 repo 的 wrangler.jsonc 範本。
部署後：{base} byo status{arg}
回到安裝精靈按「重新檢查」並繼續建立長效 KEY、真 HTTPS 測試與複製第三方串接訊息。不要將 KEY 或原始 request/response 存成檔案、聊天報告或 git。沒有實測不可宣稱完成。'''}

    def deploy(self, account, consent):
        if consent is not True or not isinstance(account, str) or not re.fullmatch('[a-fA-F0-9]{32}', account):
            raise ValueError('Select and authorize the account first.')
        fresh = cloud_accounts(self.store.directory)
        if account.lower() not in {a['id'] for a in fresh}:
            raise ValueError('Selected account is not authorized.')
        path = byo.configure(self.store, account.lower())
        cloud = byo.Cloudflare(path, self.store.get('cloudflare_account_id'))
        byo.publish(self.store, path, cloud)
        if self.owner.relay:
            self.owner.relay.stop()
            self.owner.relay.start()
        self.deployment_identity = (self.store.get('public_url'), self.store.get('relay_enabled'))

    def action(self, action, data):
        if action in {'open', 'opened'}:
            self.open_requested = action == 'open'
            return {'ok': True}
        if action == 'cli-paths':
            for provider in ('codex', 'claude'):
                path = data.get(provider + '_path', '')
                if not isinstance(path, str) or len(path) > 32768:
                    raise ValueError()
                if path:
                    providers.executable(provider, {provider + '_path': path})
            for provider in ('codex', 'claude'):
                self.store.set(provider + '_path', data.get(provider + '_path', ''))
            return {'ok': True}
        if action == 'refresh':
            return self.task('refresh', self.refresh)
        if action == 'login':
            provider = data.get('provider')
            if provider not in {'codex', 'claude', 'cloudflare'}:
                raise ValueError()
            return self.task('login-' + provider, lambda: self.login(provider))
        if action == 'prompt':
            return self.prompt()
        if action in {'power', 'power-admin'}:
            if data.get('consent') is not True:
                raise ValueError('Explicit AC automatic-sleep consent is required.')
            def apply():
                result = self.apply_power(admin=action == 'power-admin')
                if not result['verified']:
                    raise ValueError('Power readback failed.')
                with self.lock:
                    value = self.load()
                    value['power_consent'] = True
                    self.save(value)
            return self.task('power', apply)
        if action == 'restore-power-admin':
            if data.get('consent') is not True:
                raise ValueError()
            return self.task('restore-power', lambda: self.restore_power(admin=True))
        if action == 'restore-power':
            return self.task('restore-power', self.restore_power)
        if action == 'deploy':
            account, consent = data.get('account_id'), data.get('consent')
            return self.task('deploy', lambda: self.deploy(account, consent))
        if action == 'create-key':
            if not self.store.get('public_url') or not secret.load(self.store.directory):
                raise ValueError('Complete device pairing first.')
            label = data.get('label', 'Primary service')
            kid, key = self.store.create_key(label)  # All provider/model scopes by default.
            with self.lock:
                value = self.load()
                value.update(key_id=kid, verification=None)
                self.proof = None
                self.save(value)
            return {'id': kid, 'token': key, 'integration': integration(self.store, key=key)}
        if action == 'verify':
            key, model = data.get('key'), data.get('model')
            if not isinstance(key, str) or len(key) > 256:
                raise ValueError()
            identity = self.store.authenticate(key)
            selected = next((m for m in self.store.get('models') if m['id'] == model), None)
            if not identity or not selected or selected['provider'] not in identity['providers']:
                raise ValueError()
            target_url = self.store.get('public_url')
            def probe():
                result = verify(self.store, key, model, target_url)
                with self.lock:
                    current = next((m for m in self.store.get('models') if m['id'] == model), None)
                    if self.store.get('public_url') != target_url or current != selected:
                        result = {**result, 'success': False, 'code': 'configuration_changed'}
                    value = self.load()
                    # Only allowlisted receipt fields. Key and raw response remain in RAM.
                    value['verification'] = {**result, 'model': model, 'key_id': identity['id'], 'checked_at': time.time()}
                    if result['success']:
                        value['key_id'] = identity['id']  # Reinstall can reuse an already-saved valid key.
                    self.save(value)
                    self.proof = (identity['id'], target_url, json.dumps(selected, sort_keys=True)) if result['success'] else None
            return self.task('verify', probe)
        if action == 'finish':
            with self.lock:
                value = self.load()
                identity = next((k for k in self.store.keys() if k['id'] == value.get('key_id') and not k['revoked_ts']), None)
                model = next((m for m in self.store.get('models') if m['id'] == data.get('model')), None)
                if (data.get('key_saved') is not True or data.get('handoff_copied') is not True or not identity
                    or not model or self.proof != (identity['id'], self.store.get('public_url'), json.dumps(model, sort_keys=True))
                    or not self.power.inspect()['verified']):
                    raise ValueError('Complete power, HTTPS verification and key handoff first.')
                # Login is read-only and checked freshly; quota is established by the actual POST.
                if not providers.status(model['provider'], self.store)['ready']:
                    raise ValueError('Selected subscription is not ready.')
                value['completed_at'] = time.time()
                value['completed_version'] = self.owner.release['version']
                self.save(value)
            return {'ok': True}
        raise ValueError('Unknown onboarding action.')
