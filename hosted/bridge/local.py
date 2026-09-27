"""local/* :把工作交給「呼叫者本人」電腦上的 worker。

核心規則(docs/02):工單的 owner 一定等於 worker 的 owner。找工人、發工單、認領、回報,
每一步都比對一次,不存在「改派給別人」的路徑。

兩個實例之間怎麼傳遞:
  - 同一個實例上有人在等(呼叫端的連線、worker 的長輪詢)→ 走記憶體(Hub),不寫表
  - 不在同一個實例 → 寫表、對方定期讀表
  讀寫表共用每分鐘 600 次的額度,所以逐段文字的寫入最多每秒一次、心跳最多每 30 秒一次。
"""

from __future__ import annotations

import asyncio
import json
import secrets
import time
from typing import AsyncIterator

from .auth import hash_secret, new_secret
from .config import Settings
from .errors import BridgeError
from .providers.base import CallContext
from .store import Store, new_key, now

ALIASES = ("haiku", "sonnet", "opus", "fable")
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # 去掉易混淆的 0 O 1 I
ENROLL_TTL_S = 600
MAX_ATTEMPTS = 2
STREAM_MAX_S = 280          # Hosted 單一請求上限 300 秒,留餘裕
CHUNK_WRITE_EVERY_S = 1.0
LEASE_EXTEND_EVERY_S = 20.0
SEEN_WRITE_EVERY_S = 30.0
UNCLAIMED_GIVE_UP_S = 30.0  # 工單發出 30 秒沒人領,且 worker 心跳已過期 → 失敗


class AsyncAccepted(Exception):
    """同步等待超時:工作仍在進行,回 202 讓呼叫端之後查。"""

    def __init__(self, job_key: str):
        super().__init__(job_key)
        self.job_key = job_key


class Hub:
    """同一個實例內的等待者。"""

    def __init__(self):
        self.job_queues: dict[str, asyncio.Queue] = {}
        self.claim_events: dict[str, asyncio.Event] = {}

    def watch(self, job_key: str) -> asyncio.Queue:
        return self.job_queues.setdefault(job_key, asyncio.Queue())

    def unwatch(self, job_key: str) -> None:
        self.job_queues.pop(job_key, None)

    def publish(self, job_key: str, event: dict) -> bool:
        queue = self.job_queues.get(job_key)
        if queue is None:
            return False
        queue.put_nowait(event)
        return True

    def claim_event(self, owner: str) -> asyncio.Event:
        return self.claim_events.setdefault(owner, asyncio.Event())

    def notify_owner(self, owner: str) -> None:
        event = self.claim_events.get(owner)
        if event:
            event.set()


def parse_alias(model: str) -> str:
    """local/self → "",local/self:haiku → "haiku"。"""
    rest = model.removeprefix("local/")
    name, _, alias = rest.partition(":")
    if name != "self":
        raise BridgeError(400, "unsupported_local_target",
                          "local 後端只接受 local/self(只能用你自己的電腦);沒有指定他人電腦的寫法")
    if alias and alias not in ALIASES:
        raise BridgeError(400, "bad_model_alias", f"local/self: 後面只接受 {', '.join(ALIASES)}")
    return alias


def _text(content) -> str:
    if isinstance(content, str):
        return content
    out = []
    for part in content or []:
        if isinstance(part, dict):
            if part.get("type") in ("text", "input_text"):
                out.append(str(part.get("text") or ""))
            elif part.get("type") in ("image_url", "input_image"):
                raise BridgeError(400, "local_no_images", "local 後端不支援圖片;請改用 anthropic/*")
    return "".join(out)


def render_for_worker(req: dict, alias: str) -> dict:
    """把 OpenAI 形狀的請求攤成 worker 要的「系統提示 + 單一提示」。"""
    if req.get("tools"):
        raise BridgeError(400, "local_no_tools", "local 後端不支援工具呼叫;請改用 anthropic/* 或 openrouter/*")
    system, turns = [], []
    for msg in req.get("messages") or []:
        role = msg.get("role")
        if role in ("system", "developer"):
            text = _text(msg.get("content"))
            if text:
                system.append(text)
        elif role in ("user", "assistant"):
            turns.append((role, _text(msg.get("content"))))
        else:
            raise BridgeError(400, "local_bad_role", f"local 後端不支援 {role} 訊息")
    if not turns or turns[-1][0] != "user":
        raise BridgeError(400, "bad_messages", "最後一則必須是 user 訊息")
    if len(turns) == 1:
        prompt = turns[0][1]
    else:
        history = "\n\n".join(f"[{'使用者' if r == 'user' else '助理'}]\n{t}" for r, t in turns[:-1])
        prompt = (f"以下是先前的對話紀錄:\n<history>\n{history}\n</history>\n\n"
                  f"請回應使用者最新的這則訊息:\n{turns[-1][1]}")
    fmt = req.get("response_format") or {}
    schema = (fmt.get("json_schema") or {}).get("schema") if fmt.get("type") == "json_schema" else None
    if fmt.get("type") == "json_object":
        system.append("只輸出一個合法的 JSON 物件,不要加任何說明文字或程式碼區塊標記。")
    effort = req.get("reasoning_effort")
    return {"system": "\n\n".join(system), "prompt": prompt, "alias": alias, "json_schema": schema,
            "effort": effort if effort in ("low", "medium", "high", "xhigh", "max") else None,
            "max_tokens": req.get("max_completion_tokens") or req.get("max_tokens")}


def _completion(job_key: str, text: str, model_label: str, usage: dict, structured=None) -> dict:
    content = json.dumps(structured, ensure_ascii=False) if structured is not None else text
    return {"id": f"chatcmpl-{job_key}", "object": "chat.completion", "created": int(time.time()),
            "model": model_label, "choices": [{"index": 0, "message": {"role": "assistant", "content": content},
                                               "finish_reason": "stop"}], "usage": usage}


def usage_from_worker(raw: dict | None) -> dict:
    raw = raw or {}
    cached = int(raw.get("cache_read_input_tokens") or 0)
    prompt = int(raw.get("input_tokens") or 0) + cached + int(raw.get("cache_creation_input_tokens") or 0)
    completion = int(raw.get("output_tokens") or 0)
    return {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": prompt + completion,
            "prompt_tokens_details": {"cached_tokens": cached}}


class LocalService:
    def __init__(self, settings: Settings, store: Store, hub: Hub | None = None):
        self.s = settings
        self.store = store
        self.hub = hub or Hub()
        self._worker_cache: dict[str, tuple[float, dict]] = {}
        # 工單結束時清掉暫存的提示;BRIDGE_STORE_PROMPTS=1 時保留供除錯(docs/09 §8)
        self._clear_prompt: dict = {} if settings.store_prompts else {"request_json": None}
        self._last_write: dict[str, float] = {}

    # ── 節流 ─────────────────────────────────────────────────────────────
    def _due(self, key: str, every: float) -> bool:
        t = time.monotonic()
        if t - self._last_write.get(key, 0.0) >= every:
            self._last_write[key] = t
            return True
        return False

    # ── 呼叫端 ───────────────────────────────────────────────────────────
    async def online_worker(self, owner: str) -> dict | None:
        rows = await self.store.find("workers", [("owner", "eq", owner), ("status", "eq", "active"),
                                                 ("last_seen_ts", "gte", now() - self.s.worker_heartbeat_ttl_s)],
                                     sort="-last_seen_ts", limit=5)
        return rows[0] if rows else None

    async def create_job(self, ctx: CallContext, req: dict, *, provider: str = "local") -> dict:
        if not ctx.user:
            raise BridgeError(400, "user_required", "local 後端需要呼叫者身分(X-Bridge-User 或 session token)")
        alias = parse_alias(ctx.model_label) if provider == "local" else ""
        payload = render_for_worker(req, alias) if provider == "local" else {}
        if provider == "local" and not await self.online_worker(ctx.user):
            raise BridgeError(409, "no_worker_for_user",
                              "你的電腦目前沒有連線的 worker。請先在 app 內「連接我的電腦」並保持 worker 執行,"
                              "或改用 anthropic/* 後端")
        job = await self.store.insert("jobs", {
            "key": new_key(), "owner": ctx.user, "source": ctx.source, "provider": provider,
            "model": ctx.model_label, "status": "pending" if provider == "local" else "running",
            "worker_key": "", "session": ctx.session, "request_json": payload, "partial_text": "",
            "result_json": None, "error_json": None, "attempts": 0, "created_ts": now(),
            "lease_until_ts": 0, "done_ts": 0,
        })
        ctx.job_id = job["key"]
        if provider == "local":
            self.hub.notify_owner(ctx.user)
        return job

    async def _events(self, job: dict, max_wait: float) -> AsyncIterator[dict]:
        """產生 {"type": "delta", "text"} / {"type": "done", ...} / {"type": "failed", ...}。"""
        key = job["key"]
        queue = self.hub.watch(key)
        sent = ""
        deadline = time.monotonic() + max_wait
        created = job.get("created_ts") or now()
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise AsyncAccepted(key)
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=min(1.0, remaining))
                except asyncio.TimeoutError:
                    event = await self._poll_job(key, created)
                    if event is None:
                        continue
                if event["type"] in ("chunk", "done"):
                    text = event.get("text") or ""
                    if len(text) > len(sent) and text.startswith(sent):
                        yield {"type": "delta", "text": text[len(sent):]}
                        sent = text
                if event["type"] in ("done", "failed"):
                    yield event
                    return
        finally:
            self.hub.unwatch(key)

    async def _poll_job(self, key: str, created: float) -> dict | None:
        row = await self.store.by_key("jobs", key)
        if not row:
            return {"type": "failed", "error": {"code": "job_missing", "message": "工單不見了"}}
        status = row.get("status")
        if status == "done":
            result = row.get("result_json") or {}
            return {"type": "done", "text": result.get("text") or "", "result": result}
        if status == "failed":
            return {"type": "failed", "error": row.get("error_json") or {"code": "failed", "message": "worker 回報失敗"}}
        if status == "pending" and now() - created > UNCLAIMED_GIVE_UP_S:
            if not await self.online_worker(row.get("owner") or ""):
                err = {"code": "worker_offline", "message": "你的 worker 在工單送出後離線了"}
                await self.store.update("jobs", row, {"status": "failed", "error_json": err, "done_ts": now(),
                                                      **self._clear_prompt})
                return {"type": "failed", "error": err}
        if row.get("partial_text"):
            return {"type": "chunk", "text": row["partial_text"]}
        return None

    async def complete(self, req: dict, ctx: CallContext) -> dict:
        job = await self.create_job(ctx, req)
        async for event in self._events(job, self.s.sync_timeout_s):
            if event["type"] == "done":
                return self._finish(job["key"], event, ctx)
            if event["type"] == "failed":
                raise BridgeError(502, event["error"].get("code", "worker_failed"), event["error"].get("message", ""))
        raise AsyncAccepted(job["key"])

    def _finish(self, job_key: str, event: dict, ctx: CallContext) -> dict:
        result = event.get("result") or {}
        ctx.usage = usage_from_worker(result.get("usage"))
        ctx.served_by = f"local:{result.get('model') or 'claude'}"
        return _completion(job_key, result.get("text") or event.get("text") or "", ctx.model_label, ctx.usage,
                           result.get("structured"))

    async def stream(self, req: dict, ctx: CallContext) -> AsyncIterator[dict]:
        job = await self.create_job(ctx, req)
        cid = f"chatcmpl-{job['key']}"
        base = {"id": cid, "object": "chat.completion.chunk", "created": int(time.time()), "model": ctx.model_label}
        include_usage = bool((req.get("stream_options") or {}).get("include_usage"))
        yield {**base, "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}]}
        try:
            async for event in self._events(job, STREAM_MAX_S):
                if event["type"] == "delta":
                    yield {**base, "choices": [{"index": 0, "delta": {"content": event["text"]}, "finish_reason": None}]}
                elif event["type"] == "done":
                    final = self._finish(job["key"], event, ctx)
                    last = {**base, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
                    if include_usage:
                        last["usage"] = final["usage"]
                    yield last
                elif event["type"] == "failed":
                    yield {"error": {**event["error"], "provider_status": None}}
        except AsyncAccepted:
            yield {"error": {"code": "stream_timeout", "provider_status": None, "job_id": job["key"],
                             "message": "串流超過單一連線上限;工作仍在進行,請用 GET /v1/jobs/{id} 取結果"}}

    # ── 綁定(由 app 的 Server Action 代表使用者發起)──────────────────────
    async def create_enrollment(self, source: str, owner: str) -> dict:
        if not owner:
            raise BridgeError(400, "user_required", "綁定碼要屬於某位使用者(X-Bridge-User)")
        raw = "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))
        code = f"{raw[:4]}-{raw[4:]}"
        expires = now() + ENROLL_TTL_S
        await self.store.insert("enrollments", {"key": new_key(), "code_hash": hash_secret(raw), "owner": owner,
                                                "source": source, "expires_ts": expires, "used_ts": 0,
                                                "worker_key": ""})
        return {"code": code, "expires_at": int(expires), "bridge_url": self.s.public_url}

    async def list_workers(self, owner: str) -> list[dict]:
        rows = await self.store.find("workers", [("owner", "eq", owner)], sort="-last_seen_ts", limit=20)
        cutoff = now() - self.s.worker_heartbeat_ttl_s
        return [{"id": r["key"], "name": r.get("name"), "os": r.get("os"), "version": r.get("version"),
                 "status": r.get("status"), "online": r.get("status") == "active" and (r.get("last_seen_ts") or 0) >= cutoff,
                 "last_seen_at": int(r.get("last_seen_ts") or 0)} for r in rows]

    async def revoke_worker(self, owner: str, worker_key: str) -> None:
        row = await self.store.by_key("workers", worker_key)
        if not row or row.get("owner") != owner:
            raise BridgeError(404, "not_found", "找不到這台電腦")
        await self.store.update("workers", row, {"status": "revoked"})
        self._worker_cache.pop(row.get("key_hash") or "", None)

    # ── worker 面 ────────────────────────────────────────────────────────
    async def enroll(self, code: str, name: str, os_name: str, version: str, models: list) -> dict:
        raw = code.replace("-", "").strip().upper()
        rows = await self.store.find("enrollments", [("code_hash", "eq", hash_secret(raw))], limit=1)
        row = rows[0] if rows else None
        if not row or (row.get("used_ts") or 0) > 0 or (row.get("expires_ts") or 0) < now():
            raise BridgeError(400, "bad_enrollment_code", "綁定碼無效、已使用或已過期(10 分鐘內有效),請回 app 重新產生")
        device_key = new_secret("bwk")
        worker = await self.store.insert("workers", {
            "key": new_key(), "owner": row["owner"], "key_hash": hash_secret(device_key), "name": name[:80],
            "os": os_name[:40], "version": version[:40], "models": models or [], "status": "active",
            "last_seen_ts": now(), "created_ts": now()})
        await self.store.update("enrollments", row, {"used_ts": now(), "worker_key": worker["key"]})
        return {"worker_id": worker["key"], "device_key": device_key}

    async def worker_from_key(self, device_key: str) -> dict:
        digest = hash_secret(device_key)
        cached = self._worker_cache.get(digest)
        if cached and time.monotonic() - cached[0] < 30:
            worker = cached[1]
        else:
            rows = await self.store.find("workers", [("key_hash", "eq", digest)], limit=1)
            worker = rows[0] if rows else None
            if worker:
                self._worker_cache[digest] = (time.monotonic(), worker)
        if not worker or worker.get("status") != "active":
            raise BridgeError(401, "bad_device_key", "設備鑰匙無效或已撤銷")
        return worker

    async def touch(self, worker: dict, extra: dict | None = None) -> None:
        if extra or self._due("seen:" + worker["key"], SEEN_WRITE_EVERY_S):
            await self.store.update("workers", worker, {"last_seen_ts": now(), **(extra or {})})

    async def _claimable(self, owner: str) -> list[dict]:
        pending = await self.store.find("jobs", [("owner", "eq", owner), ("provider", "eq", "local"),
                                                 ("status", "eq", "pending")], sort="created_ts", limit=5)
        if pending:
            return pending
        stale = []
        for status in ("leased", "running"):
            stale += await self.store.find("jobs", [("owner", "eq", owner), ("provider", "eq", "local"),
                                                    ("status", "eq", status), ("lease_until_ts", "lte", now())],
                                           sort="created_ts", limit=5)
        return stale

    async def claim(self, worker: dict) -> dict | None:
        owner = worker["owner"]
        await self.touch(worker)
        deadline = time.monotonic() + self.s.claim_wait_s
        event = self.hub.claim_event(owner)
        while True:
            for job in await self._claimable(owner):
                if job.get("owner") != owner:        # 雙重保險:表查詢之外再比一次
                    continue
                if (job.get("attempts") or 0) >= MAX_ATTEMPTS:
                    err = {"code": "worker_lost", "message": "worker 兩次都沒有完成這張工單"}
                    await self.store.update("jobs", job, {"status": "failed", "error_json": err,
                                                          "done_ts": now(), **self._clear_prompt})
                    self.hub.publish(job["key"], {"type": "failed", "error": err})
                    continue
                leased = await self.store.update("jobs", job, {
                    "status": "leased", "worker_key": worker["key"], "attempts": (job.get("attempts") or 0) + 1,
                    "lease_until_ts": now() + self.s.lease_s})
                confirm = await self.store.by_key("jobs", job["key"])
                if confirm and confirm.get("worker_key") == worker["key"]:
                    return {"job_id": leased["key"], "session": leased.get("session") or "",
                            "lease_s": self.s.lease_s, **(leased.get("request_json") or {})}
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            event.clear()
            try:
                await asyncio.wait_for(event.wait(), timeout=min(3.0, remaining))
            except asyncio.TimeoutError:
                pass

    async def _own_job(self, worker: dict, job_key: str) -> dict:
        job = await self.store.by_key("jobs", job_key)
        if not job or job.get("worker_key") != worker["key"] or job.get("owner") != worker["owner"]:
            raise BridgeError(404, "not_found", "找不到這張工單,或它不屬於這台 worker")
        if job.get("status") in ("done", "failed"):
            raise BridgeError(409, "job_closed", "這張工單已經結束")
        return job

    async def chunk(self, worker: dict, job_key: str, text: str) -> None:
        delivered = self.hub.publish(job_key, {"type": "chunk", "text": text})
        if delivered and not self._due("lease:" + job_key, LEASE_EXTEND_EVERY_S):
            return   # 本實例有人在等,而且租約最近才延長過:不必寫表
        if not delivered and not self._due("chunk:" + job_key, CHUNK_WRITE_EVERY_S):
            return
        job = await self._own_job(worker, job_key)
        patch = {"status": "running", "lease_until_ts": now() + self.s.lease_s}
        if not delivered:
            patch["partial_text"] = text
        await self.store.update("jobs", job, patch)

    async def result(self, worker: dict, job_key: str, payload: dict) -> dict:
        job = await self._own_job(worker, job_key)
        result = {"text": str(payload.get("text") or ""), "structured": payload.get("structured"),
                  "usage": payload.get("usage") or {}, "cost_usd": payload.get("cost_usd"),
                  "model": payload.get("model"), "session": payload.get("session") or ""}
        await self.store.update("jobs", job, {"status": "done", "result_json": result, "done_ts": now(),
                                              "partial_text": "", **self._clear_prompt})
        self.hub.publish(job_key, {"type": "done", "text": result["text"], "result": result})
        return job

    async def fail(self, worker: dict, job_key: str, error: dict) -> None:
        job = await self._own_job(worker, job_key)
        err = {"code": str(error.get("code") or "worker_failed")[:40], "message": str(error.get("message") or "")[:300]}
        await self.store.update("jobs", job, {"status": "failed", "error_json": err, "done_ts": now(),
                                              **self._clear_prompt})
        self.hub.publish(job_key, {"type": "failed", "error": err})
