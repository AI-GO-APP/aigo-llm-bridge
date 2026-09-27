#!/usr/bin/env python3
"""端到端檢查 model="auto"(本機與雲端主備),用官方 openai 客戶端與 clients/python/aigo_bridge.py。

前提:Bridge 已在跑,雲端那一側指向 tools/mock_openrouter.py(可以控制它故障);
這位使用者的 worker 由本腳本在需要時啟動/停止(--worker 指到 aigo_bridge_worker.py,並已 enroll)。

  python tools/e2e_auto.py --base http://127.0.0.1:8790 --key <source key> --user <user id> \
      --mock http://127.0.0.1:8791 --worker worker/aigo_bridge_worker.py --worker-home <dir>

每一項印「✓ / ✗ 名稱:細節」,全部通過結束碼 0。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "clients" / "python"))
from aigo_bridge import BridgeClient, BridgeError  # noqa: E402

RESULTS: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append(bool(ok))
    print(f"{'✓' if ok else '✗'} {name}:{detail}", flush=True)


def mock_mode(mock: str, fail: int) -> None:
    req = urllib.request.Request(mock + "/_mode", data=json.dumps({"fail": fail}).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10).read()


def start_worker(args) -> subprocess.Popen:
    env = {**os.environ, "AIGO_BRIDGE_WORKER_HOME": args.worker_home, "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.Popen([sys.executable, args.worker, "run"], env=env, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    bridge = BridgeClient(args.base, key=args.key)
    for _ in range(60):
        if any(w["online"] for w in bridge.computers(args.user)):
            return proc
        time.sleep(1)
    raise SystemExit("worker 沒有上線")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    for name in ("--base", "--key", "--user", "--mock", "--worker", "--worker-home"):
        ap.add_argument(name, required=True)
    ap.add_argument("--local-model", default="local/self:haiku")
    args = ap.parse_args()

    from openai import OpenAI, ConflictError

    llm = OpenAI(base_url=args.base + "/v1", api_key=args.key, default_headers={"X-Bridge-User": args.user})
    bridge = BridgeClient(args.base, key=args.key)
    fast = {"reasoning": {"enabled": False}}
    models = [args.local_model, "openrouter/mock/cloud-model"]
    msg = [{"role": "user", "content": "只回一個字:好"}]
    mock_mode(args.mock, 0)

    # 1. 還沒選 → 409,openai SDK 以 ConflictError 呈現
    try:
        llm.chat.completions.create(model="auto", messages=msg, extra_body={"models": models})
        check("未選優先順序會被拒絕", False, "竟然成功了")
    except ConflictError as exc:
        body = exc.body if isinstance(exc.body, dict) else {}
        code = body.get("code") or (body.get("error") or {}).get("code")
        check("未選優先順序會被拒絕", code == "priority_required", f"openai.ConflictError,body code = {code}")

    # 2. 本機優先、worker 沒開 → 雲端,並註明備援
    bridge.set_priority(args.user, "local")
    resp = llm.chat.completions.create(model="auto", messages=msg, extra_body={"models": models, **fast})
    meta = (resp.model_extra or {}).get("x_bridge") or {}
    check("本機優先但電腦沒開 → 改用雲端", resp.choices[0].message.content.startswith("mock-cloud")
          and (meta.get("fallback") or {}).get("reason") == "no_worker_for_user", json.dumps(meta, ensure_ascii=False))

    worker = start_worker(args)
    try:
        # 3. 本機優先、worker 在線 → 本機
        t0 = time.time()
        resp = llm.chat.completions.create(model="auto", messages=msg, extra_body={"models": models, **fast})
        meta = (resp.model_extra or {}).get("x_bridge") or {}
        check("本機優先且電腦在線 → 本機回答", str(meta.get("served_by", "")).startswith("local:")
              and meta.get("fallback") is None, f"{meta.get('served_by')},{time.time() - t0:.1f} 秒")

        # 4. 串流(本機),最後一個 chunk 帶 x_bridge
        text, last = "", None
        for chunk in llm.chat.completions.create(model="auto", messages=msg, stream=True,
                                                 extra_body={"models": models, **fast}):
            if chunk.choices and chunk.choices[0].delta.content:
                text += chunk.choices[0].delta.content
            last = chunk
        tail = (last.model_extra or {}).get("x_bridge") if last else None
        check("串流(本機)", bool(text) and bool(tail) and str(tail.get("served_by", "")).startswith("local:"),
              f"{len(text)} 字,最後一段 x_bridge = {tail}")

        # 5. 雲端優先 → 雲端
        bridge.set_priority(args.user, "cloud")
        reply = bridge.chat(msg, user=args.user, models=models, **fast)
        check("雲端優先 → 雲端回答", reply.content.startswith("mock-cloud") and reply.fallback is None,
              f"{reply.served_by}")

        # 6. 雲端優先、雲端 503 → 本機
        mock_mode(args.mock, 503)
        reply = bridge.chat(msg, user=args.user, models=models, **fast)
        check("雲端故障 → 改用本機", str(reply.served_by).startswith("local:")
              and (reply.fallback or {}).get("reason") == "provider_error", f"{reply.served_by},{reply.fallback}")

        # 7. 串流也會在出字前切換(Python 客戶端)
        events = list(bridge.stream(msg, user=args.user, models=models, **fast))
        done = events[-1]
        check("串流:雲端故障 → 改用本機", done.complete and (done.meta.get("fallback") or {}).get("reason")
              == "provider_error", f"{''.join(e.text for e in events if e.kind == 'delta')!r},{done.meta}")

        # 8. 請求本身錯誤不切換(雲端 400)
        mock_mode(args.mock, 400)
        try:
            bridge.chat(msg, user=args.user, models=models)
            check("請求錯誤不切換", False, "竟然成功了")
        except BridgeError as exc:
            check("請求錯誤不切換", exc.code == "provider_bad_request", exc.code)
    finally:
        mock_mode(args.mock, 0)
        worker.terminate()
        worker.wait(timeout=10)

    # 9. 兩邊都不行(沒有電腦的使用者選本機優先、雲端限流)→ 回雲端的錯誤,並說明本機先失敗了
    nobody = args.user + "-no-computer"
    bridge.set_priority(nobody, "local")
    mock_mode(args.mock, 429)
    try:
        bridge.chat(msg, user=nobody, models=models)
        check("兩邊都失敗", False, "竟然成功了")
    except BridgeError as exc:
        check("兩邊都失敗", exc.code == "provider_rate_limited" and "no_worker_for_user" in (exc.fallback or ""),
              f"{exc.code},先前:{exc.fallback}")
    finally:
        mock_mode(args.mock, 0)

    print(f"\n{sum(RESULTS)}/{len(RESULTS)} 通過")
    return 0 if all(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
