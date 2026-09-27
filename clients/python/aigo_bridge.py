"""aigo-llm-bridge 的 Python 客戶端(只用標準函式庫;給 Hosted App 或任何伺服器端程式)。

把這一個檔案複製進你的專案即可。Custom App 的 Server Action 不能用它(action 連外一律要走
ctx.http.call),請改用 clients/custom-app/bridge_block.py。

    from aigo_bridge import BridgeClient, Pending

    bridge = BridgeClient("https://<your-bridge>.deploy.ai-go.app", key=os.environ["BRIDGE_KEY"])

    # 第一次使用:問使用者要優先用哪一個,存起來(之後 model="auto" 就照這個主備切換)
    if bridge.get_priority(user)["priority"] is None:
        bridge.set_priority(user, "local")          # 或 "cloud"

    reply = bridge.chat([{"role": "user", "content": "你好"}], user=user)
    if isinstance(reply, Pending):                  # 等太久:工作還在跑,之後用工單 id 取
        reply = bridge.wait_job(reply.job_id, user=user)
    print(reply.content, reply.served_by, reply.fallback)

    for event in bridge.stream([{"role": "user", "content": "寫一首短詩"}], user=user):
        if event.kind == "delta":
            print(event.text, end="")

規則與錯誤代碼見 docs/05-callers.md、docs/09-api-reference.md。
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Iterator

__all__ = ["BridgeClient", "BridgeError", "Reply", "Pending", "StreamEvent"]
VERSION = "0.1.0"


class BridgeError(Exception):
    """Bridge 回的錯誤。code 是穩定的代碼(例 priority_required、no_worker_for_user),message 可以直接給人看。"""

    def __init__(self, status: int, code: str, message: str, *, retry_after: float | None = None,
                 fallback: str | None = None):
        super().__init__(f"{code}: {message}")
        self.status, self.code, self.message = status, code, message
        self.retry_after, self.fallback = retry_after, fallback


@dataclass
class Reply:
    content: str
    model: str
    served_by: str | None
    priority: str | None
    fallback: dict | None            # {"from": 先試的 model, "reason": 錯誤代碼};沒用到備援是 None
    dropped: list[str]
    usage: dict
    raw: dict = field(repr=False)


@dataclass
class Pending:
    """同步等待超過上限:工作仍在進行。用 job_id 查(wait_job / job)。"""
    job_id: str


@dataclass
class StreamEvent:
    kind: str                        # delta | error | done
    text: str = ""                   # delta:這一段新增的文字
    error: dict | None = None        # error:{"code", "message", "job_id"?}
    complete: bool = False           # done:有收到 [DONE] 且沒有 error
    meta: dict = field(default_factory=dict)   # done:served_by / priority / fallback / dropped(能取得的部分)


class BridgeClient:
    def __init__(self, base_url: str, key: str, *, source: str | None = None, timeout: float = 300.0):
        """key = Bridge 發給這個 app 的 source 金鑰(Bridge 端 BRIDGE_KEY__<SOURCE> 的值)。

        給了 source(例 "SALES_APP")就改用 HMAC 簽章,金鑰本身不會出現在請求裡。
        timeout 是單次讀取的秒數;Bridge 同步最多等 280 秒,預設 300 秒剛好罩住。
        """
        self.base = base_url.rstrip("/")
        self.key, self.source, self.timeout = key, source, timeout

    # ── 對話 ─────────────────────────────────────────────────────────────
    def chat(self, messages: list[dict], *, user: str, model: str = "auto", wait: float | None = None,
             conversation: str | None = None, **params) -> Reply | Pending:
        """同步呼叫。params 照 OpenAI 形狀傳(reasoning_effort、reasoning、response_format、max_tokens…)。

        wait:最多等幾秒(1–280),超過回 Pending。不給就用 Bridge 預設(280)。
        """
        body = {"model": model, "messages": messages, **params}
        status, data, _ = self._request("POST", "/v1/chat/completions", body, user=user, wait=wait,
                                        conversation=conversation)
        if status == 202:
            return Pending(job_id=data["id"])
        return _reply(data)

    def stream(self, messages: list[dict], *, user: str, model: str = "auto", conversation: str | None = None,
               **params) -> Iterator[StreamEvent]:
        """串流。最後一定產生一個 kind="done" 的事件;complete=False 代表內容不完整(見 docs/06)。"""
        body = json.dumps({"model": model, "messages": messages, "stream": True, **params}).encode()
        req = self._build("POST", "/v1/chat/completions", body, user=user, conversation=conversation)
        try:
            resp = urllib.request.urlopen(req, timeout=self.timeout)
        except urllib.error.HTTPError as exc:
            raise _error_from(exc.code, exc.read(), exc.headers) from None
        meta = _meta_from_headers(resp.headers)
        saw_done, failed = False, False
        with resp:
            for raw in resp:
                line = raw.decode("utf-8").rstrip("\r\n")
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    saw_done = True
                    continue
                event = json.loads(data)
                if event.get("error"):
                    failed = True
                    yield StreamEvent("error", error=event["error"])
                    continue
                if event.get("x_bridge"):
                    meta.update({k: v for k, v in event["x_bridge"].items() if v is not None})
                for choice in event.get("choices") or []:
                    piece = (choice.get("delta") or {}).get("content")
                    if piece:
                        yield StreamEvent("delta", text=piece)
        yield StreamEvent("done", complete=saw_done and not failed, meta=meta)

    # ── 工單 ─────────────────────────────────────────────────────────────
    def job(self, job_id: str, *, user: str) -> dict:
        """{"id", "status": pending|running|done|failed, "result", "error"}"""
        return self._request("GET", f"/v1/jobs/{job_id}", None, user=user)[1]

    def wait_job(self, job_id: str, *, user: str, timeout: float = 900.0, interval: float = 3.0) -> Reply:
        deadline = time.monotonic() + timeout
        while True:
            state = self.job(job_id, user=user)
            if state["status"] == "done":
                return _reply(state["result"])
            if state["status"] == "failed":
                err = state.get("error") or {}
                raise BridgeError(502, err.get("code") or "failed", err.get("message") or "工作失敗")
            if time.monotonic() >= deadline:
                raise BridgeError(504, "job_wait_timeout", f"等了 {timeout:.0f} 秒還沒完成,工單 {job_id}")
            time.sleep(interval)

    # ── 優先順序(auto 用) ───────────────────────────────────────────────
    def get_priority(self, user: str) -> dict:
        """{"priority": "local"|"cloud"|None, "choices": [{"id", "label", "model", "available"}, ...]}"""
        return self._request("GET", "/bridge/preferences", None, user=user)[1]

    def set_priority(self, user: str, priority: str) -> dict:
        return self._request("PUT", "/bridge/preferences", {"priority": priority}, user=user)[1]

    # ── 使用者的電腦 ─────────────────────────────────────────────────────
    def enrollment_code(self, user: str) -> dict:
        """{"code", "expires_at", "bridge_url"};使用者拿去 `aigo_bridge_worker.py enroll`。"""
        return self._request("POST", "/bridge/enrollments", {}, user=user)[1]

    def computers(self, user: str) -> list[dict]:
        return self._request("GET", "/bridge/workers", None, user=user)[1]["workers"]

    def revoke_computer(self, user: str, computer_id: str) -> None:
        self._request("POST", f"/bridge/workers/{computer_id}/revoke", {}, user=user)

    def session_token(self, user: str, ttl: int = 3600) -> dict:
        """給瀏覽器直連串流用的短效 token:{"token", "exp"}。"""
        return self._request("POST", "/bridge/session", {"user": user, "ttl": ttl}, user=user)[1]

    # ── 內部 ─────────────────────────────────────────────────────────────
    def _build(self, method: str, path: str, body: bytes | None, *, user: str, wait: float | None = None,
               conversation: str | None = None) -> urllib.request.Request:
        headers = {"Content-Type": "application/json", "X-Bridge-User": user or "",
                   "User-Agent": f"aigo-bridge-python/{VERSION}"}
        if self.source:
            ts = str(int(time.time()))
            sig = hmac.new(self.key.encode(), f"{ts}.".encode() + (body or b""), hashlib.sha256).hexdigest()
            headers.update({"X-Bridge-Source": self.source, "X-Bridge-Timestamp": ts,
                            "X-Bridge-Signature": f"sha256={sig}"})
        else:
            headers["Authorization"] = f"Bearer {self.key}"
        if wait is not None:
            headers["X-Bridge-Wait"] = str(int(wait))
        if conversation:
            headers["X-Bridge-Session"] = conversation
        return urllib.request.Request(self.base + path, data=body, method=method, headers=headers)

    def _request(self, method: str, path: str, payload: dict | None, *, user: str, wait: float | None = None,
                 conversation: str | None = None) -> tuple[int, dict, dict]:
        body = None if payload is None else json.dumps(payload).encode()
        req = self._build(method, path, body, user=user, wait=wait, conversation=conversation)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status, json.loads(resp.read() or b"{}"), dict(resp.headers.items())
        except urllib.error.HTTPError as exc:
            raise _error_from(exc.code, exc.read(), exc.headers) from None
        except urllib.error.URLError as exc:
            raise BridgeError(0, "bridge_unreachable", f"連不上 Bridge:{exc.reason}") from None


def _error_from(status: int, raw: bytes, headers) -> BridgeError:
    try:
        err = json.loads(raw or b"{}").get("error") or {}
    except ValueError:
        err = {}
    retry = headers.get("Retry-After") if headers else None
    return BridgeError(status, err.get("code") or f"http_{status}", err.get("message") or f"HTTP {status}",
                       retry_after=float(retry) if retry and retry.replace(".", "", 1).isdigit() else None,
                       fallback=headers.get("X-Bridge-Fallback") if headers else None)


def _meta_from_headers(headers) -> dict:
    meta = {}
    for name, key in (("X-Bridge-Served-By", "served_by"), ("X-Bridge-Priority", "priority")):
        if headers.get(name):
            meta[key] = headers.get(name)
    if headers.get("X-Bridge-Dropped"):
        meta["dropped"] = headers.get("X-Bridge-Dropped").split(",")
    if headers.get("X-Bridge-Fallback"):
        origin, _, reason = headers.get("X-Bridge-Fallback").rpartition(":")
        meta["fallback"] = {"from": origin, "reason": reason}
    return meta


def _reply(data: dict) -> Reply:
    meta = data.get("x_bridge") or {}
    message = ((data.get("choices") or [{}])[0].get("message") or {})
    return Reply(content=message.get("content") or "", model=data.get("model") or "",
                 served_by=meta.get("served_by"), priority=meta.get("priority"), fallback=meta.get("fallback"),
                 dropped=list(meta.get("dropped") or []), usage=data.get("usage") or {}, raw=data)
