"""One Bridge runtime per Mac, independent of user, profile and API port."""
import errno
import socket


# Bind only: no listener, protocol, credential or configurable second lock scope.
# Kernel ownership spans GUI sessions/users and disappears on process exit.
MACHINE_ADDRESS = ('127.0.0.1', 8919)


class MachineInstance:
    def __init__(self):
        self.primary = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Do not enable SO_REUSEADDR/SO_REUSEPORT or pass this fd to children.
            self.socket.set_inheritable(False)
            self.socket.bind(MACHINE_ADDRESS)
        except OSError as exc:
            self.close()
            if exc.errno != errno.EADDRINUSE:
                raise
        else:
            self.primary = True

    def close(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None
