"""Initialize-only Codex resources; no caller data enters a resident CLI."""
import tempfile
import time

from . import providers
from .codex_session import CodexSession


class CodexResource:
    warm_hit = False

    def __init__(self, settings, cancel, deadline):
        began = time.monotonic()
        self.directory = tempfile.TemporaryDirectory(prefix='aigo-warm-runtime-')
        self.cwd = self.directory.name
        self.session = None
        try:
            self.session = CodexSession(providers.codex_command(settings), self.cwd,
                providers.environment(), cancel, max(.001, deadline - time.monotonic()),
                generation=providers.auth_generation('codex', settings))
            self.handshake_seconds = time.monotonic() - began
        except BaseException:
            self.directory.cleanup()
            raise

    def healthy(self):
        return self.session.healthy()

    def close(self):
        try:
            if self.session:
                self.session.close()
        finally:
            self.directory.cleanup()

