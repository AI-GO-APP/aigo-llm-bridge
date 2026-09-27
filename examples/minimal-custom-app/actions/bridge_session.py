"""換一枚短效 session token 給瀏覽器,讓前端直連 Bridge 串流(source 金鑰只留在伺服器)。

前置:外部服務 `llm-bridge`(指向 Bridge 網址,timeout_ms 30000)授權給本 app;
secrets `BRIDGE_KEY`(Bridge 發給本 app 的 source 金鑰)、`BRIDGE_PUBLIC_URL`(前端要直連的網址)。
"""


def _bridge(ctx, method, path, body=None):
    key = str(ctx.secrets.get("BRIDGE_KEY") or "").strip()
    if not key:
        return 0, {"error": {"code": "not_configured", "message": "尚未設定 BRIDGE_KEY"}}
    # ★ slug 一定要寫字面值:發布閘門只認得字面 slug,用變數傳入就檢查不到授權
    resp = ctx.http.call("llm-bridge", path, method=method, body=body,
                         headers={"Authorization": "Bearer " + key, "X-Bridge-User": str(ctx.user_id or ""),
                                  "Content-Type": "application/json"})
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {"raw": str(resp.get("data"))[:200]}
    return int(resp.get("status") or 500), data


def execute(ctx):
    if not ctx.user_id:
        ctx.response.json({"ok": False, "error": "需要登入者身分"})
        return
    status, data = _bridge(ctx, "POST", "/bridge/session", {"user": str(ctx.user_id), "ttl": 3600})
    if status >= 400 or not data.get("token"):
        ctx.response.json({"ok": False, "status": status, "error": (data.get("error") or {}).get("message")
                           or "換 token 失敗"})
        return
    ctx.response.json({"ok": True, "token": data["token"], "exp": data.get("exp"),
                       "base_url": str(ctx.secrets.get("BRIDGE_PUBLIC_URL") or "").rstrip("/")})
