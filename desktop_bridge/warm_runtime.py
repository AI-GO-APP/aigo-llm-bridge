"""Initialize-only Codex resources; no caller data enters a resident CLI."""
import tempfile
import time

from . import providers
from .codex_session import CodexSession


class CodexResource:
    warm_hit = False

    def __init__(self, settings, cancel, deadline, *, profile='standard'):
        began = time.monotonic()
        self.directory = tempfile.TemporaryDirectory(prefix='aigo-warm-runtime-')
        self.cwd = self.directory.name
        self.session = None
        try:
            command = (providers.codex_command(settings,profile=profile,cancel=cancel) if profile != 'standard'
                       else providers.codex_command(settings))
            self.session = CodexSession(command, self.cwd,
                providers.environment(), cancel, max(.001, deadline - time.monotonic()),
                generation=providers.auth_generation('codex', settings),profile=profile)
            self.handshake_seconds = time.monotonic() - began
        except BaseException:
            self.directory.cleanup()
            raise

    def healthy(self):
        return self.session.healthy()

    def prepare(self, cancel, deadline):
        # The pool must own this root before a policy check can fail.
        self.session.verify_profile(cancel, deadline)

    def close(self):
        try:
            if self.session:
                self.session.close()
        finally:
            self.directory.cleanup()

