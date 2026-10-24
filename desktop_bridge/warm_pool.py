"""Single-use CLI leases sharing one active/idle/refill/closing budget.

One accounting domain covers active, idle, starting and closing CLI roots.
Factory receives no request, key, model or instructions. Prewarm cancellation
belongs to the pool; cold startup additionally observes its request cancellation.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import threading
import time

from desktop_bridge.errors import BridgeError
from desktop_bridge.process import check_cancel


@dataclass(eq=False)
class Entry:
    generation: object
    resource: object = None
    ready_at: float = 0
    state: str = 'starting'


class StartupCancel:
    def __init__(self, request, stop):
        self.request, self.stop = request, stop

    def is_set(self):
        return self.request.is_set() or self.stop.is_set()

    def wait(self, timeout):
        until = time.monotonic() + timeout
        while not self.is_set():
            remaining = until - time.monotonic()
            if remaining <= 0:
                return False
            self.stop.wait(min(.02, remaining))
        return True


class SingleUsePool:
    def __init__(self, factory, generation, *, target=0, limit=8, ttl=120, backoff=.1, paused=False):
        if type(target) is not int or type(limit) is not int or not 0 <= target <= limit <= 64 or limit < 1:
            raise ValueError('Require 0 <= target <= limit <= 64 and limit >= 1.')
        if not 0 < ttl <= 600 or not .01 <= backoff <= 5:
            raise ValueError('Invalid TTL or backoff.')
        self.factory, self.generation = factory, generation
        self.target, self.limit, self.ttl = target, limit, ttl
        self.backoff = backoff
        self.condition = threading.Condition(threading.RLock())
        self.entries = set()
        self.waiting_leases = 0
        self.paused = paused
        self.stop_event = threading.Event()
        self.created = self.hits = self.cold = self.failures = self.peak = 0
        self.thread = threading.Thread(target=self._refill, name='bridge-warm-refill', daemon=True)
        self.thread.start()

    def snapshot(self):
        with self.condition:
            return {state: sum(e.state == state or (state == 'closing' and e.state == 'retiring') for e in self.entries)
                    for state in ('starting', 'idle', 'active', 'closing', 'quarantined')} | {
                'unavailable': self.stop_event.is_set(), 'resident_target': self.target, 'total': len(self.entries), 'limit': self.limit, 'peak': self.peak,
                'created': self.created, 'warm_hits': self.hits, 'cold_starts': self.cold,
                'refill_failures': self.failures, 'paused': self.paused,
                'waiting_leases': self.waiting_leases}

    def _reserve(self, generation):
        entry = Entry(generation)
        self.entries.add(entry)
        self.peak = max(self.peak, len(self.entries))
        return entry

    def _dispose(self, entry):
        # Keep the slot counted until the owned process/pipes/cwd have closed.
        with self.condition:
            if entry not in self.entries or entry.state == 'closing':
                return
            entry.state = 'closing'
        try:
            if entry.resource is not None:
                entry.resource.close()
        except BaseException:
            with self.condition:
                entry.state = 'quarantined'
                self.stop_event.set()
                self.condition.notify_all()
            raise
        with self.condition:
            self.entries.discard(entry)
            self.condition.notify_all()

    def _create(self, entry, cancel, deadline):
        try:
            entry.resource = self.factory(StartupCancel(cancel, self.stop_event),
                                          min(deadline, time.monotonic() + 3))
            with self.condition:
                self.created += 1
            if self.stop_event.is_set() or entry.generation != self.generation():
                raise BridgeError(503, 'provider_authentication', '待命 CLI 世代已失效。')
            check_cancel(cancel, deadline)
            entry.ready_at = time.monotonic()
        except BaseException:
            self._dispose(entry)
            raise

    def _refill(self):
        delay = self.backoff
        while not self.stop_event.is_set():
            stale = []; entry = None
            try:
                with self.condition:
                    if self.paused or self.target == 0:
                        self.condition.wait(.05)
                        continue
                generation = self.generation()
                with self.condition:
                    stale = [e for e in self.entries if e.state == 'idle' and (
                        self.paused or e.generation != generation or
                        time.monotonic() - e.ready_at >= self.ttl or not e.resource.healthy())]
                    for old in stale:
                        old.state = 'retiring'
                    idle = sum(e.state in {'idle', 'starting'} for e in self.entries)
                    if (not stale and not self.paused and not self.waiting_leases
                            and idle < self.target and len(self.entries) < self.limit):
                        entry = self._reserve(generation)
                for old in stale:
                    self._dispose(old)
                if entry:
                    self._create(entry, self.stop_event, time.monotonic() + 3)
                    with self.condition:
                        discard = self.paused or self.stop_event.is_set()
                        if not discard:
                            entry.state = 'idle'
                        self.condition.notify_all()
                    if discard:
                        self._dispose(entry)
                    delay = self.backoff
                    continue
            except Exception:
                with self.condition:
                    self.failures += 1
                self.stop_event.wait(delay)
                delay = min(5, delay * 2)
                continue
            with self.condition:
                self.condition.wait(.05)

    @contextmanager
    def lease(self, cancel, deadline, *, cold_only=False, allow_paused=False):
        entry = None
        waiting = True
        with self.condition:
            self.waiting_leases += 1
        try:
            while entry is None:
                check_cancel(cancel, deadline)
                generation = self.generation()
                stale = []
                with self.condition:
                    if self.stop_event.is_set() or (self.paused and not allow_paused):
                        raise BridgeError(503, 'paused', 'CLI 池已暫停或停止。')
                    for candidate in self.entries:
                        if candidate.state != 'idle':
                            continue
                        if cold_only and len(self.entries) < self.limit:
                            break
                        if (cold_only or candidate.generation != generation or time.monotonic() - candidate.ready_at >= self.ttl
                                or not candidate.resource.healthy()):
                            candidate.state = 'retiring'
                            stale.append(candidate)
                            if cold_only:break
                            continue
                        entry = candidate
                        entry.state = 'active'
                        entry.resource.warm_hit = True
                        self.hits += 1
                        break
                    if entry is None and not stale and len(self.entries) < self.limit:
                        entry = self._reserve(generation)
                        self.cold += 1
                    if entry is None and not stale:
                        self.condition.wait(min(.05, max(.001, deadline - time.monotonic())))
                for old in stale:
                    self._dispose(old)
            with self.condition:
                self.waiting_leases -= 1
                waiting = False
            if entry.resource is None:
                if cold_only:
                    entry.resource = EmptyResource()
                else:
                    self._create(entry, cancel, deadline)
                with self.condition:
                    entry.state = 'active'
            check_cancel(cancel, deadline)
            if not cold_only and entry.generation != self.generation():
                raise BridgeError(503, 'provider_authentication', '待命 CLI 世代已失效。')
            yield entry.resource
        finally:
            if waiting:
                with self.condition:
                    self.waiting_leases -= 1
                    self.condition.notify_all()
            if entry:
                self._dispose(entry)

    def pause(self):
        with self.condition:
            self.paused = True
            self.condition.notify_all()
            idle = [e for e in self.entries if e.state == 'idle']
            for entry in idle:
                entry.state = 'retiring'
        for entry in idle:
            self._dispose(entry)

    def resume(self):
        with self.condition:
            if self.stop_event.is_set():
                raise ValueError('A stopped pool cannot resume.')
            self.paused = False
            self.condition.notify_all()

    def configure(self, target, limit):
        if type(target) is not int or type(limit) is not int or not 0 <= target <= limit <= 64 or limit < 1:
            raise ValueError('Require 0 <= resident <= concurrency <= 64 and concurrency >= 1.')
        with self.condition:
            if not self.paused or self.entries or self.waiting_leases or self.stop_event.is_set():
                raise ValueError('Pause and drain before changing experimental capacity.')
            self.target, self.limit = target, limit
            self.condition.notify_all()

    def close(self):
        self.stop_event.set()
        until = time.monotonic() + 4
        with self.condition:
            self.condition.notify_all()
        self.thread.join(timeout=max(0, until - time.monotonic()))
        with self.condition:
            while (any(e.state == 'starting' for e in self.entries) or self.waiting_leases) and time.monotonic() < until:
                self.condition.wait(min(.05, max(0, until - time.monotonic())))
        with self.condition:
            entries = [e for e in self.entries if e.state != 'starting']
        for entry in entries:
            self._dispose(entry)
        if self.thread.is_alive() or self.entries:
            raise RuntimeError('Experimental CLI cleanup incomplete.')


class EmptyResource:
    """Count a cold provider's owned root until its call has cleaned up."""
    warm_hit = False

    def close(self):
        pass
