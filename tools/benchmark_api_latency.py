"""Opt-in small-token public Chat/Decisions acceptance; synthetic content in RAM.

No inference retry. Keys are temporary, retained only in RAM, revoked in finally.
Reports are fixed numeric/boolean metadata; never record response text or events.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import ssl
import statistics
import sys
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def valid(value, model, protocol):
    if value.get('model') != model:
        return False
    if protocol == 'chat':
        return value.get('choices', [{}])[0].get('message', {}).get('content', '').strip() == 'OK'
    answer = value.get('answers', {}).get('q', {})
    probability = answer.get('noul')
    return (set(value.get('answers', {})) == {'q'} and answer.get('type') == 'noul'
            and type(probability) in (int, float) and math.isfinite(probability) and 0 <= probability <= 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--install-root', type=Path, default=Path.home() / 'Library/Application Support/AIGO LLM Bridge')
    parser.add_argument('--label', required=True)
    parser.add_argument('--provider', choices=['both','codex','claude'], default='both')
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.apply or not 1 <= args.rounds <= 3 or len(args.label) > 60:
        parser.error('Require --apply, rounds 1–3 and label <=60 characters.')
    import certifi
    from desktop_bridge.store import Store
    from desktop_bridge.connection_test import NoRedirect
    from desktop_bridge.execution_budget import TIMING_COLUMNS
    manifest = json.loads((args.install_root / 'source-install.json').read_text())
    store = Store(manifest['data_dir'], startup=False)
    def snapshot():
        with store.lock:
            return (store.db.execute('select name,value from settings order by name').fetchall(),
                    store.db.execute('select * from api_keys order by id').fetchall())
    before_settings, before_keys = snapshot()
    kid, key = store.create_key('Synthetic API latency acceptance', ['claude', 'codex'], 60)
    base = store.get('public_url').rstrip('/')
    report = {'schema': 1, 'label': args.label, 'version': manifest['version'],
        'source_commit': manifest['source_commit'], 'transport': 'public HTTPS', 'rounds': args.rounds,
        'inference_retries': 0, 'concurrent_requests': 1, 'warm_pool_enabled': store.get('inference_resident') > 0,
        'resident': store.get('inference_resident'), 'workers': store.get('inference_workers'),
        'raw_content_saved': False, 'rows': [],
        'runtime_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted((Path(manifest['app']) / 'desktop_bridge').glob('*.py'))}}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
    def http(path, body=None, rid=None):
        headers = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
                   'User-Agent': 'ltbb-small-latency-acceptance/1'}
        if rid:
            headers['X-AIEA-Request-Id'] = rid
        request = urllib.request.Request(base + path, headers=headers,
            data=json.dumps(body).encode() if body is not None else None)
        try:
            response = opener.open(request, timeout=100)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read(4_000_001)
            try:
                value = json.loads(raw)
            except ValueError:
                value = {}
            return response.status, value if isinstance(value, dict) else {}
    success = False
    try:
        if not base.startswith('https://') or not store.get('accepting'):
            raise ValueError('Selected installation is not ready.')
        until = time.monotonic() + 40
        while True:
            code, catalog = http('/api/v1/models')
            if code != 401 or time.monotonic() >= until:
                break
            time.sleep(.5)  # Key-digest propagation: read-only, no inference.
        models = [m for m in ['openai/gpt-6.1-sol', 'anthropic/claude-haiku-4.5']
                  if args.provider=='both' or m.startswith('openai/' if args.provider=='codex' else 'anthropic/')]
        report['models_http'] = code
        if code != 200 or not set(models) <= {m['id'] for m in catalog.get('data', [])}:
            raise ValueError('Required models are not available.')
        for round_no in range(1, args.rounds + 1):
            for model in models if round_no % 2 else list(reversed(models)):
                for protocol in ('chat', 'decisions'):
                    body = ({'model': model, 'messages': [{'role': 'user', 'content': 'Reply exactly OK.'}],
                             'stream': False} if protocol == 'chat' else
                            {'model': model, 'state': 'A synthetic object is blue.',
                             'questions': {'q': {'type': 'noul', 'instructions': 'Is the object blue?'}}})
                    path = '/api/v1/chat/completions' if protocol == 'chat' else '/api/alpha/decisions'
                    rid = str(uuid.uuid4())
                    row = {'round': round_no, 'model': model, 'protocol': protocol,
                           'request_bytes': len(json.dumps(body).encode())}
                    report['rows'].append(row)
                    if report['warm_pool_enabled'] and model.startswith('openai/'):
                        ready_until=time.monotonic()+15
                        while True:
                            with opener.open('http://127.0.0.1:'+str(store.get('port'))+'/health',timeout=2) as response:
                                health=json.load(response)
                            pool=health.get('warm_pool',{})
                            if pool.get('idle',0)>=report['resident']:break
                            if time.monotonic()>=ready_until:raise ValueError('Resident pool not ready.')
                            time.sleep(.05)
                        row['ready_residents_before']=pool['idle']
                    began = time.monotonic()
                    try:
                        code, value = http(path, body, rid)
                        row.update(http=code, seconds=round(time.monotonic() - began, 4),
                                   response_valid=code == 200 and valid(value, model, protocol))
                        usage = value.get('usage', {})
                        cost = usage.get('cost')
                        receipt_code, receipt = http('/bridge/v1/receipts/' + rid)
                        row['execution']=receipt.get('execution',{})
                        row['lease_valid']=(row['execution'].get('warm_hits')==int(report['warm_pool_enabled'] and model.startswith('openai/'))
                            and row['execution'].get('cold_starts')==int(not report['warm_pool_enabled'] or not model.startswith('openai/')))
                        row.update(receipt_http=receipt_code,
                            receipt_complete=receipt.get('billing_status') == {
                                'complete': True, 'calls_started': 1, 'calls_completed': 1},
                            cost_matches=(type(cost) in (int, float) and math.isfinite(cost) and cost >= 0
                                and cost == receipt.get('billing', {}).get('usage', {}).get('cost')))
                        for field, alternatives in [('prompt_tokens', ('prompt_tokens', 'input_tokens')),
                            ('completion_tokens', ('completion_tokens', 'output_tokens')), ('cost_usd', ('cost',))]:
                            number = next((usage[k] for k in alternatives if k in usage), None)
                            row[field] = number if type(number) in (int, float) and math.isfinite(number) else None
                        with store.lock:
                            record = store.db.execute('select '+','.join(TIMING_COLUMNS)+
                                ' from requests where key_id=? and client_request_id=?', (kid, rid)).fetchone()
                            row['timings_ms'] = dict(record) if record is not None else {}
                        row['passed'] = row['lease_valid'] and row['response_valid'] and row['receipt_complete'] and row['cost_matches']
                    except Exception:
                        row.update(passed=False, transport_or_validation_error=True,
                                   seconds=round(time.monotonic() - began, 4))
                    args.output.write_text(json.dumps(report, indent=2) + '\n')
                    # Preserve the failed attempt, do not replace it with a retry.
                    if not row['passed']:
                        raise ValueError('Synthetic inference acceptance failed.')
        success = True
    except Exception:
        report['incomplete'] = True
    finally:
        store.revoke(kid)
        report['temporary_key_revoked'] = store.authenticate(key) is None
        after_settings, after_keys = snapshot()
        report['settings_preserved'] = [tuple(r) for r in before_settings] == [tuple(r) for r in after_settings]
        report['owner_keys_preserved'] = [tuple(r) for r in before_keys] == [tuple(r) for r in after_keys if r[0] != kid]
        report['summary'] = []
        for model in ('openai/gpt-6.1-sol', 'anthropic/claude-haiku-4.5'):
            for protocol in ('chat', 'decisions'):
                rows = [r for r in report['rows'] if r['model'] == model and r['protocol'] == protocol]
                if rows:
                    report['summary'].append({'model': model, 'protocol': protocol, 'requests': len(rows),
                        'passed': sum(r.get('passed', False) for r in rows),
                        'median_seconds': round(statistics.median(r['seconds'] for r in rows), 4),
                        'max_seconds': max(r['seconds'] for r in rows)})
        report['success'] = (success and report['temporary_key_revoked'] and report['settings_preserved']
                             and report['owner_keys_preserved'])
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        store.close()
    print(json.dumps({k: report[k] for k in ('success', 'version', 'summary', 'temporary_key_revoked',
                                           'settings_preserved', 'owner_keys_preserved')}))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
