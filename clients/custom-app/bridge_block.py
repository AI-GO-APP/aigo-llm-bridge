"""Custom App Server Action 用的 Bridge 區塊 —— 整段貼進你的 action 檔案(從這行下面到檔尾)。

為什麼是「貼上」而不是 import:
- action 連外一律要走 ctx.http.call,而發布閘門只認得**寫死的字面 slug**。用變數傳進來會被標成
  「動態 slug」,閘門檢查不了授權。所以 slug `llm-bridge` 就寫在下面的呼叫裡;你的外部服務若叫別的
  名字,把那一處字串換掉即可。
- egress 閘道對單次呼叫有 30 秒硬牆,所以每次都帶 X-Bridge-Wait: 20:Bridge 20 秒內沒做完就回 202
  與工單 id,之後用 bridge_job() 查,不會撞牆。

前置設定(一次):
  1. 外部服務:slug `llm-bridge`,base_url = Bridge 網址,timeout_ms 30000,授權給這個 app
  2. secrets:BRIDGE_KEY(Bridge 發給這個 app 的 source 金鑰)、BRIDGE_PUBLIC_URL(Bridge 網址,前端直連用)

回傳值一律是 dict,不丟例外;看 ok 判斷。錯誤代碼見 docs/09 §6。
"""

# ── 從這裡開始貼 ──────────────────────────────────────────────────────────
BRIDGE_WAIT_S = 20        # 留 10 秒給 egress 閘道與 action 本身;不要調到 25 以上


def _bridge(ctx, method, path, body=None, wait=False):
    """回 (status, data)。status 0 = 還沒設定好或連不上。"""
    key = str(ctx.secrets.get("BRIDGE_KEY") or "").strip()
    if not key:
        return 0, {"error": {"code": "not_configured", "message": "尚未設定 BRIDGE_KEY"}}
    headers = {"Authorization": "Bearer " + key, "X-Bridge-User": str(ctx.user_id or ""),
               "Content-Type": "application/json"}
    if wait:
        headers["X-Bridge-Wait"] = str(BRIDGE_WAIT_S)
    # ★ slug 必須是字面字串(發布閘門只認得字面值)
    resp = ctx.http.call("llm-bridge", path, method=method, body=body, headers=headers)
    data = resp.get("data")
    if not isinstance(data, dict):
        data = {"error": {"code": "bad_response", "message": str(data)[:200]}}
    return int(resp.get("status") or 0), data


def _fail(status, data, default):
    err = data.get("error") if isinstance(data.get("error"), dict) else {}
    return {"ok": False, "status": status, "code": err.get("code") or "error",
            "error": err.get("message") or default}


def bridge_chat(ctx, messages, model="auto", **params):
    """同步對話。成功:{"ok", "content", "served_by", "priority", "fallback", "dropped", "usage"};
    20 秒內沒做完:{"ok": True, "pending": True, "job_id"};失敗:{"ok": False, "code", "error"}。

    code == "priority_required":使用者還沒選優先順序 → 畫面上問他,再呼叫 bridge_set_priority。
    """
    status, data = _bridge(ctx, "POST", "/v1/chat/completions",
                           {"model": model, "messages": messages, **params}, wait=True)
    if status == 202:
        return {"ok": True, "pending": True, "job_id": data.get("id")}
    if status >= 400 or status == 0 or "choices" not in data:
        return _fail(status, data, "呼叫失敗")
    meta = data.get("x_bridge") or {}      # egress 拿不到回應標頭,中繼資訊以本體為準
    return {"ok": True, "content": data["choices"][0]["message"].get("content"),
            "served_by": meta.get("served_by"), "priority": meta.get("priority"),
            "fallback": meta.get("fallback"), "dropped": meta.get("dropped") or [], "usage": data.get("usage")}


def bridge_job(ctx, job_id):
    """{"ok", "status": pending|running|done|failed, "content"?, "error"?}"""
    status, data = _bridge(ctx, "GET", f"/v1/jobs/{job_id}")
    if status >= 400 or status == 0:
        return _fail(status, data, "查不到工單")
    out = {"ok": True, "status": data.get("status"), "job_id": job_id}
    if data.get("status") == "done":
        out["content"] = ((data.get("result") or {}).get("choices") or [{}])[0].get("message", {}).get("content")
    if data.get("status") == "failed":
        out["error"] = (data.get("error") or {}).get("message")
    return out


def bridge_get_priority(ctx):
    """{"ok", "priority": "local"|"cloud"|None, "choices": [...]};priority 是 None 代表還沒問過使用者。"""
    status, data = _bridge(ctx, "GET", "/bridge/preferences")
    return _fail(status, data, "讀不到優先順序") if status >= 400 or status == 0 else {"ok": True, **data}


def bridge_set_priority(ctx, priority):
    """priority:"local"(優先用使用者自己電腦上的 Claude Code)或 "cloud"(優先用 OpenRouter)。"""
    # 用 POST:Bridge 的偏好端點 PUT / POST 都收,POST 在 egress 閘道一定支援
    status, data = _bridge(ctx, "POST", "/bridge/preferences", {"priority": priority})
    return _fail(status, data, "儲存失敗") if status >= 400 or status == 0 else {"ok": True, **data}


def bridge_session_token(ctx, ttl=3600):
    """給前端直連串流用的短效 token:{"ok", "token", "exp", "base_url"}(token 綁 ctx.user_id)。"""
    if not ctx.user_id:
        return {"ok": False, "code": "user_required", "error": "需要登入者身分"}
    status, data = _bridge(ctx, "POST", "/bridge/session", {"user": str(ctx.user_id), "ttl": ttl})
    if status >= 400 or status == 0 or not data.get("token"):
        return _fail(status, data, "換 token 失敗")
    return {"ok": True, "token": data["token"], "exp": data.get("exp"),
            "base_url": str(ctx.secrets.get("BRIDGE_PUBLIC_URL") or "").rstrip("/")}


def bridge_enrollment_code(ctx):
    """「連接我的電腦」:一次性綁定碼(10 分鐘內有效),綁定後那台電腦只服務 ctx.user_id 本人。"""
    status, data = _bridge(ctx, "POST", "/bridge/enrollments", {})
    if status >= 400 or status == 0:
        return _fail(status, data, "產生綁定碼失敗")
    return {"ok": True, "code": data.get("code"), "expires_at": data.get("expires_at"),
            "bridge_url": data.get("bridge_url") or str(ctx.secrets.get("BRIDGE_PUBLIC_URL") or "")}


def bridge_computers(ctx):
    """{"ok", "workers": [{"id", "name", "os", "version", "status", "online", "last_seen_at"}]}"""
    status, data = _bridge(ctx, "GET", "/bridge/workers")
    return _fail(status, data, "讀不到電腦清單") if status >= 400 or status == 0 else {"ok": True, **data}


def bridge_revoke_computer(ctx, computer_id):
    status, data = _bridge(ctx, "POST", f"/bridge/workers/{computer_id}/revoke", {})
    return _fail(status, data, "撤銷失敗") if status >= 400 or status == 0 else {"ok": True}
# ── 貼上的區塊到此為止 ────────────────────────────────────────────────────
