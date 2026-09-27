"""Hosted App 呼叫 Bridge 的最小範例(FastAPI)。

這個服務示範四件事:
  1. 第一次使用先問「優先用哪一個」(GET/PUT /priority),之後 model="auto" 照它主備切換
  2. 同步呼叫(POST /ask),等太久回工單 id,再用 GET /jobs/{id} 取
  3. 串流轉送(POST /ask/stream),把 Bridge 的文字逐段轉給你的前端
  4. 回應一律附上「實際由誰回答」「有沒有用到備援」

身分:Bridge 的 local/* 只替「使用者本人」運算,所以每個呼叫都要帶使用者 id。
這個範例的 current_user() 是佔位 —— 假設上游(例如你的 Custom App 的 Server Action)用共用密鑰
呼叫這個服務並在 X-User-Id 帶平台使用者 id。換成你自己的身分來源即可,但**不要讓瀏覽器自己宣稱身分**。

環境變數:
  BRIDGE_URL        Bridge 網址(https://<your-bridge>.deploy.ai-go.app)
  BRIDGE_KEY        Bridge 發給這個服務的 source 金鑰
  BRIDGE_SOURCE     選填;給了就改用 HMAC 簽章(金鑰不會出現在請求裡)
  INTERNAL_KEY      上游呼叫這個服務用的共用密鑰(佔位身分機制用)
"""

from __future__ import annotations

import hmac
import json
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from aigo_bridge import BridgeClient, BridgeError, Pending

app = FastAPI(title="bridge caller", docs_url=None, redoc_url=None)


def bridge() -> BridgeClient:
    return BridgeClient(os.environ["BRIDGE_URL"], key=os.environ["BRIDGE_KEY"],
                        source=os.environ.get("BRIDGE_SOURCE") or None)


def current_user(request: Request) -> str:
    """佔位的身分來源:只相信帶了正確共用密鑰的上游。換成你自己的登入機制。"""
    expected = os.environ.get("INTERNAL_KEY", "")
    given = request.headers.get("x-internal-key", "")
    if not expected or not hmac.compare_digest(given, expected):
        raise HTTPException(401, "unauthorized")
    user = request.headers.get("x-user-id", "").strip()
    if not user:
        raise HTTPException(400, "X-User-Id 必填")
    return user


@app.exception_handler(BridgeError)
async def bridge_error(_request: Request, exc: BridgeError):
    # 錯誤代碼原樣轉給前端;priority_required 代表要先問使用者(見 /priority)
    headers = {"Retry-After": str(int(exc.retry_after))} if exc.retry_after else {}
    return JSONResponse({"error": {"code": exc.code, "message": exc.message, "fallback": exc.fallback}},
                        status_code=exc.status or 502, headers=headers)


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/priority")
def get_priority(request: Request):
    """priority 是 null → 前端要先讓使用者選(local = 我的電腦的 Claude Code,cloud = OpenRouter)。"""
    return bridge().get_priority(current_user(request))


@app.put("/priority")
async def put_priority(request: Request):
    data = await request.json()
    return bridge().set_priority(current_user(request), str(data.get("priority") or ""))


@app.post("/ask")
async def ask(request: Request):
    user = current_user(request)
    data = await request.json()
    reply = bridge().chat([{"role": "user", "content": str(data.get("prompt") or "")}], user=user,
                          wait=float(data.get("wait") or 60))
    if isinstance(reply, Pending):
        return JSONResponse({"pending": True, "job_id": reply.job_id}, status_code=202)
    return {"content": reply.content, "served_by": reply.served_by, "priority": reply.priority,
            "fallback": reply.fallback, "dropped": reply.dropped}


@app.get("/jobs/{job_id}")
def job(job_id: str, request: Request):
    return bridge().job(job_id, user=current_user(request))


@app.post("/ask/stream")
async def ask_stream(request: Request):
    user = current_user(request)
    data = await request.json()
    events = bridge().stream([{"role": "user", "content": str(data.get("prompt") or "")}], user=user)

    def body():
        # 同步產生器:Starlette 會放到執行緒池跑,不會卡住事件迴圈
        try:
            for event in events:
                payload = {"kind": event.kind, "text": event.text, "error": event.error,
                           "complete": event.complete, "meta": event.meta}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        except BridgeError as exc:   # 串流開始前的錯誤(例:還沒選優先順序)
            yield f"data: {json.dumps({'kind': 'error', 'error': {'code': exc.code, 'message': exc.message}}, ensure_ascii=False)}\n\n"

    return StreamingResponse(body(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
