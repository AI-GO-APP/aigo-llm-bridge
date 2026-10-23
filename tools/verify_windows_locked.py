"""Opt-in interactive lock acceptance; never locks/unlocks or changes power policy.

Runs an isolated frozen Bridge and real Codex inference before/during/after a
human Win+L/unlock. Only metadata is persisted. Existing Claude/Cloud untouched.
"""
import argparse
import ctypes
from ctypes import wintypes as w
import json
import math
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop_bridge.secret import protect
from desktop_bridge.store import Store
from desktop_bridge.windows_console import request_owner
from desktop_bridge.windows_release import atomic_json


class Level1(ctypes.Structure):
    _fields_ = [('session', w.DWORD), ('state', ctypes.c_int), ('flags', w.LONG),
                ('station', w.WCHAR * 33), ('user', w.WCHAR * 21), ('domain', w.WCHAR * 18),
                *[(name, ctypes.c_longlong) for name in ('logon', 'connect', 'disconnect', 'input', 'now')],
                *[(name, w.DWORD) for name in ('inbytes', 'outbytes', 'inframes', 'outframes', 'inc', 'outc')]]


class Info(ctypes.Structure):
    _fields_ = [('level', w.DWORD), ('data', Level1)]


class Session:
    def __init__(self):
        self.dll = ctypes.WinDLL('wtsapi32', use_last_error=True)
        self.dll.WTSQuerySessionInformationW.argtypes = [w.HANDLE, w.DWORD, ctypes.c_int,
                                                        ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(w.DWORD)]
        self.dll.WTSFreeMemory.argtypes = [ctypes.c_void_p]
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.SetThreadExecutionState.argtypes = [w.DWORD]
        self.kernel.SetThreadExecutionState.restype = w.DWORD
        value = w.DWORD()
        if not self.kernel.ProcessIdToSessionId(self.kernel.GetCurrentProcessId(), ctypes.byref(value)):
            raise OSError('Cannot determine interactive session')
        self.id = value.value

    def locked(self):
        pointer, size = ctypes.c_void_p(), w.DWORD()
        if not self.dll.WTSQuerySessionInformationW(None, self.id, 25, ctypes.byref(pointer), ctypes.byref(size)):
            raise OSError('Cannot query interactive session')
        try:
            if size.value < ctypes.sizeof(Info):
                raise ValueError('Invalid session information')
            info = ctypes.cast(pointer, ctypes.POINTER(Info)).contents
            if info.level != 1 or info.data.session != self.id or info.data.flags not in (0, 1):
                raise ValueError('Unknown session lock state')
            return info.data.flags == 0
        finally:
            self.dll.WTSFreeMemory(pointer)

    def awake(self, enabled):
        if not self.kernel.SetThreadExecutionState(0x80000001 if enabled else 0x80000000):
            raise OSError('Cannot assert system availability')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--wait-lock', type=int, default=600)
    parser.add_argument('--wait-unlock', type=int, default=600)
    args = parser.parse_args()
    if sys.platform != 'win32':
        parser.error('Windows interactive session required')
    exe, output = Path(args.exe).resolve(), Path(args.output).resolve()
    if not exe.is_file() or output.exists():
        parser.error('Use an existing candidate CLI and a NEW isolated receipt directory')
    output.mkdir(parents=True)
    data = output / 'profile'
    receipt = {'success': False, 'phase': 'starting', 'calls': [], 'checks': {},
               'scope': 'isolated frozen candidate, real local Codex subscription POST/GET; no Cloud deployment or Claude calls'}
    session = Session()
    owner = key = key_id = None
    stop = threading.Event()
    samples = []
    def sample():
        while not stop.is_set():
            try:
                samples.append((time.monotonic(), session.locked()))
            except Exception:
                samples.append((time.monotonic(), None))
            stop.wait(.5)
    watcher = threading.Thread(target=sample, daemon=True)
    def save(phase):
        receipt['phase'] = phase
        atomic_json(output / 'acceptance.json', receipt)
    def manager(path, body=None):
        return json.loads(request_owner(owner, path, body))
    def wait_state(locked, timeout):
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            if session.locked() is locked:
                return
            time.sleep(.5)
        raise TimeoutError('Expected lock transition did not occur')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def call(phase, expected):
        start = time.monotonic()
        assert session.locked() is expected, 'Unexpected initial lock state'
        headers = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}
        with opener.open(urllib.request.Request(base + '/models', headers=headers), timeout=15) as response:
            assert response.status == 200 and any(m['id'] == model for m in json.load(response)['data'])
        body = json.dumps({'model': model, 'messages': [{'role': 'user', 'content': 'Reply exactly PONG.'}], 'stream': False}).encode()
        request = urllib.request.Request(base + '/chat/completions', data=body, headers=headers)
        try:
            with opener.open(request, timeout=200) as response:
                value = json.load(response)
                assert response.status == 200
                assert value['choices'][0]['message']['content'].strip() == 'PONG'
                usage = value['usage']
                assert type(usage['cost']) in (int, float) and math.isfinite(usage['cost']) and usage['cost'] > 0
                assert usage['prompt_tokens'] > 0 and usage['completion_tokens'] > 0
                cost_source = response.headers.get('X-Bridge-Cost-Source')
                assert cost_source == 'openrouter-list-price-estimate'
        except urllib.error.HTTPError as error:
            # Never persist a raw body or upstream error text.
            safe = json.loads(error.read(65536)).get('error', {})
            receipt['failure_http_status'] = error.code
            receipt['failure_code'] = safe.get('type', safe.get('code'))
            raise RuntimeError('Inference failed') from None
        end = time.monotonic()
        assert session.locked() is expected
        interval = [v for t, v in samples if start <= t <= end]
        assert interval and all(v is expected for v in interval), 'Lock state changed during inference'
        receipt['calls'].append({'phase': phase, 'http_status': 200, 'model': model, 'locked_entire_call': expected,
                                 'session_samples': len(interval), 'elapsed_ms': round((end-start)*1000),
                                 'prompt_tokens': usage['prompt_tokens'], 'completion_tokens': usage['completion_tokens'],
                                 'cost_usd': usage['cost'], 'cost_source': cost_source})
        save(phase + '_passed')
    try:
        assert not session.locked(), 'Begin from an unlocked desktop'
        session.awake(True)  # No display requirement, registry, power plan, or administrator rights.
        watcher.start()
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        store = Store(data, startup=False)
        store.set('port', port)
        store.set('timeout_s', 180)
        model = store.get('default_model')
        device_id = store.get('device_id')
        store.close()
        result = subprocess.run([str(exe), 'onboarding', 'status', '--data-dir', str(data)],
                                capture_output=True, timeout=65, creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode == 0, 'Candidate did not start'
        owner = json.loads(protect((data / 'windows-control.dpapi').read_bytes(), decrypt=True))
        initial = manager('/manage/state')
        created = manager('/manage/keys/create', {'label': 'Isolated lock acceptance'})
        key_id, key = created['id'], created['token']
        base = f'http://127.0.0.1:{port}/api/v1'
        call('before_lock', False)
        save('ready_for_human_Win_L')
        wait_state(True, args.wait_lock)
        locked_start = time.monotonic()
        save('locked_testing')
        call('while_locked_1', True)
        # Cross the common 60s locked-display timeout without keeping the display on.
        while time.monotonic() - locked_start < 75:
            assert session.locked(), 'Unlocked before locked acceptance completed'
            time.sleep(.5)
        call('while_locked_2', True)
        receipt['locked_duration_seconds'] = round(time.monotonic() - locked_start, 1)
        save('locked_tests_passed_unlock_normally')
        wait_state(False, args.wait_unlock)
        call('after_unlock', False)
        final = manager('/manage/state')
        store = Store(data, startup=False)
        rows = store.logs()
        receipt['checks'] = {
            'four_real_codex_inferences': len(receipt['calls']) == 4,
            'same_device': store.get('device_id') == device_id,
            'same_key_valid': bool(store.authenticate(key)),
            'same_configured_url': final['settings']['public_url'] == initial['settings']['public_url'],
            'four_metadata_cost_rows': len(rows) == 4 and all(r['status'] == 'completed' and r['cost_usd'] > 0 for r in rows),
            'no_power_policy_or_elevation_files': not (data / 'windows-power.json').exists() and not (data / 'windows-power-elevation.json').exists(),
        }
        store.close()
        assert all(receipt['checks'].values())
        receipt['success'] = True
        save('completed')
    except Exception as error:
        receipt['failure_type'] = type(error).__name__
        save('failed')
    finally:
        if owner:
            if key_id:
                try:
                    manager('/manage/keys/revoke', {'id': key_id})
                    receipt['test_key_revoked'] = True
                except Exception:
                    receipt['test_key_revoked'] = False
            try:
                manager('/manage/shutdown', {})
                receipt['isolated_service_shutdown_requested'] = True
            except Exception:
                receipt['isolated_service_shutdown_requested'] = False
        stop.set()
        if watcher.is_alive():
            watcher.join(2)
        session.awake(False)
        atomic_json(output / 'acceptance.json', receipt)
    print(json.dumps({'success': receipt['success'], 'phase': receipt['phase'], 'calls': len(receipt['calls'])}))
    return 0 if receipt['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
