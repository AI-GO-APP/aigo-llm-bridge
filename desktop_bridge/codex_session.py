"""One app-server connection, one inference; pipes and events remain in RAM."""
import json
import queue
import threading
import time

from .errors import BridgeError
from .process import Child, check_cancel
from .execution_budget import timed


class CodexSession:
    MAX_LINE = 4_000_000
    MAX_BUFFER = 8_000_000

    def __init__(self, command, cwd, env, cancel, timeout, *, generation=None):
        self.cwd = str(cwd)
        with timed('cli_spawn_ms'):
            self.child = Child(command, cwd, env)
        self.messages = queue.Queue(maxsize=4096)
        self.overflow = threading.Event()
        self.lock = threading.Lock()
        self.buffered = 0
        self.next_id = 0
        self.claimed = False
        self.generation = generation
        self.closed = False
        self.closing = False
        self.close_lock = threading.Lock()
        self.sent = {'initialize': 0, 'initialized': 0, 'thread/start': 0, 'turn/start': 0}
        self.idle_work_events = 0
        self.readers = [threading.Thread(target=self._reader, daemon=True),
                        threading.Thread(target=self._drain, daemon=True)]
        try:
            for reader in self.readers:
                reader.start()
            deadline = time.monotonic() + timeout
            with timed('cli_ready_ms'):
                self.response(self.send('initialize', {
                    'clientInfo': {'name': 'aigo_llm_bridge', 'version': '0.2.0'},
                    'capabilities': {'experimentalApi': True}}, cancel, deadline), cancel, deadline)
                self.send('initialized', {}, cancel, deadline, notification=True)
            self.ready_at = time.monotonic()
        except BaseException:
            self.close()
            raise

    def _reader(self):
        try:
            while True:
                line = self.child.proc.stdout.readline(self.MAX_LINE + 1)
                if not line:
                    break
                if len(line) > self.MAX_LINE:
                    self.overflow.set()
                    break
                if not self.claimed:
                    try:
                        event = json.loads(line)
                        if isinstance(event, dict) and str(event.get('method', '')).startswith(('thread/', 'turn/', 'item/')):
                            self.idle_work_events += 1
                            self.overflow.set()
                            break
                    except ValueError:
                        pass
                with self.lock:
                    if self.buffered + len(line) > self.MAX_BUFFER:
                        self.overflow.set()
                        break
                    self.buffered += len(line)
                try:
                    self.messages.put_nowait(line)
                except queue.Full:
                    self.overflow.set()
                    break
        except (OSError, ValueError):
            pass
        finally:
            try:
                self.messages.put_nowait(None)
            except queue.Full:
                self.overflow.set()

    def _drain(self):
        try:
            while self.child.proc.stderr.read(65536):
                pass
        except (OSError, ValueError):
            pass

    def healthy(self):
        return not self.closed and not self.closing and not self.overflow.is_set() and self.child.proc.poll() is None

    def claim(self, cwd):
        with self.lock:
            if self.claimed or not self.healthy() or str(cwd) != self.cwd:
                raise BridgeError(503, 'session_isolation', 'CLI 程序不可重用或移至其他工作目錄。')
            self.claimed = True

    def send(self, method, params, cancel, deadline, *, notification=False):
        check_cancel(cancel, deadline)
        if not self.claimed and method not in {'initialize', 'initialized'}:
            raise BridgeError(503, 'session_isolation', '待命 CLI 不可建立工作。')
        if method in self.sent:
            self.sent[method] += 1
        self.next_id += 1
        message = {'method': method, 'params': params}
        if not notification:
            message['id'] = self.next_id
        self.child.write((json.dumps(message) + '\n').encode(), cancel,
                         max(.001, deadline - time.monotonic()))
        return self.next_id

    def receive(self, cancel, deadline):
        while True:
            check_cancel(cancel, deadline)
            if self.overflow.is_set():
                raise BridgeError(502, 'output_too_large', 'CLI 事件佇列超過上限。')
            try:
                line = self.messages.get(timeout=.05)
            except queue.Empty:
                continue
            if self.overflow.is_set():
                raise BridgeError(502, 'output_too_large', 'CLI 事件佇列超過上限。')
            if line is None:
                raise BridgeError(502, 'provider_error', 'Codex 提前結束。')
            with self.lock:
                self.buffered -= len(line)
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if not isinstance(value, dict):
                raise BridgeError(502, 'invalid_provider_response', 'CLI 事件不是合法物件。')
            if not self.claimed and value.get('method', '').startswith(('thread/', 'turn/', 'item/')):
                self.idle_work_events += 1
                raise BridgeError(503, 'session_isolation', '待命 CLI 出現工作事件。')
            if 'method' in value and 'id' in value:
                raise BridgeError(502, 'tool_execution_blocked', '此服務未開放本機工具或權限問答。')
            if value.get('method') == 'item/started':
                kind = value.get('params', {}).get('item', {}).get('type')
                if kind not in {'userMessage', 'agentMessage', 'reasoning', 'plan'}:
                    raise BridgeError(502, 'tool_execution_blocked', '此服務未開放本機工具。')
            return value

    def response(self, rid, cancel, deadline):
        from .providers import classify
        while True:
            value = self.receive(cancel, deadline)
            if value.get('id') == rid:
                if 'error' in value:
                    raise classify(str(value['error'].get('message', '')))
                return value.get('result', {})

    def close(self):
        with self.close_lock:
            if self.closed:
                return
            self.closing = True
            self.child.close()
            for reader in self.readers:
                if reader.ident is not None:
                    reader.join(timeout=1)
            while True:
                try:
                    self.messages.get_nowait()
                except queue.Empty:
                    break
            self.buffered = 0
            self.closed = True
