"""Mac source setup using the same BYO/key/verification coordinator as Windows."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import uuid

from . import byo, providers
from .windows_onboarding import Onboarding as SharedOnboarding, cloud_accounts


def source_install(directory):
    for parent in Path(__file__).resolve().parents:
        path = parent / 'source-install.json'
        if path.is_file():
            value = json.loads(path.read_text())
            if Path(value['data_dir']).resolve() == Path(directory).resolve():
                return value
    return None


class Onboarding(SharedOnboarding):
    state_filename = 'macos-onboarding.json'

    def action(self, action, data):
        if action == 'finish' and self.load().get('power_consent') is not True:
            raise ValueError('Confirm the AC idle-sleep step before completion.')
        return super().action(action, data)

    def installation_identity(self):
        return uuid.uuid5(uuid.NAMESPACE_URL, 'macos-source:' + self.store.get('device_id')).hex

    def apply_power(self, admin=False):
        return self.power.apply(consent=True, admin=admin)

    def restore_power(self, admin=False):
        return self.power.restore(admin=admin)

    def login(self, provider):
        if provider not in {'codex', 'claude', 'cloudflare'}:
            raise ValueError('Unknown provider.')
        if provider == 'cloudflare':
            try:
                self.accounts = cloud_accounts(self.store.directory)
            except (byo.SetupError, OSError, ValueError, subprocess.SubprocessError):
                self.accounts = []
            if self.accounts:
                return
            command = byo.wrangler_command() + ['login']
        else:
            if providers.status(provider, self.store)['ready']:
                self.subscriptions[provider] = True
                return
            if self.owner.auth_checking:
                raise ValueError('Wait for the login status check.')
            with self.store.lock:
                active = self.store.db.execute("select count(*) from requests where status in ('queued','running')").fetchone()[0]
            if active:
                raise ValueError('Drain active Bridge requests before login.')
            command = [providers.executable(provider, self.store)] + (['login'] if provider == 'codex' else ['auth', 'login'])
        # A new terminal belongs to this explicit click; never drives existing CLI windows.
        script = 'on run argv\n tell application "Terminal"\n activate\n do script (item 1 of argv)\n end tell\nend run'
        result = subprocess.run(['/usr/bin/osascript', '-e', script, shlex.join(command)],
                                capture_output=True, timeout=30)
        if result.returncode:
            raise ValueError('Open the official login in your terminal.')

    def prompt(self):
        install = source_install(self.store.directory)
        root = Path(install['app']) if install else Path(__file__).resolve().parent.parent
        python = install['python'] if install else sys.executable
        base = shlex.join([python, str(root / 'tools/byo_setup.py')])
        args = ' --data-dir ' + shlex.quote(str(self.store.directory))
        return {'prompt': f'''請協助完成這台 macOS LLM Bridge 的 BYO Cloudflare 設定。你是 AI IDE 協作者，不要呼叫 Claude/Codex 的推論 CLI 當作設定 agent。
先讀 {root / 'docs/MACOS-SETUP.md'}、{root / 'docs/README.md'} 及 {root / 'skills/byo-cloudflare/SKILL.md'}。
沿用原 data-dir、device_id、Keychain、endpoint 及 client KEY，不更改其他電腦、Windows 或其他 Cloud 專案。
檢查 Node.js 22+、Wrangler 4.95.0、wrangler whoami --json。官方登入由本人完成，不要求 token、auth.json、Keychain 檔或 Global API key。
請本人明確選擇自有 account ID；已綁定時必須與原帳戶相同。
先規劃：{base} plan --account-id <本人選定的帳戶>{args}
展示帳戶與 Worker 名稱後，依本人本次部署授權執行：{base} deploy{args}
檢查：{base} status{args}
不要直接部署 repo 的 wrangler.jsonc，不以刪除資料、換入口或輪替 KEY 排錯。
回 Mac 安裝精靈重新檢查，交付有效長效 KEY、endpoint、模型及第三方串接訊息，按一次真 HTTPS 合成測試。
原始內容及完整 KEY 不落檔、不進報告或 Git；沒有實測不可宣稱完成。不要自動更改睡眠、鎖定或登入設定。'''}
