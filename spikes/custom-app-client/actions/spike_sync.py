"""S3:從 Server Action 同步呼叫 Bridge,伺服端刻意延遲 delay_ms 才回,量實際能等多久。

manifest 把這支的 timeout_ms 設成 120000,所以先撞到的應該是 egress 閘道那道牆
(外部服務的 timeout_ms,預設 10000、上限 30000)。撞牆時平台砍的是整支 action,
這裡的程式碼不會執行到回傳那一行——前端要讀 action 回應信封的 status 才看得到。

params: delay_ms(伺服端延遲,毫秒)
"""

import time

SLUG = "llm-bridge-spike"


def execute(ctx):
    key = str(ctx.secrets.get("SPIKE_KEY") or "").strip()
    delay_ms = int(ctx.params.get("delay_ms") or 0)
    t0 = time.time()
    resp = ctx.http.call(SLUG, "/v1/chat/completions", method="POST",
                         body={"model": "spike/echo", "messages": [{"role": "user", "content": "ping"}],
                               "spike": {"delay_ms": delay_ms}},
                         headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    status = int(resp.get("status") or 500)
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    ctx.response.json({
        "ok": status < 400, "http_status": status, "delay_ms": delay_ms,
        "elapsed_ms": round((time.time() - t0) * 1000),
        "server_slept_ms": (data.get("spike") or {}).get("slept_ms"),
        "bridge_instance": (data.get("spike") or {}).get("instance"),
        "detail": None if status < 400 else str(resp.get("data"))[:200],
    })
