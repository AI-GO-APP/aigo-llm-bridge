"""S2:向 Bridge 換一枚短效 session token 給瀏覽器,讓前端直連 Bridge 串流。

source 金鑰只活在這裡(ctx.secrets),不會出現在前端。token 綁定觸發者的平台身分(ctx.user_id)。

前置設定
  外部服務 slug `llm-bridge-spike` → Bridge 的網址(timeout_ms 30000)
  secrets:SPIKE_KEY(Bridge 的 source 金鑰)、BRIDGE_PUBLIC_URL(前端要直連的網址)
"""

import time

SLUG = "llm-bridge-spike"


def execute(ctx):
    key = str(ctx.secrets.get("SPIKE_KEY") or "").strip()
    base = str(ctx.secrets.get("BRIDGE_PUBLIC_URL") or "").strip().rstrip("/")
    if not key or not base:
        ctx.response.json({"ok": False, "error": "尚未設定 SPIKE_KEY 或 BRIDGE_PUBLIC_URL"})
        return
    if not ctx.user_id:
        ctx.response.json({"ok": False, "error": "沒有使用者身分(排程或 webhook 不能換 session token)"})
        return

    t0 = time.time()
    resp = ctx.http.call(SLUG, "/bridge/session", method="POST", body={"user": str(ctx.user_id)},
                         headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    status = int(resp.get("status") or 500)
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    if status >= 400 or not data.get("token"):
        ctx.response.json({"ok": False, "error": f"換 token 失敗({status})", "detail": str(resp.get("data"))[:200]})
        return
    ctx.response.json({
        "ok": True, "token": data["token"], "exp": data.get("exp"), "base_url": base,
        "user": str(ctx.user_id), "bridge_instance": data.get("instance"),
        "elapsed_ms": round((time.time() - t0) * 1000),
    })
