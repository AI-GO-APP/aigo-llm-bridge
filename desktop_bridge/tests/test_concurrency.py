import os
import subprocess
import sys
import threading
import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from desktop_bridge.errors import BridgeError
from desktop_bridge.service import Runtime, ApiServer
from desktop_bridge.store import Store


def test_schema_capacity_wait_is_cancellable_and_does_not_launch_extra_processes(monkeypatch):
    from desktop_bridge import schema_guard
    occupied = threading.BoundedSemaphore(1)
    occupied.acquire()
    monkeypatch.setattr(schema_guard, 'CAPACITY', occupied)
    cancel = threading.Event()
    with ThreadPoolExecutor(max_workers=1) as clients:
        future = clients.submit(schema_guard.run, {'schemas': [{}]}, cancel)
        assert not future.done()
        cancel.set()
        with pytest.raises(BridgeError) as error:
            future.result(timeout=2)
        assert error.value.category == 'cancelled'
    # Waiting did not consume or incorrectly release the occupied validator slot.
    assert not occupied.acquire(blocking=False)
    occupied.release()


def test_parallel_execution_capacity_and_cancel_isolation(tmp_path):
    store = Store(tmp_path)
    _, key = store.create_key("parallel-test")
    caller = store.authenticate(key)
    release = threading.Event()
    running = threading.Event()
    lock = threading.Lock()
    entered = 0

    def runner(spec, settings, cancel):
        nonlocal entered
        with lock:
            entered += 1
            if entered == 3:
                running.set()
        assert release.wait(5)
        if cancel.is_set():
            raise BridgeError(499, "cancelled", "cancelled")
        return "OK", {"prompt_tokens": 2, "completion_tokens": 1}, "stop"

    rt = Runtime(store, runner, max_workers=3, max_pending=4)
    body = {"messages": [{"role": "user", "content": "synthetic"}]}
    try:
        tasks = [rt.submit(body, caller, 20) for _ in range(3)]
        assert running.wait(3), "All three calls must enter inference before any completes."
        queued = rt.submit(body, caller, 20)
        with pytest.raises(BridgeError) as error:
            rt.submit(body, caller, 20)
        assert error.value.category == "queue_full"
        with pytest.raises(BridgeError) as error:
            rt.preflight(body, caller)
        assert error.value.category == "queue_full"
        tasks[0].cancel.set()
        release.set()
        for task in [*tasks, queued]:
            assert task.done.wait(5)
        assert tasks[0].error.category == "cancelled"
        assert all(task.result is not None and task.error is None for task in [*tasks[1:], queued])
        # Completed and cancelled jobs both release capacity.
        next_task = rt.submit(body, caller, 20)
        assert next_task.done.wait(5) and next_task.result is not None
    finally:
        release.set()
        rt.stop()
        store.close()


@pytest.mark.parametrize("workers,pending", [(0, 9), (True, 9), (2, 1), (2, False), (1.5, 9), (65,65), (64,65)])
def test_invalid_execution_limits_do_not_start_runtime(tmp_path, workers, pending):
    store = Store(tmp_path)
    try:
        with pytest.raises(ValueError):
            Runtime(store, max_workers=workers, max_pending=pending)
    finally:
        store.close()


@pytest.mark.parametrize("provider,model", [
    ("codex", "openai/gpt-6-astra"), ("claude", "anthropic/claude-haiku-4.5"),
])
def test_standard_supports_64_real_execution_slots_for_either_provider(tmp_path, provider, model):
    store = Store(tmp_path)
    _, key = store.create_key("standard-capacity", [provider])
    caller = store.authenticate(key)
    # A standard key must accept a full 64-request burst.
    assert caller["rpm"] >= 64
    release, all_running = threading.Event(), threading.Event()
    lock = threading.Lock()
    entered = 0

    def runner(*_):
        nonlocal entered
        with lock:
            entered += 1
            if entered == 64:
                all_running.set()
        assert release.wait(10)
        return "OK", {"prompt_tokens": 2, "completion_tokens": 1}, "stop"

    rt = Runtime(store, runner)
    body = {"model": model, "messages": [{"role": "user", "content": "synthetic"}]}
    try:
        tasks = [rt.submit(body, caller, 20) for _ in range(64)]
        assert all_running.wait(5), "64 calls must execute before any call finishes."
        with pytest.raises(BridgeError) as error:
            rt.submit(body, caller, 20)
        assert error.value.status == 429
        assert error.value.category == "queue_full"
        release.set()
        assert all(task.done.wait(5) and task.error is None for task in tasks)
        assert entered == 64
    finally:
        release.set()
        rt.stop()
        store.close()


@pytest.mark.parametrize('decisions', [False, True])
def test_64_normal_http_calls_share_capacity_and_leave_models_available(tmp_path, decisions):
    store = Store(tmp_path)
    _, key = store.create_key("ordinary-api")
    release, all_running = threading.Event(), threading.Event()
    lock = threading.Lock()
    entered = 0

    def runner(spec, *_):
        nonlocal entered
        with lock:
            entered += 1
            if entered == 64:
                all_running.set()
        assert release.wait(60)
        text = '{"noul":0.9}' if spec.schema else spec.messages[0]["parts"][0]["text"]
        return text, {"prompt_tokens": 2, "completion_tokens": 1}, "stop"

    rt = Runtime(store, runner)
    api = ApiServer(rt, 0)
    api.start()

    def http(path, body=None):
        request = urllib.request.Request(f"http://127.0.0.1:{api.port}" + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            response = opener.open(request, timeout=80)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read())

    def call(index):
        model = "openai/gpt-6-astra" if index % 2 else "anthropic/claude-haiku-4.5"
        if decisions and index % 2:
            return http('/api/alpha/decisions', {'model':model,'state':f'synthetic-{index}',
                'questions':{'q':{'type':'noul','instructions':'Synthetic?'}}})
        return http("/api/v1/chat/completions", {"model": model,
            "messages": [{"role": "user", "content": f"synthetic-{index}"}]})

    try:
        with ThreadPoolExecutor(max_workers=64) as clients:
            futures = [clients.submit(call, i) for i in range(64)]
            try:
                assert all_running.wait(50)
                assert http("/api/v1/models")[0] == 200
                status, health = http("/health")
                assert status == 200 and health["max_concurrent_requests"] == 64
                assert call(64)[0] == 429  # Shared total, not 64 for each provider.
            finally:
                release.set()
            for i, future in enumerate(futures):
                status, value = future.result(timeout=50)
                assert status == 200, value
                if decisions and i % 2:
                    assert value['answers']['q']['noul'] == 0.9
                else:
                    assert value["choices"][0]["message"]["content"] == f"synthetic-{i}"
    finally:
        release.set()
        rt.stop()
        api.stop()
        store.close()


MAC_FILE_LIMIT_PROBE = r'''
import json, resource, sys, tempfile, threading, urllib.request
from concurrent.futures import ThreadPoolExecutor
resource.setrlimit(resource.RLIMIT_NOFILE, (256, resource.getrlimit(resource.RLIMIT_NOFILE)[1]))
from desktop_bridge.capacity import ensure_file_limit
limit = ensure_file_limit()
from desktop_bridge.process import Child
from desktop_bridge.service import ApiServer, Runtime
from desktop_bridge.store import Store
release, all_running, lock, entered = threading.Event(), threading.Event(), threading.Lock(), [0]
def runner(*_):
    with tempfile.TemporaryDirectory() as cwd:
        child = Child([sys.executable, '-c', 'import sys; sys.stdin.read()'], cwd, None)
        try:
            with lock:
                entered[0] += 1
                if entered[0] == 64: all_running.set()
            release.wait(30)
            child.proc.communicate(b'', timeout=10)
        finally: child.close()
    return 'OK', {'prompt_tokens': 1, 'completion_tokens': 1}, 'stop'
store = Store(tempfile.mkdtemp()); _, key = store.create_key('fd-limit')
rt = Runtime(store, runner); api = ApiServer(rt, 0); api.start()
def call(_):
    request = urllib.request.Request(f'http://127.0.0.1:{api.port}/api/v1/chat/completions',
        data=json.dumps({'model': 'openai/gpt-6-astra', 'messages': [{'role': 'user', 'content': 'synthetic'}]}).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=60) as response:
            return response.status
    except urllib.error.HTTPError as error: return error.code
    except OSError: return 0
try:
    with ThreadPoolExecutor(max_workers=64) as clients:
        futures = [clients.submit(call, i) for i in range(64)]
        running = all_running.wait(30); release.set()
        statuses = [future.result() for future in futures]
finally:
    release.set(); rt.stop(); api.stop(); store.close()
print(json.dumps({'limit': limit, 'running': running, 'statuses': statuses}))
'''


@pytest.mark.skipif(sys.platform == 'win32', reason='POSIX descriptor limit')
def test_64_real_child_processes_fit_after_raising_launchd_descriptor_limit():
    # macOS LaunchAgents start with a 256 soft limit; 64 CLI pipe sets plus sockets exceed it.
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run([sys.executable, '-c', MAC_FILE_LIMIT_PROBE], cwd=root, capture_output=True,
                            timeout=120, env={**os.environ, 'PYTHONPATH': str(root)})
    assert result.returncode == 0, result.stderr.decode()[-2000:]
    value = json.loads(result.stdout.decode().strip().splitlines()[-1])
    assert value['limit'] >= 1024
    assert value['running'] and value['statuses'] == [200] * 64
