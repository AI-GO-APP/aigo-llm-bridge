"""模擬 OpenRouter 的 chat/completions(端到端測試用,不連網、不需要金鑰)。

    uvicorn tools.mock_openrouter:app --port 8791
    Bridge 端設 OPENROUTER_BASE_URL=http://127.0.0.1:8791 與任意 OPENROUTER_API_KEY

POST /_mode {"fail": 503} 讓之後的呼叫一律回那個狀態碼(測備援);{"fail": 0} 恢復。
回答內容固定是「mock-cloud:<model>」,一看就知道是雲端這一側回的。
"""

from __future__ import annotations

import json
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

app = FastAPI()
STATE = {"fail": 0, "calls": 0}


@app.post("/_mode")
async def mode(request: Request):
    STATE["fail"] = int((await request.json()).get("fail") or 0)
    return STATE


@app.get("/_state")
async def state():
    return STATE


@app.post("/chat/completions")
async def chat(request: Request):
    STATE["calls"] += 1
    body = await request.json()
    if STATE["fail"]:
        return JSONResponse({"error": {"code": STATE["fail"], "message": "mock failure"}}, status_code=STATE["fail"])
    model = body.get("model") or "unknown"
    text = f"mock-cloud:{model}"
    usage = {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8, "cost": 0.00001}
    if not body.get("stream"):
        return {"id": "mock-1", "object": "chat.completion", "created": int(time.time()), "model": model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                "usage": usage}

    def events():
        for i in range(0, len(text), 4):
            yield "data: " + json.dumps({"id": "mock-1", "object": "chat.completion.chunk", "model": model,
                                         "choices": [{"index": 0, "delta": {"content": text[i:i + 4]},
                                                      "finish_reason": None}]}) + "\n\n"
        yield "data: " + json.dumps({"id": "mock-1", "object": "chat.completion.chunk", "model": model,
                                     "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                                     "usage": usage}) + "\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
