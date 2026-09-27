"""S2–S4 共用的 Hosted App:模擬 Bridge 的對外形狀,但**不呼叫任何模型**。

端點
  GET  /healthz                    版本、實例、uptime(uptime 很小 = 剛冷啟動)
  POST /bridge/session             source 金鑰 → 短效 session token(S2)
  POST /v1/chat/completions        OpenAI 形狀;stream=true 走 SSE(S2),否則延遲 N 毫秒才回(S3)
  GET  /v1/sse-hold?seconds=N      SSE 撐 N 秒、每 5 秒一個心跳,量平台對長連線的截斷(S2)
  GET  /v1/sse-gap?gap=N           SSE 先送一段、沉默 N 秒、再送一段,量閒置逾時(local 工單等 worker 時就是這個形狀)
  POST /worker/claim               模擬 worker 輪詢,回實例與 uptime,量冷啟動命中(S4)

驗證:Authorization: Bearer <SPIKE_KEY>,或 Bearer <session token>。
session token = base64url(user) "." exp "." HMAC-SHA256(SPIKE_KEY, "session|user|exp")[:32]
"""

import asyncio
import base64
import hashlib
import hmac
import json
import os
import time
import uuid

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

VERSION = os.environ.get("SPIKE_VERSION", "spike-3")
BOOT = time.time()
INSTANCE = uuid.uuid4().hex[:8]
KEY = os.environ.get("SPIKE_KEY", "")
SESSION_TTL = 3600

app = FastAPI(title="llm-bridge spike echo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Bridge-Session", "X-Bridge-Async"],
    expose_headers=["X-Spike-Instance", "X-Spike-Uptime"],
)


def _meta() -> dict:
    return {"version": VERSION, "instance": INSTANCE, "uptime_s": round(time.time() - BOOT, 1)}


@app.middleware("http")
async def _stamp(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Spike-Instance"] = INSTANCE
    resp.headers["X-Spike-Uptime"] = str(round(time.time() - BOOT, 1))
    return resp


def _sign(payload: str) -> str:
    return hmac.new(KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]


def _mint(user: str) -> tuple[str, int]:
    exp = int(time.time()) + SESSION_TTL
    u = base64.urlsafe_b64encode(user.encode()).decode().rstrip("=")
    return f"{u}.{exp}.{_sign(f'session|{user}|{exp}')}", exp


def _auth(authorization: str | None) -> dict:
    """回 {"kind": "key"|"session", "user": ...};驗不過丟 401。"""
    if not KEY:
        raise HTTPException(503, "服務尚未設定 SPIKE_KEY")
    raw = (authorization or "").removeprefix("Bearer ").strip()
    if raw and hmac.compare_digest(raw, KEY):
        return {"kind": "key", "user": None}
    parts = raw.split(".")
    if len(parts) == 3:
        u, exp_raw, sig = parts
        try:
            user = base64.urlsafe_b64decode(u + "=" * (-len(u) % 4)).decode()
            exp = int(exp_raw)
        except (ValueError, UnicodeDecodeError):
            raise HTTPException(401, "token 格式不對")
        if exp < time.time():
            raise HTTPException(401, "token 已過期")
        if hmac.compare_digest(sig, _sign(f"session|{user}|{exp}")):
            return {"kind": "session", "user": user}
    raise HTTPException(401, "憑證不正確")


@app.get("/healthz")
async def healthz():
    return {"ok": True, **_meta()}


@app.post("/bridge/session")
async def session(request: Request, authorization: str | None = Header(default=None)):
    if _auth(authorization)["kind"] != "key":
        raise HTTPException(403, "只有 source 金鑰能換 session token")
    body = await request.json()
    user = str(body.get("user") or "").strip()
    if not user:
        raise HTTPException(400, "user 必填")
    token, exp = _mint(user)
    return {"token": token, "exp": exp, **_meta()}


def _completion(text: str, model: str) -> dict:
    return {
        "id": "chatcmpl-" + uuid.uuid4().hex[:12], "object": "chat.completion", "created": int(time.time()),
        "model": model, "choices": [{"index": 0, "message": {"role": "assistant", "content": text},
                                     "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": len(text), "total_tokens": len(text)},
    }


@app.post("/v1/chat/completions")
async def chat(request: Request, authorization: str | None = Header(default=None)):
    who = _auth(authorization)
    body = await request.json()
    opts = body.get("spike") or {}
    model = str(body.get("model") or "spike/echo")
    delay_ms = max(0, min(int(opts.get("delay_ms", 0)), 900_000))   # 量平台上限用,刻意放寬到 15 分鐘
    t0 = time.time()

    if not body.get("stream"):
        await asyncio.sleep(delay_ms / 1000)
        out = _completion("echo", model)
        out["spike"] = {**_meta(), "slept_ms": round((time.time() - t0) * 1000), "auth": who["kind"]}
        return JSONResponse(out)

    tokens = max(1, min(int(opts.get("tokens", 20)), 2000))
    interval = max(0, min(int(opts.get("interval_ms", 100)), 10_000))

    async def stream():
        cid = "chatcmpl-" + uuid.uuid4().hex[:12]
        head = {"id": cid, "object": "chat.completion.chunk", "created": int(time.time()), "model": model}
        await asyncio.sleep(delay_ms / 1000)
        for i in range(tokens):
            chunk = {**head, "choices": [{"index": 0, "delta": {"content": f"字{i + 1} "}, "finish_reason": None}]}
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            await asyncio.sleep(interval / 1000)
        done = {**head, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                "spike": {**_meta(), "elapsed_ms": round((time.time() - t0) * 1000), "auth": who["kind"],
                          "user": who["user"]}}
        yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/v1/sse-hold")
async def sse_hold(seconds: int = Query(60, ge=1, le=900), authorization: str | None = Header(default=None),
                   token: str | None = Query(None)):
    # EventSource 不能帶 header,所以也接受 ?token=
    _auth(authorization or (f"Bearer {token}" if token else None))
    t0 = time.time()

    async def stream():
        n = 0
        while time.time() - t0 < seconds:
            n += 1
            yield f"data: {json.dumps({'n': n, 'elapsed_s': round(time.time() - t0, 1), **_meta()})}\n\n"
            await asyncio.sleep(5)
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/v1/sse-gap")
async def sse_gap(gap: int = Query(60, ge=1, le=900), authorization: str | None = Header(default=None),
                  token: str | None = Query(None)):
    _auth(authorization or (f"Bearer {token}" if token else None))
    t0 = time.time()

    async def stream():
        yield f"data: {json.dumps({'phase': 'start', **_meta()})}\n\n"
        await asyncio.sleep(gap)
        yield f"data: {json.dumps({'phase': 'end', 'elapsed_s': round(time.time() - t0, 1), **_meta()})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/worker/claim")
async def claim(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return {"jobs": [], **_meta()}
