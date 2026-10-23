"""Real Windows process ownership; synthetic profiles and isolated reservations."""
import hashlib
import json
import os
from pathlib import Path
import queue
import socket
import subprocess
import sys
import threading
import urllib.request

import pytest

from desktop_bridge import windows_instance as guard

pytestmark = pytest.mark.skipif(sys.platform != 'win32', reason='Windows Winsock ownership')
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def address(monkeypatch):
    with socket.socket() as available:
        available.bind(('127.0.0.1', 0)); address = available.getsockname()
    monkeypatch.setattr(guard, 'MACHINE_ADDRESS', address)
    return address


def line(child):
    ready = queue.Queue()
    threading.Thread(target=lambda: ready.put(child.stdout.readline()), daemon=True).start()
    return ready.get(timeout=30).strip()


def test_reservation_is_exclusive_not_listening_and_reusable(address):
    first = guard.MachineInstance()
    try:
        assert first.primary and not first.socket.get_inheritable()
        assert first.socket.getsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE)
        second = guard.MachineInstance()
        assert not second.primary and second.socket is None
        with socket.socket() as intruder:
            intruder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            with pytest.raises(OSError): intruder.bind(address)
        with pytest.raises(OSError): socket.create_connection(address, timeout=.2)
    finally:
        first.close()
    successor = guard.MachineInstance()
    try: assert successor.primary
    finally: successor.close()


def test_unexpected_socket_failure_closes_reservation(monkeypatch):
    class Failed:
        closed = False
        def set_inheritable(self, _value): pass
        def setsockopt(self, *_values): pass
        def bind(self, _address): raise OSError(10022, 'synthetic invalid socket')
        def close(self): self.closed = True
    failed = Failed()
    monkeypatch.setattr(guard.socket, 'socket', lambda *_: failed)
    with pytest.raises(OSError): guard.MachineInstance()
    assert failed.closed


@pytest.mark.parametrize('background', [False, True])
def test_rejected_profile_is_untouched_before_store(tmp_path, address, monkeypatch, capsys, background):
    from desktop_bridge import __main__ as app
    from desktop_bridge.store import Store
    profile = tmp_path / 'existing'
    store = Store(profile, startup=False)
    store.insert_request({'id': 'synthetic-active', 'status': 'running'})
    store.close()
    before = hashlib.sha256((profile / 'bridge.sqlite').read_bytes()).digest()
    owner = guard.MachineInstance()
    monkeypatch.setattr(app.sys, 'argv', ['bridge', '--headless', '--data-dir', str(profile),
        *(['--background'] if background else [])])
    monkeypatch.setattr(app, 'Store', lambda *_: pytest.fail('Rejected start opened Store'))
    try:
        assert app.main() == guard.BUSY_EXIT
        assert '一台電腦只能執行一個 Bridge' in capsys.readouterr().err
        assert hashlib.sha256((profile / 'bridge.sqlite').read_bytes()).digest() == before
    finally: owner.close()


@pytest.mark.parametrize('stage', ['runtime', 'api', 'relay'])
def test_failed_startup_releases_machine_and_initialized_services(tmp_path, address, monkeypatch, stage):
    from desktop_bridge import __main__ as app, relay
    servers = []
    original = app.ApiServer
    class Captured(original):
        def start(self): super().start(); servers.append(self)
    monkeypatch.setattr(app, 'ApiServer', Captured)
    def fail(*_a, **_k): raise (OSError('synthetic bind failure') if stage == 'api' else RuntimeError('synthetic initialization failure'))
    if stage == 'runtime': monkeypatch.setattr(app, 'Runtime', fail)
    elif stage == 'api': monkeypatch.setattr(app, 'ApiServer', fail)
    else: monkeypatch.setattr(relay, 'Relay', fail)
    monkeypatch.setattr(app.sys, 'argv', ['bridge', '--headless', '--port', '0', '--data-dir', str(tmp_path)])
    if stage == 'api': assert app.main() == 2
    else:
        with pytest.raises(RuntimeError): app.main()
    for server in servers:
        assert not server.thread.is_alive()
        with pytest.raises(OSError): socket.create_connection(('127.0.0.1', server.port), timeout=.2)
    next_owner = guard.MachineInstance()
    try: assert next_owner.primary
    finally: next_owner.close()


WRAPPER = '''
import json,sys,threading
from desktop_bridge import windows_instance,management,__main__ as app
windows_instance.MACHINE_ADDRESS=('127.0.0.1',int(sys.argv.pop(1)))
management.ManagementServer.refresh_auth=lambda self:None
original=management.ManagementServer.start
def ready(manager):
    original(manager)
    print(json.dumps({'api':manager.api.port}),flush=True)
    threading.Thread(target=lambda:(sys.stdin.readline(),manager.on_shutdown()),daemon=True).start()
management.ManagementServer.start=ready
raise SystemExit(app.main())
'''


@pytest.mark.parametrize('ending', ['normal', 'kill'])
def test_real_profiles_normal_exit_kill_and_restart(tmp_path, address, ending):
    command = [sys.executable, '-u', '-c', WRAPPER, str(address[1])]
    def start(profile):
        child = subprocess.Popen(command + ['--background', '--data-dir', str(profile), '--port', '0'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=ROOT,
            creationflags=subprocess.CREATE_NO_WINDOW)
        try: return child, json.loads(line(child))['api']
        except BaseException: child.kill(); child.communicate(timeout=10); raise
    one, two = tmp_path / 'one', tmp_path / 'two'
    child, port = start(one)
    try:
        duplicate = subprocess.run(command + ['--background', '--data-dir', str(one), '--port', '0'],
            capture_output=True, text=True, cwd=ROOT, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
        assert duplicate.returncode == 0
        rejected = subprocess.run(command + ['--background', '--data-dir', str(two), '--port', '0'],
            capture_output=True, text=True, cwd=ROOT, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
        assert rejected.returncode == guard.BUSY_EXIT and not two.exists()
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://127.0.0.1:{port}/health', timeout=3) as response: assert json.load(response)['ok']
    finally:
        if ending == 'normal': child.stdin.write('stop\n'); child.stdin.flush()
        else: child.kill()
        child.communicate(timeout=20)
    assert child.returncode == (0 if ending == 'normal' else 1)
    with pytest.raises(OSError): socket.create_connection(('127.0.0.1', port), timeout=.2)
    successor, _ = start(two)
    successor.stdin.write('stop\n'); successor.stdin.flush(); successor.communicate(timeout=20)
    assert successor.returncode == 0


def test_simultaneous_processes_have_one_owner(tmp_path, address):
    script = '''
import sys
from desktop_bridge import windows_instance as guard
guard.MACHINE_ADDRESS=('127.0.0.1',int(sys.argv[1]))
sys.stdin.readline();owner=guard.MachineInstance()
print(int(owner.primary),flush=True)
sys.stdin.readline();owner.close()
'''
    children = [subprocess.Popen([sys.executable, '-u', '-c', script, str(address[1])],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=ROOT,
        creationflags=subprocess.CREATE_NO_WINDOW) for _ in range(6)]
    try:
        for child in children: child.stdin.write('start\n'); child.stdin.flush()
        assert sum(int(line(child)) for child in children) == 1
    finally:
        for child in children:
            if child.poll() is None: child.stdin.write('stop\n'); child.stdin.flush()
            child.communicate(timeout=15)
