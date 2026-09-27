#!/usr/bin/env python3
"""S4:worker 以固定間隔輪詢一個會縮到零的 Bridge,冷啟動多常命中、代價多大。

兩段:
  gaps   閒置一段時間後打一次(30s、60s、2m、4m、8m、15m),看實例是否換了(= 冷啟動)與延遲
         → 找出「多久沒流量就縮到零」與冷啟動的實際秒數
  steady 以 --interval 秒持續輪詢 --minutes 分鐘,量延遲分佈與實例是否穩定
         → worker 持續輪詢時 Bridge 等於永遠醒著,這一段量那個狀態下的成本

用法:
  python spikes/cold-poll/probe.py --url https://<bridge>.deploy.ai-go.app --key-file <檔案> [--skip-gaps]
key-file 內容:SPIKE_KEY=... 或單行金鑰。輸出 spikes/cold-poll/out/<時間>.json。
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
GAPS = [30, 60, 120, 240, 480, 900]


def read_key(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("SPIKE_KEY="):
            return line.split("=", 1)[1].strip()
    return text.strip()


def hit(client: httpx.Client, url: str, key: str) -> dict:
    t0 = time.perf_counter()
    try:
        r = client.post(url + "/worker/claim", headers={"Authorization": "Bearer " + key}, timeout=120)
        body = r.json()
        return {"ms": round((time.perf_counter() - t0) * 1000), "http": r.status_code,
                "instance": body.get("instance"), "uptime_s": body.get("uptime_s")}
    except (httpx.HTTPError, ValueError) as exc:
        return {"ms": round((time.perf_counter() - t0) * 1000), "error": f"{type(exc).__name__}: {exc}"[:200]}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--key-file", required=True)
    ap.add_argument("--interval", type=float, default=5)
    ap.add_argument("--minutes", type=float, default=10)
    ap.add_argument("--skip-gaps", action="store_true")
    args = ap.parse_args()
    url, key = args.url.rstrip("/"), read_key(Path(args.key_file))
    report: dict = {"when": datetime.now().isoformat(timespec="seconds"), "url": url, "gaps": [], "steady": {}}

    with httpx.Client() as client:
        if not args.skip_gaps:
            prev = hit(client, url, key)
            print("warm-up:", prev, flush=True)
            for gap in GAPS:
                time.sleep(gap)
                r = hit(client, url, key)
                r["gap_s"] = gap
                r["cold"] = bool(r.get("instance") and r.get("instance") != prev.get("instance"))
                report["gaps"].append(r)
                print(f"gap {gap:>4}s → {r}", flush=True)
                prev = r

        samples = []
        end = time.time() + args.minutes * 60
        while time.time() < end:
            samples.append(hit(client, url, key))
            time.sleep(args.interval)
        lat = [s["ms"] for s in samples if "error" not in s]
        report["steady"] = {
            "interval_s": args.interval, "minutes": args.minutes, "n": len(samples),
            "errors": sum(1 for s in samples if "error" in s),
            "instances": sorted({s.get("instance") for s in samples if s.get("instance")}),
            "ms_median": round(statistics.median(lat)) if lat else None,
            "ms_p95": round(sorted(lat)[int(len(lat) * 0.95) - 1]) if lat else None,
            "ms_max": max(lat) if lat else None,
        }
        print("steady:", report["steady"], flush=True)

    out = HERE / "out"
    out.mkdir(exist_ok=True)
    path = out / f"{datetime.now():%Y%m%d-%H%M%S}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("完整輸出:", path)


if __name__ == "__main__":
    main()
