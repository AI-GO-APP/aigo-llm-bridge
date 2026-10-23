"""Explicit live Mac source update acceptance. Synthetic requests and temporary key, RAM only."""
import argparse
import json
import math
from pathlib import Path
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import certifi
from desktop_bridge.store import Store
from desktop_bridge.connection_test import NoRedirect


def emit(name, **metadata):
    print(json.dumps({'check': name, **metadata}, ensure_ascii=False), flush=True)


def locked():
    result = subprocess.run(['/usr/sbin/ioreg', '-n', 'Root', '-d1'], capture_output=True, text=True)
    return '"CGSSessionScreenIsLocked"=Yes' in result.stdout


def snapshot(store):
    return {'settings': {name: store.get(name) for name in ('device_id', 'public_url', 'cloudflare_account_id',
            'cloudflare_worker_name', 'models', 'default_model', 'inference_workers', 'relay_enabled')},
            'keys': store.db.execute('select * from api_keys order by id').fetchall()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install-root', default=str(Path.home() / 'Library/Application Support/AIGO LLM Bridge'))
    parser.add_argument('--apply', action='store_true', help='Actually update the selected existing source installation.')
    args = parser.parse_args()
    if not args.apply:
        parser.error('Live update requires explicit --apply.')
    root = Path(args.install_root).expanduser().resolve()
    original = json.loads((root / 'source-install.json').read_text())
    store = Store(original['data_dir'], startup=False)
    before = snapshot(store)
    key_id, key = store.create_key('Mac source upgrade acceptance', ['codex'], 60)
    base = store.get('public_url').rstrip('/')
    model = next(m['id'] for m in store.get('models') if m['provider'] == 'codex')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
    def http(path, body=None, request_id=None):
        headers = {'Authorization': 'Bearer ' + key, 'User-Agent': 'aigo-llm-bridge-macos-acceptance/1',
                   'Content-Type': 'application/json'}
        if request_id:
            headers['X-AIEA-Request-Id'] = request_id
        request = urllib.request.Request(base + path, headers=headers,
            data=json.dumps(body).encode() if body is not None else None)
        try:
            with opener.open(request, timeout=120 if body is not None else 25) as response:
                return response.status, json.loads(response.read(4_000_001))
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read(65536))
    def models():
        until = time.monotonic() + 40
        while True:
            code, value = http('/api/v1/models')
            if code != 401 or time.monotonic() >= until:
                return code, value
            time.sleep(1)
    checks = []
    def check(name, success, **metadata):
        checks.append(bool(success)); emit(name, passed=bool(success), **metadata)
        if not success:
            raise ValueError('Acceptance failed: ' + name)
    try:
        code, value = models()
        check('original_key_before_update', code == 200 and any(m['id'] == model for m in value.get('data', [])), http=code)
        # Keep this same temporary key across update; owner service keys remain untouched.
        expected = snapshot(store)
        result = subprocess.run([sys.executable, str(ROOT / 'tools/mac_service.py'), 'update',
            '--install-root', str(root), '--source', str(ROOT)], capture_output=True, timeout=420)
        check('source_update', result.returncode == 0)
        current = json.loads((root / 'source-install.json').read_text())
        after = snapshot(store)
        check('device_keys_models_capacity_preserved', after == expected,
              version=current['version'], inference_workers=store.get('inference_workers'))
        code, value = models()
        check('same_key_after_update', code == 200 and len(value.get('data', [])) == len(store.get('models')), http=code)
        screen_before = locked()
        body = {'model': model, 'messages': [{'role': 'user', 'content': 'Synthetic check. Reply exactly PONG.'}], 'stream': False}
        request_id = str(uuid.uuid4()); started = time.monotonic()
        code, value = http('/api/v1/chat/completions', body, request_id)
        usage = value.get('usage', {}); cost = usage.get('cost')
        content = value.get('choices', [{}])[0].get('message', {}).get('content')
        check('https_chat_cost_locked', code == 200 and isinstance(content, str) and content.strip() == 'PONG'
              and type(cost) in (int, float) and math.isfinite(cost) and cost >= 0,
              http=code, seconds=round(time.monotonic() - started, 3), locked_before=screen_before,
              locked_after=locked(), cost_usd=cost, model=value.get('model'))
        first_id = value.get('id')
        count = store.db.execute('select count(*) from requests').fetchone()[0]
        code, value = http('/api/v1/chat/completions', body, request_id)
        check('deduplicated_same_request', code == 200 and value.get('id') == first_id
              and store.db.execute('select count(*) from requests').fetchone()[0] == count)
        structured = {**body, 'messages': [{'role': 'user', 'content': 'Synthetic JSON check. Return status ok.'}],
            'response_format': {'type': 'json_schema', 'json_schema': {'name': 'probe', 'strict': True, 'schema': {
                'type': 'object', 'properties': {'status': {'type': 'string', 'enum': ['ok']}},
                'required': ['status'], 'additionalProperties': False}}}}
        code, value = http('/api/v1/chat/completions', structured, str(uuid.uuid4()))
        content = value.get('choices', [{}])[0].get('message', {}).get('content', '{}')
        check('https_structured_output', code == 200 and json.loads(content) == {'status': 'ok'}, http=code)
        tool = {**body, 'messages': [{'role': 'user', 'content': 'Propose synthetic_ping with status ok. Do not execute anything.'}],
            'tools': [{'type': 'function', 'function': {'name': 'synthetic_ping', 'parameters': {
                'type': 'object', 'properties': {'status': {'type': 'string', 'enum': ['ok']}},
                'required': ['status'], 'additionalProperties': False}}}],
            'tool_choice': {'type': 'function', 'function': {'name': 'synthetic_ping'}}, 'parallel_tool_calls': False}
        code, value = http('/api/v1/chat/completions', tool, str(uuid.uuid4()))
        calls = value.get('choices', [{}])[0].get('message', {}).get('tool_calls', [])
        check('https_tool_proposal_only', code == 200 and len(calls) == 1
              and calls[0]['function']['name'] == 'synthetic_ping'
              and json.loads(calls[0]['function']['arguments']) == {'status': 'ok'}, http=code)
        code, value = http('/api/v1/chat/completions', {**body, 'temperature': .2})
        check('unsupported_parameter', code == 400 and value.get('error', {}).get('metadata', {}).get('error_type') == 'unsupported_parameter', http=code)
        from desktop_bridge.handoff import integration
        handoff = integration(store, model, key=key)
        check('handoff_complete', key in handoff['prompt'] and handoff['contains_key'] and handoff['config']['model'] == model)
        emit('completed', passed=all(checks), owner_service_keys_preserved=True)
        return 0
    finally:
        store.revoke(key_id)
        check_revoked = store.authenticate(key) is None
        remaining = snapshot(store)
        owner_keys = [row for row in remaining['keys'] if row[0] != key_id]
        # Compare tuples, because sqlite3.Row equality also preserves all original metadata.
        owner_preserved = [tuple(r) for r in owner_keys] == [tuple(r) for r in before['keys']]
        emit('temporary_key_revoked', passed=check_revoked, owner_service_keys_preserved=owner_preserved)
        store.close()


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        # Exceptions may embed URLs or response text; only a fixed diagnostic is printed.
        emit('incomplete', passed=False, notice='Inspect allowlisted metadata; no inference was automatically retried.')
        raise SystemExit(1)
