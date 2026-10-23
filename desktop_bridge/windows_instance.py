"""Winsock-owned machine-wide runtime guard; no IPC or credential sharing."""
import socket


MACHINE_ADDRESS = ('127.0.0.1', 8919)
BUSY_EXIT = 3
BUSY_MESSAGE = ('一台電腦只能執行一個 Bridge。已有服務或全機啟動鎖 TCP 8919 被占用；'
                '請先暫停、排空並正常結束既有 Bridge，再切換設定檔。')


class RuntimeBusyError(ValueError):
    pass


class MachineInstance:
    def __init__(self):
        self.primary = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.set_inheritable(False)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            # A reservation only: never listen, accept, send or expose an owner token.
            self.socket.bind(MACHINE_ADDRESS)
        except OSError as error:
            self.close()
            if (getattr(error, 'winerror', None) or error.errno) not in (10013, 10048):
                raise
        else:
            self.primary = True

    def close(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None
