"""「連接我的電腦」:產生綁定碼、列出我的電腦、撤銷某台。

params:
  op = "enroll"   產生一次性綁定碼(10 分鐘內有效),worker 用它綁定這位使用者
  op = "list"     列出這位使用者綁定過的電腦與是否在線
  op = "revoke"   撤銷一台(params.id)
一律以平台身分 ctx.user_id 為擁有者 —— 使用者不能替別人綁電腦,也看不到別人的電腦。
"""

WORKER_URL = "https://raw.githubusercontent.com/AI-GO-APP/aigo-llm-bridge/main/worker/aigo_bridge_worker.py"


def _bridge(ctx, method, path, body=None):
    key = str(ctx.secrets.get("BRIDGE_KEY") or "").strip()
    if not key:
        return 0, {"error": {"code": "not_configured", "message": "尚未設定 BRIDGE_KEY"}}
    resp = ctx.http.call("llm-bridge", path, method=method, body=body,
                         headers={"Authorization": "Bearer " + key, "X-Bridge-User": str(ctx.user_id or ""),
                                  "Content-Type": "application/json"})
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {"raw": str(resp.get("data"))[:200]}
    return int(resp.get("status") or 500), data


def execute(ctx):
    if not ctx.user_id:
        ctx.response.json({"ok": False, "error": "需要登入者身分"})
        return
    op = str(ctx.params.get("op") or "list")
    if op == "enroll":
        status, data = _bridge(ctx, "POST", "/bridge/enrollments", {})
        if status >= 400:
            ctx.response.json({"ok": False, "error": (data.get("error") or {}).get("message") or "產生綁定碼失敗"})
            return
        bridge = data.get("bridge_url") or str(ctx.secrets.get("BRIDGE_PUBLIC_URL") or "")
        ctx.response.json({"ok": True, "code": data["code"], "expires_at": data.get("expires_at"),
                           "worker_url": WORKER_URL,
                           "commands": [f"python aigo_bridge_worker.py enroll --bridge {bridge} --code {data['code']}",
                                        "python aigo_bridge_worker.py run"]})
    elif op == "revoke":
        status, data = _bridge(ctx, "POST", f"/bridge/workers/{ctx.params.get('id')}/revoke", {})
        ctx.response.json({"ok": status < 400, "error": None if status < 400 else (data.get("error") or {}).get("message")})
    else:
        status, data = _bridge(ctx, "GET", "/bridge/workers")
        ctx.response.json({"ok": status < 400, "workers": data.get("workers") or [],
                           "error": None if status < 400 else (data.get("error") or {}).get("message")})
