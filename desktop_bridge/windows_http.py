"""Exclusive loopback listeners for Windows entry points."""
from http.server import ThreadingHTTPServer
import socket


class ExclusiveLoopbackServer(ThreadingHTTPServer):
    def server_bind(self):
        # ApiServer's nested class enables reuse on other platforms. Override
        # that inherited setting before TCPServer.server_bind can apply it.
        self.allow_reuse_address = False
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def install():
    from . import management, service
    # Do not change the stdlib class or Mac entry point behavior.
    management.ThreadingHTTPServer = ExclusiveLoopbackServer
    service.ThreadingHTTPServer = ExclusiveLoopbackServer
