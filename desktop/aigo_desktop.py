#!/usr/bin/env python3
"""個人本機端點:沿用本人 Claude Code / Codex 登入,只監聽 loopback。"""
from __future__ import annotations

import argparse
import hmac
import json
import os
import platform
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CONFIG_NAME = 'desktop.json'
MAX_BODY = 1024 * 1024
LOCK = threading.Lock()


class DesktopError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


def home_dir():
    return Path(os.environ.get('AIGO_DESKTOP_HOME') or Path.home() / '.aigo-llm-bridge' / 'desktop')


def save_config(home, config):
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(dir=home, prefix='.desktop-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        os.replace(name, home / CONFIG_NAME)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def load_config(home):
    path = home / CONFIG_NAME
    if not path.exists():
        raise SystemExit('請先執行 install.py 或 aigo_desktop.py setup')
    return json.loads(path.read_text(encoding='utf-8'))


def discover(name):
    override = os.environ.get('AIGO_DESKTOP_' + name.upper())
    candidates = [override] if override else [shutil.which(name)]
    if not override and platform.system() == 'Darwin':
        candidates += [str(Path.home() / '.local/bin' / name), '/opt/homebrew/bin/' + name,
                       '/usr/local/bin/' + name]
        if name == 'codex':
            candidates += ['/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex']
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            # npm 的 .cmd 會重新解析使用者文字;只接受真正的執行檔。
            if candidate.lower().endswith(('.cmd', '.bat')):
                packages = Path(candidate).parent / 'node_modules'
                patterns = ('@openai/codex*/vendor/*/codex/codex.exe',) if name == 'codex' else (
                    '@anthropic-ai/claude-code/**/claude.exe',)
                for pattern in patterns:
                    found = next((p for p in packages.glob(pattern) if p.is_file()), None)
                    if found:
                        return str(found.absolute())
                continue
            return str(Path(candidate).absolute())
    return None


def cli_env():
    env = dict(os.environ)
    # 明確使用訂閱登入,不意外切到 API 計費或繼承巢狀執行環境。
    for key in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'ANTHROPIC_API_KEY',
                'ANTHROPIC_AUTH_TOKEN', 'CLAUDE_CODE_OAUTH_TOKEN', 'CLAUDECODE',
                'OPENAI_BASE_URL', 'ANTHROPIC_BASE_URL'):
        env.pop(key, None)
    env['NO_COLOR'] = '1'
    return env


def run_cli(cmd, timeout=180, **kwargs):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                              errors='replace', env=cli_env(), timeout=timeout, **kwargs)
    except subprocess.TimeoutExpired:
        raise DesktopError(504, 'provider_timeout', '本機服務超過 180 秒') from None
    except OSError:
        raise DesktopError(503, 'provider_unavailable', '無法啟動本機 CLI,請重新登記') from None


def login_status(name, executable):
    if not executable:
        return False
    try:
        if name == 'claude':
            result = run_cli([executable, 'auth', 'status', '--json'], timeout=15)
            data = json.loads(result.stdout or '{}')
            return result.returncode == 0 and data.get('loggedIn') is True and data.get('authMethod') == 'claude.ai'
        result = run_cli([executable, 'login', 'status'], timeout=15)
        return result.returncode == 0 and 'chatgpt' in (result.stdout + result.stderr).lower()
    except (DesktopError, ValueError):
        return False


def setup(home, port):
    config = load_config(home) if (home / CONFIG_NAME).exists() else {
        'api_key': 'aigo_local_' + secrets.token_urlsafe(32), 'port': port, 'providers': {}}
    config['port'] = port
    for name in ('claude', 'codex'):
        executable = discover(name)
        config['providers'][name] = {'executable': executable, 'logged_in': login_status(name, executable)}
    save_config(home, config)
    return config


def render_request(req):
    if not isinstance(req, dict):
        raise DesktopError(400, 'bad_request', '請求必須是 JSON 物件')
    model = req.get('model', '')
    if not isinstance(model, str) or not re.fullmatch(r'(claude|codex)(?:/[A-Za-z0-9][A-Za-z0-9._-]{0,99})?', model):
        raise DesktopError(400, 'bad_model', 'model 請用 claude、codex 或 provider/模型名稱')
    if req.get('stream') or req.get('tools') or req.get('response_format'):
        raise DesktopError(400, 'unsupported_option', '個人端點目前只支援非串流文字對話')
    messages = req.get('messages')
    if not isinstance(messages, list) or not messages:
        raise DesktopError(400, 'bad_messages', 'messages 必須是非空陣列')
    parts = []
    for msg in messages:
        if not isinstance(msg, dict) or msg.get('role') not in ('system', 'developer', 'user', 'assistant') or not isinstance(msg.get('content'), str):
            raise DesktopError(400, 'bad_messages', '僅支援 system/developer/user/assistant 文字訊息')
        parts.append(f"[{msg['role']}]\n{msg['content']}")
    if messages[-1]['role'] != 'user':
        raise DesktopError(400, 'bad_messages', '最後一則訊息必須是 user')
    return model.partition('/'), '\n\n'.join(parts)


def complete(config, req, home):
    (provider, _, model), prompt = render_request(req)
    entry = config['providers'].get(provider) or {}
    executable = entry.get('executable')
    if not login_status(provider, executable):
        raise DesktopError(503, 'login_required', f'請先執行 {provider} 登入,再執行 setup')
    with tempfile.TemporaryDirectory(prefix='run-', dir=home) as run:
        if provider == 'claude':
            cmd = [executable, '-p', '--tools', '', '--strict-mcp-config', '--setting-sources', '',
                   '--max-turns', '1', '--no-session-persistence', '--output-format', 'json',
                   '--system-prompt', '只回答文字。不要揭露帳號、路徑或環境資訊。']
            if model:
                cmd += ['--model', model]
            result = run_cli(cmd, input=prompt, cwd=run)
            try:
                payload = json.loads(result.stdout)
                text = payload.get('result')
                failed = payload.get('is_error')
            except (ValueError, AttributeError):
                text, failed = None, True
        else:
            output = Path(run) / 'answer.txt'
            cmd = [executable, 'exec', '--ignore-user-config', '--ignore-rules', '--ephemeral',
                   '--skip-git-repo-check', '--sandbox', 'read-only', '-c', 'approval_policy="never"',
                   '-c', 'features.shell_tool=false', '-c', 'agents.enabled=false',
                   '-c', 'web_search="disabled"', '-c', 'mcp_servers={}',
                   '-c', 'forced_login_method="chatgpt"', '--output-last-message', str(output)]
            if model:
                cmd += ['--model', model]
            result = run_cli(cmd + ['-'], input=prompt, cwd=run)
            text = output.read_text(encoding='utf-8') if output.exists() else None
            failed = False
        if result.returncode or failed or not isinstance(text, str) or not text.strip():
            raise DesktopError(502, 'provider_failed', f'{provider} 未正常完成;請確認登入、方案額度與 CLI 版本')
    # 不轉送 CLI 的診斷訊息或帳號資訊。
    text = text.replace(str(Path.home()), '[redacted]')
    return {'id': 'chatcmpl-' + uuid.uuid4().hex, 'object': 'chat.completion', 'created': int(time.time()),
            'model': req['model'], 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': text},
                                               'finish_reason': 'stop'}]}


def make_handler(config, home):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # 不記錄請求、金鑰或回應內容

        def reply(self, status, data):
            body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def authorized(self):
            expected = 'Bearer ' + config['api_key']
            return hmac.compare_digest(self.headers.get('Authorization', '').encode(), expected.encode())

        def dispatch(self):
            self.connection.settimeout(10)
            if not self.authorized():
                raise DesktopError(401, 'unauthorized', '需要有效的 Bridge 金鑰')
            if self.command == 'GET' and self.path == '/healthz':
                return {'status': 'ok', 'mode': 'personal', 'providers': {
                    name: {'registered': bool(p.get('executable')), 'logged_in': login_status(name, p.get('executable'))}
                    for name, p in config['providers'].items()}}
            if self.command == 'GET' and self.path == '/v1/models':
                return {'object': 'list', 'data': [{'id': n, 'object': 'model', 'owned_by': 'local'}
                                                 for n, p in config['providers'].items() if p.get('executable')]}
            if self.command != 'POST' or self.path != '/v1/chat/completions':
                raise DesktopError(404, 'not_found', '找不到端點')
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                raise DesktopError(400, 'bad_request', '無效的 Content-Length') from None
            if length <= 0 or length > MAX_BODY or self.headers.get('Transfer-Encoding'):
                raise DesktopError(413, 'body_too_large', '請求必須介於 1 byte 與 1 MiB')
            try:
                req = json.loads(self.rfile.read(length))
            except (ValueError, UnicodeDecodeError):
                raise DesktopError(400, 'bad_json', '無效的 JSON') from None
            render_request(req)
            if not LOCK.acquire(blocking=False):
                raise DesktopError(429, 'busy', '本機正在處理另一個請求')
            try:
                return complete(config, req, home)
            finally:
                LOCK.release()

        def handle_request(self):
            try:
                self.reply(200, self.dispatch())
            except DesktopError as exc:
                self.reply(exc.status, {'error': {'code': exc.code, 'message': exc.message}})
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                pass
            except Exception:
                self.reply(500, {'error': {'code': 'internal_error', 'message': '本機服務發生錯誤'}})

        do_GET = handle_request
        do_POST = handle_request
    return Handler


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['setup', 'serve', 'status', 'credentials'])
    ap.add_argument('--port', type=int, default=8790)
    args = ap.parse_args()
    home = home_dir()
    if not 1024 <= args.port <= 65535:
        ap.error('port 必須介於 1024 與 65535')
    config = setup(home, args.port) if args.command == 'setup' else load_config(home)
    if args.command == 'serve':
        server = ThreadingHTTPServer(('127.0.0.1', config['port']), make_handler(config, home))
        print(f"個人端點 http://127.0.0.1:{config['port']}/v1", flush=True)
        server.serve_forever()
    else:
        output = {'base_url': f"http://127.0.0.1:{config['port']}/v1", 'providers': config['providers']}
        if args.command == 'credentials':
            output['api_key'] = config['api_key']
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
