"""Real process contention without touching the owner's Bridge or credentials."""
import errno
import json
import os
from pathlib import Path
import selectors
import socket
import subprocess
import sys
import urllib.request

import pytest

from desktop_bridge import macos_instance


pytestmark = pytest.mark.skipif(os.name == 'nt', reason='macOS/POSIX instance contract; Windows tracked separately')


@pytest.fixture
def address(monkeypatch):
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        address = probe.getsockname()
    monkeypatch.setattr(macos_instance, 'MACHINE_ADDRESS', address)
    return address


def test_kernel_lock_excludes_second_owner_and_releases(address):
    one = macos_instance.MachineInstance()
    try:
        assert one.primary and not one.socket.get_inheritable()
        two = macos_instance.MachineInstance()
        assert not two.primary and two.socket is None
        two.close()
    finally:
        one.close()
    three = macos_instance.MachineInstance()
    try:
        assert three.primary
    finally:
        three.close()


def test_unexpected_bind_failure_closes_socket_and_fails(monkeypatch):
    class DeniedSocket:
        closed = False
        def set_inheritable(self, _value): pass
        def bind(self, _address): raise PermissionError(errno.EACCES, 'synthetic')
        def close(self): self.closed = True
    denied = DeniedSocket()
    monkeypatch.setattr(macos_instance.socket, 'socket', lambda *_: denied)
    with pytest.raises(PermissionError): macos_instance.MachineInstance()
    assert denied.closed


@pytest.mark.skipif(os.name == 'nt', reason='Mac/POSIX service entry and signals')
@pytest.mark.parametrize('ending', ['terminate', 'kill'])
def test_real_service_excludes_other_profiles_and_restarts(tmp_path, address, ending):
    # An isolated lock address keeps this regression independent of a real owner service.
    # Production has no CLI/env option to change its fixed machine address.
    wrapper = '''
import sys
from desktop_bridge import macos_instance, __main__ as app
macos_instance.MACHINE_ADDRESS = ('127.0.0.1', int(sys.argv.pop(1)))
sys.platform = 'darwin'
original = app.ApiServer.start
def ready(server):
    original(server)
    print(server.port, flush=True)
app.ApiServer.start = ready
raise SystemExit(app.main())
'''
    first = tmp_path / 'one'
    second = tmp_path / 'two'
    command = [sys.executable, '-u', '-c', wrapper, str(address[1])]
    def start(profile):
        child = subprocess.Popen(command + ['--data-dir', str(profile), '--headless', '--port', '0'],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                 cwd=Path(__file__).resolve().parents[2])
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(child.stdout, selectors.EVENT_READ)
                assert selector.select(timeout=15), 'service did not report readiness'
            port = int(child.stdout.readline().strip())
            return child, port
        except BaseException:
            child.kill(); child.communicate(timeout=10)
            raise
    child, port = start(first)
    try:
        for flags, expected in [([], 2), (['--background'], 0)]:
            denied = subprocess.run(command + ['--data-dir', str(second), '--headless', '--port', '0', *flags],
                                    capture_output=True, text=True, timeout=10,
                                    cwd=Path(__file__).resolve().parents[2])
            assert denied.returncode == expected and '一台電腦只能執行一個 Bridge' in denied.stderr
            assert not (second / 'bridge.sqlite').exists()
        duplicate = subprocess.run(command + ['--data-dir', str(first), '--headless'],
                                   capture_output=True, text=True, timeout=10,
                                   cwd=Path(__file__).resolve().parents[2])
        assert duplicate.returncode == 0 and not duplicate.stderr
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=3) as response:
            assert json.load(response)['ok']
    finally:
        getattr(child, ending)()
        child.communicate(timeout=15)
    with pytest.raises(OSError):
        urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=1)
    successor, _ = start(second)
    successor.terminate(); successor.communicate(timeout=15)


@pytest.mark.parametrize('background', [False, True])
def test_denied_start_preserves_existing_database(tmp_path, address, monkeypatch, capsys, background):
    from desktop_bridge import __main__ as app
    from desktop_bridge.store import Store
    profile = tmp_path / 'existing'
    store = Store(profile, startup=False)
    store.insert_request({'id': 'sentinel', 'status': 'running'})
    original_id = store.get('device_id')
    store.close()
    owner = macos_instance.MachineInstance()
    monkeypatch.setattr(app.sys, 'platform', 'darwin')
    monkeypatch.setattr(app.sys, 'argv', ['bridge', '--data-dir', str(profile), '--headless',
                                       *(['--background'] if background else [])])
    try:
        assert app.main() == (0 if background else 2)
        assert '一台電腦只能執行一個 Bridge' in capsys.readouterr().err
        store = Store(profile, startup=False)
        try:
            assert store.get('device_id') == original_id
            assert store.logs()[0]['status'] == 'running'
        finally:
            store.close()
    finally:
        owner.close()


def test_initialization_error_releases_both_locks(tmp_path, address, monkeypatch):
    from desktop_bridge import __main__ as app
    from desktop_bridge.windows import Instance
    monkeypatch.setattr(app.sys, 'platform', 'darwin')
    monkeypatch.setattr(app.sys, 'argv', ['bridge', '--data-dir', str(tmp_path)])
    def fail(*_args): raise RuntimeError('synthetic startup failure')
    monkeypatch.setattr(app, 'run', fail)
    with pytest.raises(RuntimeError): app.main()
    machine = macos_instance.MachineInstance()
    profile = Instance(tmp_path)
    try:
        assert machine.primary and profile.primary
    finally:
        machine.close(); profile.close()


def test_api_bind_failure_releases_machine_lock(tmp_path, address, monkeypatch):
    from desktop_bridge import __main__ as app
    monkeypatch.setattr(app.sys, 'platform', 'darwin')
    monkeypatch.setattr(app.sys, 'argv', ['bridge', '--data-dir', str(tmp_path), '--headless'])
    def occupied(*_args, **_kwargs): raise OSError(errno.EADDRINUSE, 'synthetic occupied API port')
    monkeypatch.setattr(app, 'ApiServer', occupied)
    assert app.main() == 2
    successor = macos_instance.MachineInstance()
    try:
        assert successor.primary
    finally:
        successor.close()


def test_simultaneous_processes_have_exactly_one_owner(tmp_path, address):
    script = '''
import sys
from desktop_bridge import macos_instance
macos_instance.MACHINE_ADDRESS = ('127.0.0.1', int(sys.argv[1]))
sys.stdin.readline()
instance = macos_instance.MachineInstance()
print(int(instance.primary), flush=True)
sys.stdin.readline()
instance.close()
'''
    children = [subprocess.Popen([sys.executable, '-u', '-c', script, str(address[1])],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, cwd=Path(__file__).resolve().parents[2]) for _ in range(6)]
    try:
        for child in children:
            child.stdin.write('start\n'); child.stdin.flush()
        results = []
        for child in children:
            with selectors.DefaultSelector() as selector:
                selector.register(child.stdout, selectors.EVENT_READ)
                assert selector.select(timeout=10)
            results.append(int(child.stdout.readline()))
        assert sum(results) == 1
    finally:
        for child in children:
            if child.poll() is None:
                child.stdin.write('stop\n'); child.stdin.flush()
            child.communicate(timeout=10)
