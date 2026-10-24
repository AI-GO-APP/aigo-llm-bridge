"""Mac-only opt-in Codex feasibility pilot. Never updates the installed service.

No owner key or request body is written; the report contains numeric metadata.
This is a pilot, not the #39 release gate matrix or receipt acceptance.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from desktop_bridge import providers
from desktop_bridge.codex_session import CodexSession
from desktop_bridge.contract import Inference
from desktop_bridge.errors import BridgeError
from desktop_bridge.execution_budget import Budget, scope
from desktop_bridge.store import DEFAULTS
from tools.warm_cli_pool import SingleUsePool


class Resources:
    """Sample this experiment tree only; never collect argv or process content."""
    def __init__(self):
        self.pid = os.getpid()
        self.lib = ctypes.CDLL('/usr/lib/libproc.dylib')
        self.stop = threading.Event()
        self.values = {'peak_tree_rss_kib': 0, 'peak_tree_cpu_percent_lifetime_average': 0,
                       'peak_descendants': 0, 'peak_tree_fds': 0, 'samples': 0, 'sampling_errors': 0}
        self.thread = threading.Thread(target=self.sample, daemon=True)

    def sample(self):
        while not self.stop.is_set():
            try:
                rows = [r.split() for r in subprocess.check_output(
                    ['ps', '-axo', 'pid=,ppid=,rss=,%cpu='], text=True, timeout=2).splitlines()]
                family = {self.pid}
                for _ in range(8):
                    family.update(int(r[0]) for r in rows if len(r) == 4 and int(r[1]) in family)
                owned = [r for r in rows if len(r) == 4 and int(r[0]) in family]
                for name, value in (
                    ('peak_tree_rss_kib', sum(int(r[2]) for r in owned)),
                    ('peak_tree_cpu_percent_lifetime_average', sum(float(r[3]) for r in owned)),
                    ('peak_descendants', len(owned) - 1),
                    ('peak_tree_fds', sum(self.lib.proc_pidinfo(int(r[0]), 1, 0, None, 0) // 8 for r in owned))):
                    self.values[name] = max(self.values[name], value)
                self.values['samples'] += 1
            except (OSError, ValueError, subprocess.SubprocessError):
                self.values['sampling_errors'] += 1
            self.stop.wait(.1)

    def finish(self):
        self.stop.set()
        self.thread.join(timeout=3)
        return self.values | {'cpu_kind': 'ps lifetime-average sampled maximum; 100% is one logical core',
                              'includes': 'experiment, all owned descendants, refill and sampler ps process'}


from desktop_bridge.warm_runtime import CodexResource as Resource

def settings_from_install(root):
    manifest = json.loads((root / 'source-install.json').read_text())
    # Read only selected nonsecret settings. No Store migrations or profile writes.
    connection = sqlite3.connect((Path(manifest['data_dir']) / 'bridge.sqlite').as_uri() + '?mode=ro', uri=True)
    try:
        settings = {name: DEFAULTS[name] for name in ('codex_path', 'timeout_s')}
        for name, raw in connection.execute("select name,value from settings where name in ('codex_path','timeout_s')"):
            settings[name] = json.loads(raw)
        return settings, manifest['version']
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Start owned CLIs; requests consume subscription usage.')
    parser.add_argument('--install-root', type=Path, default=Path.home() / 'Library/Application Support/AIGO LLM Bridge')
    parser.add_argument('--idle-seconds', type=float, default=600)
    parser.add_argument('--requests', type=int, default=3, help='Synthetic requests per cold/warm arm; 0 means idle only.')
    parser.add_argument('--resident', type=int, default=2)
    parser.add_argument('--concurrency', type=int, default=8)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if (not args.apply or sys.platform != 'darwin' or not 0 <= args.requests <= 100
            or not 0 <= args.idle_seconds <= 600 or not 0 <= args.resident <= args.concurrency <= 64
            or args.concurrency < 1):
        parser.error('Require Mac, --apply, requests 0–100, idle 0–600, 0 <= resident <= concurrency <= 64.')
    settings, installed_version = settings_from_install(args.install_root)
    settings['timeout_s'] = min(settings['timeout_s'], 90)
    cancel = threading.Event()
    report = {'schema': 1, 'experiment': 'single-use Codex initialize-only pilot',
        'installed_version': installed_version, 'production_changed': False, 'release_gates_passed': False,
        'resident': args.resident, 'concurrency': args.concurrency, 'automatic_inference_retries': 0,
        'raw_content_saved': False, 'rows': [], 'source_sha256': {
            str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT/'desktop_bridge/providers.py', ROOT/'desktop_bridge/codex_session.py',
                      ROOT/'tools/warm_cli_pool.py', Path(__file__).resolve())}}
    report['cli_version'] = subprocess.run([providers.executable('codex',settings),'--version'],
        capture_output=True, text=True, timeout=10, env=providers.environment(), check=True).stdout.strip()
    created = []
    def factory(stop, deadline):
        resource = Resource(settings, stop, deadline)
        created.append(resource)
        return resource
    def save():
        args.output.write_text(json.dumps(report, indent=2) + '\n')
    pool = None
    experiment_start = time.monotonic()
    resources = Resources()
    resources.thread.start()
    try:
        pool = SingleUsePool(factory, lambda: providers.auth_generation('codex', settings),
            target=args.resident, limit=args.concurrency, ttl=600)
        until = time.monotonic() + max(15, args.resident * 4)
        while pool.snapshot()['idle'] < args.resident:
            if time.monotonic() >= until:
                raise BridgeError(503, 'warm_not_ready', '待命握手未就緒。')
            time.sleep(.05)
        started = time.monotonic()
        while time.monotonic() - started < args.idle_seconds:
            if any(r.session.idle_work_events or r.session.sent['turn/start'] for r in created):
                raise BridgeError(503, 'idle_inference', '待命時不可推論。')
            time.sleep(.1)
        report['idle'] = {'seconds': round(time.monotonic() - started, 3),
            'thread_starts': sum(r.session.sent['thread/start'] for r in created),
            'turn_starts': sum(r.session.sent['turn/start'] for r in created),
            'work_events': sum(r.session.idle_work_events for r in created)}
        # Alternate paired arms to expose first-run/network effects. Prewarm/refill
        # costs are included in the full experiment wall time and process counts.
        for index in range(args.requests):
            for arm in ('cold', 'warm') if index % 2 == 0 else ('warm', 'cold'):
                pool.pause()
                until = time.monotonic() + 5
                while pool.snapshot()['total']:
                    if time.monotonic() >= until:
                        raise BridgeError(503, 'warm_not_drained', '待命池未排空。')
                    time.sleep(.05)
                pool.configure(args.resident if arm == 'warm' else 0, args.concurrency)
                pool.resume()
                until = time.monotonic() + max(15, args.resident * 4)
                while arm == 'warm' and pool.snapshot()['idle'] < args.resident:
                    if time.monotonic() >= until:
                        raise BridgeError(503, 'warm_not_ready', '待命握手未就緒。')
                    time.sleep(.05)
                marker = f'PILOT_{index:03d}'
                spec = Inference({'provider': 'codex', 'native': 'gpt-6.1-sol', 'id': 'openai/gpt-6.1-sol'},
                    [{'role': 'user', 'parts': [{'type': 'text', 'text': 'Return exactly ' + marker}]}],
                    'Return the requested synthetic marker and nothing else.', None, 'text', None)
                budget = Budget(time.monotonic() + settings['timeout_s'], cancel)
                began = time.monotonic()
                row = {'arm': arm, 'index': index}
                report['rows'].append(row)
                try:
                    with scope(budget):
                        with pool.lease(cancel, budget.until) as resource:
                            result = providers.call_codex(spec, settings, cancel, resource.cwd, session=resource.session)
                    text, usage, _, model = result
                    row.update(correct=text.strip() == marker, model_match=model == spec.model['native'],
                               usage={k: v for k, v in usage.items() if k in {'prompt_tokens', 'completion_tokens',
                                   'prompt_tokens_details', 'completion_tokens_details'}})
                except BridgeError as error:
                    row.update(correct=False, error_category=error.category)
                finally:
                    row.update(seconds=round(time.monotonic() - began, 4), timings_ms=budget.metadata())
                    save()
        report['experiment_wall_seconds_including_idle_refill'] = round(time.monotonic() - experiment_start, 4)
    except BridgeError as error:
        report['error_category'] = error.category
    finally:
        began = time.monotonic()
        if pool:
            report['pool'] = pool.snapshot()
            try:
                pool.close()
            except Exception:
                report['error_category'] = 'cleanup_failed'
            report['after_close'] = pool.snapshot()
        report['handshake_seconds_total'] = round(sum(r.handshake_seconds for r in created),4)
        report['cleanup_seconds'] = round(time.monotonic() - began, 4)
        report['owned_clis_stopped'] = all(r.session.child.proc.poll() is not None for r in created)
        report['owned_cwds_removed'] = all(not Path(r.cwd).exists() for r in created)
        report['resources'] = resources.finish()
        report['single_request_summary'] = {
            arm: {'requests': len(rows), 'correct': sum(r.get('correct',False) for r in rows),
                  'median_seconds': statistics.median(r['seconds'] for r in rows) if rows else None}
            for arm in ('cold','warm') if (rows := [r for r in report['rows'] if r['arm']==arm])}
        save()
    print(json.dumps({key: report[key] for key in ('release_gates_passed', 'cleanup_seconds',
                                                  'owned_clis_stopped', 'owned_cwds_removed')}))
    return int('error_category' in report or any(not r.get('correct') for r in report['rows']))


if __name__ == '__main__':
    raise SystemExit(main())
