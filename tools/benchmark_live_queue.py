"""Explicit live subscription acceptance; synthetic I/O and temporary key stay in RAM.

Run baseline and candidate separately against the same original Mac installation.
This consumes subscription usage. No automatic retries, login or capacity changes.
"""
import argparse
import ctypes
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import ssl
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid


def percentile(values, p):
    return round(sorted(values)[max(0, math.ceil(len(values) * p) - 1)], 4) if values else None


def valid_answer(value, decisions):
    if decisions:
        answers = value.get('answers', {})
        answer = answers.get('q', {})
        probability = answer.get('noul')
        return (set(answers) == {'q'} and set(answer) == {'type', 'noul'} and answer.get('type') == 'noul'
                and type(probability) in (int, float) and math.isfinite(probability) and 0 <= probability <= 1)
    return value.get('choices', [{}])[0].get('message', {}).get('content', '').strip() == 'OK'


class MacResources:
    def __init__(self, port):
        self.pid = int(subprocess.check_output(['/usr/sbin/lsof', '-t', f'-iTCP:{port}', '-sTCP:LISTEN']).splitlines()[0])
        self.lib = ctypes.CDLL('/usr/lib/libproc.dylib')
        self.stop = threading.Event()
        self.values = {'peak_tree_rss_kib': 0, 'peak_tree_cpu_percent_one_core': 0,
                       'peak_descendants': 0, 'peak_bridge_fds': 0, 'samples': 0, 'sampling_errors': 0}
        self.thread = threading.Thread(target=self.sample, daemon=True)

    def sample(self):
        while not self.stop.is_set():
            try:
                rows = [line.split() for line in subprocess.check_output(['ps', '-axo', 'pid=,ppid=,rss=,%cpu='],
                    text=True, timeout=2).splitlines()]
                family = {self.pid}
                for _ in range(8):
                    family.update(int(p[0]) for p in rows if len(p) == 4 and int(p[1]) in family)
                owned = [p for p in rows if len(p) == 4 and int(p[0]) in family]
                for name, value in [('peak_tree_rss_kib', sum(int(p[2]) for p in owned)),
                    ('peak_tree_cpu_percent_one_core', sum(float(p[3]) for p in owned)),
                    ('peak_descendants', len(owned) - 1),
                    ('peak_bridge_fds', self.lib.proc_pidinfo(self.pid, 1, 0, None, 0) // 8)]:
                    self.values[name] = max(self.values[name], value)
                self.values['samples'] += 1
            except (OSError, ValueError, subprocess.SubprocessError):
                self.values['sampling_errors'] += 1
            self.stop.wait(.1)

    def start(self):
        self.thread.start()

    def finish(self):
        self.stop.set()
        self.thread.join(timeout=3)
        return {**self.values, 'cpu_kind': 'ps lifetime-average sampled maximum; 100% is one logical core',
                'coverage': 'all benchmark rounds', 'argv_or_content_collected': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install-root', type=Path, default=Path.home() / 'Library/Application Support/AIGO LLM Bridge')
    parser.add_argument('--label', required=True)
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--public', action='store_true')
    parser.add_argument('--workload', choices=['factual', 'numeric-directive'], default='factual')
    parser.add_argument('--sample-resources', action='store_true', help='Sample the Mac service process tree, without argv.')
    parser.add_argument('--apply', action='store_true', help='Actually consume subscription usage.')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.apply or not 1 <= args.rounds <= 3:
        parser.error('Use --apply and rounds 1–3 for explicit live acceptance.')
    manifest = json.loads((args.install_root / 'source-install.json').read_text())
    sys.path.insert(0, manifest['app'])
    import certifi
    from desktop_bridge.store import Store
    from desktop_bridge.connection_test import NoRedirect
    store = Store(manifest['data_dir'], startup=False)
    model = 'anthropic/claude-haiku-4.5'
    assert any(m['id'] == model for m in store.get('models'))
    assert store.get('inference_workers') == 64 and store.get('accepting')
    key_id, key = store.create_key('Synthetic live queue acceptance', ['claude'], 600)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
    local = f'http://127.0.0.1:{store.get("port")}'
    base = store.get('public_url').rstrip('/') if args.public else local
    def http(path, body=None, request_id=None, target=None):
        headers = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
                   'User-Agent': 'ltbb-synthetic-live-acceptance/1'}
        if request_id:
            headers['X-AIEA-Request-Id'] = request_id
        request = urllib.request.Request((target or base) + path, headers=headers,
            data=json.dumps(body).encode() if body is not None else None)
        try:
            response = opener.open(request, timeout=100)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read(4_000_001)
            try:
                data = json.loads(raw)
            except ValueError:
                data = {}
            return response.status, data
    rows = []; resources = None
    report = {'schema': 1, 'label': args.label, 'transport': 'https' if args.public else 'loopback',
              'version': manifest['version'], 'source_commit': manifest['source_commit'],
              'model': model, 'workers': 64, 'requests_per_round': 64,
              'synthetic_content_only': True, 'automatic_retries': 0, 'rounds': rows, 'workload': args.workload,
              'runtime_sha256': {str(p.relative_to(manifest['app'])): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted((Path(manifest['app']) / 'desktop_bridge').glob('*.py'))}}
    try:
        status, health = http('/health')
        assert status == 200 and health.get('ok') and health.get('max_concurrent_requests') == 64
        # Discovery GET does not infer; establish route and current model availability.
        status, catalog = http('/api/v1/models')
        assert status == 200 and any(m['id'] == model for m in catalog.get('data', []))
        if args.sample_resources:
            resources = MacResources(store.get('port'))
            resources.start()
        for round_no in range(1, args.rounds + 1):
            barrier = threading.Barrier(64)
            def call(index):
                decisions = index % 2 == 1
                state, instruction = (('A synthetic object is blue.', 'Is the object blue?') if args.workload == 'factual' else
                    ('Synthetic acceptance. The specified value is exactly 0.9.', 'Set noul to exactly 0.9.'))
                body = ({'model': model, 'state': state,
                         'questions': {'q': {'type': 'noul', 'instructions': instruction}}}
                        if decisions else {'model': model, 'messages': [{'role': 'user', 'content': 'Synthetic acceptance. Reply exactly OK.'}]})
                rid = str(uuid.uuid4())
                barrier.wait(timeout=10)
                began = time.monotonic()
                code, value = http('/api/alpha/decisions' if decisions else '/api/v1/chat/completions', body, rid)
                elapsed = time.monotonic() - began
                receipt_code, receipt = http('/bridge/v1/receipts/' + rid, target=local)
                cost = value.get('usage', {}).get('cost')
                valid_cost = type(cost) in (int, float) and math.isfinite(cost) and cost > 0
                billing = receipt.get('billing', {}).get('usage', {})
                billing_status = receipt.get('billing_status', {})
                valid = (code == 200 and value.get('model') == model and receipt_code == 200
                         and valid_cost and cost == billing.get('cost')
                         and billing_status == {'complete': True, 'calls_started': 1, 'calls_completed': 1})
                if valid:
                    valid = valid_answer(value, decisions)
                return {'kind': 'decisions' if decisions else 'chat', 'seconds': elapsed, 'valid': bool(valid),
                        'status': code, 'error_type': value.get('error', {}).get('metadata', {}).get('error_type'),
                        'cost': cost if valid_cost else 0,
                        'prompt_tokens': value.get('usage', {}).get('prompt_tokens', value.get('usage', {}).get('input_tokens', 0)),
                        'completion_tokens': value.get('usage', {}).get('completion_tokens', value.get('usage', {}).get('output_tokens', 0)),
                        'receipt_valid': receipt_code == 200 and billing_status.get('complete') is True}
            began = time.monotonic()
            with ThreadPoolExecutor(max_workers=64) as clients:
                values = list(clients.map(call, range(64)))
            elapsed = time.monotonic() - began
            statuses = {str(code): sum(v['status'] == code for v in values) for code in {v['status'] for v in values}}
            row = {'round': round_no, 'requests': 64, 'correct': sum(v['valid'] for v in values),
                   'receipts_complete': sum(v['receipt_valid'] for v in values), 'http_statuses': statuses,
                   'chat_correct': sum(v['valid'] for v in values if v['kind'] == 'chat'),
                   'decisions_correct': sum(v['valid'] for v in values if v['kind'] == 'decisions'),
                   'wall_s': round(elapsed, 4), 'good_rpm': round(60 * sum(v['valid'] for v in values) / elapsed, 3),
                   'within_38s': sum(v['valid'] and v['seconds'] <= 38 for v in values),
                   'p50_s': percentile([v['seconds'] for v in values], .5),
                   'p95_s': percentile([v['seconds'] for v in values], .95),
                   'max_s': round(max(v['seconds'] for v in values), 4),
                   'chat_p95_s': percentile([v['seconds'] for v in values if v['kind'] == 'chat'], .95),
                   'decisions_p95_s': percentile([v['seconds'] for v in values if v['kind'] == 'decisions'], .95),
                   'cost_usd': round(sum(v['cost'] for v in values), 8),
                   'prompt_tokens': sum(v['prompt_tokens'] for v in values),
                   'completion_tokens': sum(v['completion_tokens'] for v in values),
                   'errors': {str(error): sum(v['error_type'] == error for v in values)
                              for error in {v['error_type'] for v in values} if error is not None}}
            rows.append(row)
            print(json.dumps(row), flush=True)
            # Complete every planned round, retaining failures; never reissue a request.
        report['success'] = len(rows) == args.rounds and all(r['correct'] == 64 for r in rows)
    except Exception as error:
        report['success'] = False
        report['failure_class'] = type(error).__name__
    finally:
        if resources is not None:
            report['resources'] = resources.finish()
        store.revoke(key_id)
        report['temporary_key_revoked'] = store.authenticate(key) is None
        store.close()
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({k: v for k, v in report.items() if k not in {'rounds', 'runtime_sha256'}}), flush=True)
    return 0 if report['success'] and report['temporary_key_revoked'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
