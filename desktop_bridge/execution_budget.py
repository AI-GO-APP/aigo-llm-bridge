"""Request-local monotonic budgets and numeric timing metadata; no caller content."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
import threading
import time

from .errors import BridgeError

TIMING_COLUMNS = (
    'validation_ms', 'schema_wait_ms', 'schema_execution_ms', 'queue_wait_ms',
    'provider_setup_ms', 'cli_spawn_ms', 'cli_ready_ms', 'inference_ms',
    'output_validation_ms', 'total_ms',
)
LEASE_COLUMNS = ('warm_hits', 'cold_starts')
PROFILE_COLUMNS = ('inference_profile', 'profile_reason')
_current = ContextVar('bridge_execution_budget', default=None)


@dataclass
class Budget:
    until: float
    cancel: threading.Event
    started: float = field(default_factory=time.monotonic)
    timings: dict = field(default_factory=dict)
    leases: dict = field(default_factory=dict)
    profile: dict = field(default_factory=dict)

    def check(self):
        if self.cancel.is_set():
            raise BridgeError(499, 'cancelled', '請求已取消。')
        if time.monotonic() >= self.until:
            raise BridgeError(408, 'timeout', '請求期限已過。')

    def remaining(self):
        self.check()
        return self.until - time.monotonic()

    def metadata(self):
        from .inference_profile import STANDARD, MINIMAL, PROFILE_REASONS
        return {name: round(value * 1000) for name, value in self.timings.items()
                if name in TIMING_COLUMNS} | {name: self.leases.get(name, 0) for name in LEASE_COLUMNS} | {
                name:value for name,value in self.profile.items()
                if (name == 'inference_profile' and value in {STANDARD,MINIMAL})
                or (name == 'profile_reason' and value in PROFILE_REASONS)}


def current():
    return _current.get()


def check():
    if budget := current():
        budget.check()


@contextmanager
def scope(budget):
    token = _current.set(budget)
    try:
        yield
    finally:
        _current.reset(token)


@contextmanager
def timed(name):
    started = time.monotonic()
    try:
        yield
    finally:
        if budget := current():
            budget.timings[name] = budget.timings.get(name, 0) + time.monotonic() - started


@contextmanager
def locked(lock):
    """Shared metadata locks must not outlive the caller's request budget."""
    budget=current()
    if budget:
        while not lock.acquire(timeout=min(.05,budget.remaining())):
            budget.check()
    else:lock.acquire()
    try:
        check()
        yield
    finally:lock.release()
