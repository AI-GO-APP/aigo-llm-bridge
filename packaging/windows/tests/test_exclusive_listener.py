"""Exercise real API/management sockets; never touch an installed profile."""
import socket
import sys

import pytest

from desktop_bridge import management, service
from desktop_bridge.store import Store
from desktop_bridge.windows_http import ExclusiveLoopbackServer, install


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
        runtime.pool.shutdown()
        store.close()


def test_adapter_does_not_replace_standard_library_server(monkeypatch):
    import http.server
    original = http.server.ThreadingHTTPServer
    monkeypatch.setattr(service, 'ThreadingHTTPServer', service.ThreadingHTTPServer)
    monkeypatch.setattr(management, 'ThreadingHTTPServer', management.ThreadingHTTPServer)
    install()
    assert http.server.ThreadingHTTPServer is original
