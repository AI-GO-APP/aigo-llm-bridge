#!/usr/bin/env python3
"""S5:Hosted App 本身的時間上限(不經 Custom App 的 egress 閘道)。

三種形狀同時送出,各自記錄「在第幾秒、以什麼方式結束」:
  delay   非串流:伺服端延遲 N 秒才回一個 JSON(整段期間沒有任何位元組)
  hold    串流:每 5 秒送一個心跳,撐 N 秒(量「總長度」上限)
  gap     串流:先送一段、沉默 N 秒、再送一段(量「閒置」上限;local 工單等 worker 就是這個形狀)

  python spikes/hosted-timeout/probe.py --url https://<app>.deploy.ai-go.app --key-file <檔案>
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
DELAYS = [60, 120, 240, 290, 305, 330, 600]
HOLDS = [330, 620]
GAPS = [120, 250, 330]


def read_key(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("SPIKE_KEY="):
            return line.split("=", 1)[1].strip()
    return path.read_text(encoding="utf-8").strip()


def delay_case(url, key, seconds, out):
    t0 = time.monotonic()
    rec = {"shape": "delay", "target_s": seconds}
    try:
        r = httpx.post(url + "/v1/chat/completions", timeout=seconds + 120,
                       headers={"Authorization": f"Bearer {key}"},
                       json={"messages": [{"role": "user", "content": "x"}], "spike": {"delay_ms": seconds * 1000}})
        rec.update(status=r.status_code, body=r.text[:160], server=r.headers.get("server"))
    except httpx.HTTPError as exc:
        rec.update(status=None, error=f"{type(exc).__name__}: {exc}"[:200])
    rec["ended_s"] = round(time.monotonic() - t0, 1)
    out.append(rec)
    print(json.dumps(rec, ensure_ascii=False), flush=True)


def stream_case(url, key, path, shape, seconds, out):
    t0 = time.monotonic()
    rec = {"shape": shape, "target_s": seconds, "events": 0, "done": False}
    try:
        with httpx.stream("GET", url + path, timeout=httpx.Timeout(seconds + 120, connect=15),
                          headers={"Authorization": f"Bearer {key}"}) as r:
            rec["status"] = r.status_code
            for line in r.iter_lines():
                if line.startswith("data: "):
                    rec["events"] += 1
                    rec["last_event_s"] = round(time.monotonic() - t0, 1)
                    if line == "data: [DONE]":
                        rec["done"] = True
    except httpx.HTTPError as exc:
        rec["error"] = f"{type(exc).__name__}: {exc}"[:200]
    rec["ended_s"] = round(time.monotonic() - t0, 1)
    out.append(rec)
    print(json.dumps(rec, ensure_ascii=False), flush=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--key-file", required=True)
    args = ap.parse_args()
    url, key = args.url.rstrip("/"), read_key(Path(args.key_file))
    out: list = []
    threads = [threading.Thread(target=delay_case, args=(url, key, s, out)) for s in DELAYS]
    threads += [threading.Thread(target=stream_case, args=(url, key, f"/v1/sse-hold?seconds={s}", "hold", s, out))
                for s in HOLDS]
    threads += [threading.Thread(target=stream_case, args=(url, key, f"/v1/sse-gap?gap={s}", "gap", s, out))
                for s in GAPS]
    for t in threads:
        t.start()
        time.sleep(0.5)
    for t in threads:
        t.join()
    path = HERE / "out"
    path.mkdir(exist_ok=True)
    f = path / f"{datetime.now():%Y%m%d-%H%M%S}.json"
    f.write_text(json.dumps(sorted(out, key=lambda r: (r["shape"], r["target_s"])), ensure_ascii=False, indent=2),
                 encoding="utf-8")
    print("完整輸出:", f)


if __name__ == "__main__":
    main()
