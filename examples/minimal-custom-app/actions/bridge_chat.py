"""伺服器端同步呼叫 Bridge(給不需要串流、或要在 action 裡接著處理結果的情境)。

★ 一定要帶 X-Bridge-Wait: 20 —— Custom App 經 egress 閘道呼叫的硬牆是 30 秒,撞牆時整支 action
  可能被砍;Bridge 20 秒內沒做完就回 202 與工單 id,之後用 op="job" 查結果。

params:
  op = "chat"(預設)  model、messages、reasoning_effort、reasoning、response_format 照 OpenAI 形狀傳
  op = "job"          id:查 202 回來的工單
"""

ALLOWED = ("model", "messages", "reasoning_effort", "reasoning", "thinking", "response_format",
           "max_tokens", "max_completion_tokens")


def _bridge(ctx, method, path, body=None, extra=None):
    key = str(ctx.secrets.get("BRIDGE_KEY") or "").strip()
    if not key:
        return 0, {"error": {"code": "not_configured", "message": "尚未設定 BRIDGE_KEY"}}, {}
    headers = {"Authorization": "Bearer " + key, "X-Bridge-User": str(ctx.user_id or ""),
               "Content-Type": "application/json", **(extra or {})}
    resp = ctx.http.call("llm-bridge", path, method=method, body=body, headers=headers)
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {"raw": str(resp.get("data"))[:200]}
    raw_headers = resp.get("headers") if isinstance(resp.get("headers"), dict) else {}
    return int(resp.get("status") or 500), data, {str(k).lower(): v for k, v in raw_headers.items()}


def execute(ctx):
    if str(ctx.params.get("op") or "chat") == "job":
        status, data, _ = _bridge(ctx, "GET", f"/v1/jobs/{ctx.params.get('id')}")
        ctx.response.json({"ok": status < 400, **data})
        return
    body = {k: ctx.params[k] for k in ALLOWED if ctx.params.get(k) is not None}
    status, data, headers = _bridge(ctx, "POST", "/v1/chat/completions", body, {"X-Bridge-Wait": "20"})
    if status == 202:
        ctx.response.json({"ok": True, "pending": True, "job_id": data.get("id")})
        return
    if status >= 400 or "choices" not in data:
        # egress 在 30 秒時回傳的錯誤,或 Bridge 自己的錯誤,都照實回給畫面
        ctx.response.json({"ok": False, "status": status, "error": (data.get("error") or {}).get("message")
                           or str(data)[:200]})
        return
    # egress 回應不一定帶標頭,所以實際型號與未套用的參數以本體的 x_bridge 為準
    meta = data.get("x_bridge") or {}
    ctx.response.json({"ok": True, "content": data["choices"][0]["message"].get("content"),
                       "usage": data.get("usage"),
                       "served_by": meta.get("served_by") or headers.get("x-bridge-served-by"),
                       "dropped": meta.get("dropped") or headers.get("x-bridge-dropped")})
