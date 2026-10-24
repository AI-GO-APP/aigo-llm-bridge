"""Bounded 64 x near-3 MB synthetic queue stress; no subscription CLI or owner profile."""
import argparse
import gc
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import weakref

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop_bridge.service import Runtime
from desktop_bridge.store import Store
from desktop_bridge.errors import BridgeError


def rss():
    return int(subprocess.check_output(['ps', '-o', 'rss=', '-p', str(os.getpid())]).strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = {'synthetic_only': True, 'rounds': [], 'rss_kind': 'sampled current process RSS; allocator may retain freed pages'}
    with tempfile.TemporaryDirectory(prefix='ltbb-queue-memory-') as directory:
        store = Store(directory)
        key_id, key = store.create_key('synthetic memory acceptance')
        caller = store.authenticate(key)
        release = threading.Event()
        started = threading.Event()
        def runner(spec, settings, cancel):
            started.set()
            assert release.wait(30)
            return 'OK', {'prompt_tokens': 1, 'completion_tokens': 1}, 'stop'
        runtime = Runtime(store, runner, max_workers=1, max_pending=64)
        real = runtime.validate_request
        references = []
        def observe(*args):
            spec = real(*args)
            references.append(weakref.ref(spec))
            return spec
        runtime.validate_request = observe
        try:
            for round_no in range(1, 4):
                references.clear()
                tasks = []
                release.clear()
                started.clear()
                before = rss()
                peak = before
                for index in range(64):
                    body = {'model': 'openai/gpt-6-astra', 'messages': [{'role': 'user', 'content': str(index) + 'S' * 2_999_000}]}
                    byte_count = len(json.dumps(body).encode())
                    assert 2_999_000 < byte_count < 3_000_000
                    tasks.append(runtime.submit(body, caller, byte_count))
                    del body
                    peak = max(peak, rss())
                assert started.wait(1) and runtime.capacity()['queued_requests'] == 63
                try:
                    runtime.submit({'messages': [{'role': 'user', 'content': 'synthetic'}]}, caller, 20)
                except BridgeError as error:
                    assert error.status == 429
                else:
                    raise AssertionError('65th admission must fail')
                began = time.monotonic()
                for task in tasks[1:]:
                    task.cancel.set()
                assert all(task.done.wait(1) for task in tasks[1:])
                cancellation_seconds = time.monotonic() - began
                gc.collect()
                assert all(ref() is None for ref in references[1:]) and not runtime.waiting
                assert all(store.request(task.id, key_id)['calls_started'] == 0 for task in tasks[1:])
                release.set()
                assert tasks[0].done.wait(3)
                gc.collect()
                report['rounds'].append({'round': round_no, 'accepted': 64, 'max_body_bytes': byte_count,
                    'queued_specs_released': 63, 'zero_inference_cancelled': 63,
                    'cancel_seconds': round(cancellation_seconds, 4), 'rss_before_kib': before,
                    'peak_rss_kib': peak, 'rss_after_drain_kib': rss()})
            runtime.stop()
            report['owned_workers_after_stop'] = sum(t.is_alive() for t in runtime.worker_threads)
            report['queue_after_stop'] = len(runtime.waiting)
            report['success'] = report['owned_workers_after_stop'] == report['queue_after_stop'] == 0
        finally:
            release.set()
            runtime.stop()
            store.revoke(key_id)
            report['temporary_key_revoked'] = store.authenticate(key) is None
            store.close()
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
