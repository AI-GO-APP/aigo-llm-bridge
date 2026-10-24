"""Exercise real API/management sockets; never touch an installed profile."""
import socket
import sys

import pytest

from desktop_bridge import management, service
from desktop_bridge.store import Store
from desktop_bridge.windows_http import ExclusiveLoopbackServer, install


@pytest.fixture
def isolated_source():
    with socket.socket() as available:
        available.bind(('127.0.0.1', 0)); port = available.getsockname()[1]
    wrapper = "import sys;from desktop_bridge import windows_instance,__main__;windows_instance.MACHINE_ADDRESS=('127.0.0.1',int(sys.argv.pop(1)));raise SystemExit(__main__.main())"
    return [sys.executable, '-c', wrapper, str(port)]


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows Winsock semantics')
def test_native_api_and_management_refuse_port_hijacking(tmp_path, monkeypatch):
    monkeypatch.setattr(service, 'ThreadingHTTPServer', service.ThreadingHTTPServer)
    monkeypatch.setattr(management, 'ThreadingHTTPServer', management.ThreadingHTTPServer)
    install()
    store = Store(tmp_path)
    runtime = service.Runtime(store)
    api = service.ApiServer(runtime, 0)
    manager = management.ManagementServer(store, runtime, api, preview=True)
    try:
        for owner in (api, manager):
            assert isinstance(owner.server, ExclusiveLoopbackServer)
            assert owner.server.socket.getsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE)
            assert not owner.server.socket.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)
            with socket.socket() as intruder:
                intruder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                with pytest.raises(OSError) as error:
                    intruder.bind(('127.0.0.1', owner.port))
                assert error.value.winerror in (10013, 10048)
    finally:
        manager.server.server_close()
        api.server.server_close()
        runtime.stop()
        store.close()


def test_adapter_does_not_replace_standard_library_server(monkeypatch):
    import http.server
    original = http.server.ThreadingHTTPServer
    monkeypatch.setattr(service, 'ThreadingHTTPServer', service.ThreadingHTTPServer)
    monkeypatch.setattr(management, 'ThreadingHTTPServer', management.ThreadingHTTPServer)
    install()
    assert http.server.ThreadingHTTPServer is original


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows source entry point')
def test_background_port_conflict_exits_without_desktop_dialog(tmp_path, isolated_source):
    import subprocess
    from pathlib import Path
    with socket.socket() as reserved:
        reserved.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        reserved.bind(('127.0.0.1',0));reserved.listen()
        completed=subprocess.run([*isolated_source,'--background',
            '--data-dir',str(tmp_path),'--port',str(reserved.getsockname()[1])],
            cwd=Path(__file__).resolve().parents[3],capture_output=True,timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW)
        assert completed.returncode==2 and not completed.stdout and not completed.stderr


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows source entry point')
def test_source_headless_entry_uses_exclusive_listener(tmp_path, isolated_source):
    import subprocess,time,urllib.request
    from pathlib import Path
    with socket.socket() as available:
        available.bind(('127.0.0.1',0));port=available.getsockname()[1]
    child=subprocess.Popen([*isolated_source,'--headless',
        '--data-dir',str(tmp_path),'--port',str(port)],
        cwd=Path(__file__).resolve().parents[3],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        deadline=time.monotonic()+10
        while True:
            try:
                with opener.open(f'http://127.0.0.1:{port}/health',timeout=.5) as response:
                    assert response.status==200;break
            except OSError:
                assert child.poll() is None and time.monotonic()<deadline
                time.sleep(.1)
        with socket.socket() as intruder:
            intruder.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            with pytest.raises(OSError):intruder.bind(('127.0.0.1',port))
    finally:
        child.terminate();child.wait(timeout=10)
