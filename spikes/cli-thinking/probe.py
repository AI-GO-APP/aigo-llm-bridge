#!/usr/bin/env python3
"""S1b:每次呼叫由參數決定模型、effort 與 thinking 時,各組合的延遲、成本、thinking 量與格式遵守度。

變數
  模型      haiku / sonnet / opus(別名;實際解析到的型號記在 resolved_model)
  設定      default(不帶任何參數)/ effort=low / effort=high / thinking_off(MAX_THINKING_TOKENS=0)
  題目      json:系統提示要求只輸出 {"city": "..."};qa:一句話回答的一般問題
每組跑 --runs 次(預設 2)。系統提示與 worker 一致(含「不得提及附加資訊」條款)。

  python spikes/cli-thinking/probe.py [--runs 2] [--models haiku,sonnet,opus]
輸出:spikes/cli-thinking/out/<時間>.json 與終端摘要表。會用執行者本人的 Claude Code 跑數十次短對話。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
HYGIENE = ("對話中由系統附加的資訊(工作目錄、作業系統、帳號 email、組織、日期、模型與額度提示)"
           "只供系統內部使用,絕對不要在回答中提及、引用或推論它們。")
TASKS = {
    "json": ("只輸出一個 JSON 物件,格式為 {\"city\": \"城市名\"},不要輸出任何其他文字、說明或程式碼區塊標記。",
             "台灣的首都是哪一座城市?"),
    "qa": ("用繁體中文,一句話回答。", "為什麼天空是藍色的?"),
}
CONFIGS = {
    "default": ([], {}),
    "effort_low": (["--effort", "low"], {}),
    "effort_high": (["--effort", "high"], {}),
    "thinking_off": ([], {"MAX_THINKING_TOKENS": "0"}),
}


def resolve_claude() -> list[str]:
    found = shutil.which("claude")
    if not found:
        sys.exit("找不到 claude")
    if found.lower().endswith((".cmd", ".bat")):
        m = re.search(r'"%dp0%\\([^"]+\.exe)"', Path(found).read_text(encoding="utf-8", errors="replace"))
        if m and (Path(found).parent / m.group(1)).exists():
            return [str(Path(found).parent / m.group(1))]
    return [found]


def run(claude, model, extra_args, extra_env, system, prompt, cwd) -> dict:
    cmd = claude + ["-p", "--model", model, "--tools", "", "--max-turns", "1", "--strict-mcp-config",
                    "--setting-sources", "", "--no-session-persistence", "--system-prompt", system + HYGIENE,
                    "--output-format", "stream-json", "--include-partial-messages", "--verbose"] + extra_args
    t0 = time.perf_counter()
    marks, text, result, init = {}, "", {}, {}
    proc = subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env={**os.environ, "NO_COLOR": "1", **extra_env})
    proc.stdin.write(prompt.encode("utf-8"))
    proc.stdin.close()
    for raw in proc.stdout:
        try:
            ev = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue
        ms = round((time.perf_counter() - t0) * 1000)
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            init = ev
        elif ev.get("type") == "stream_event":
            inner = ev.get("event") or {}
            delta = inner.get("delta") or {}
            if delta.get("type") == "text_delta":
                marks.setdefault("first_text", ms)
                text += delta.get("text") or ""
            elif delta.get("type") == "thinking_delta":
                marks.setdefault("first_thinking", ms)
            elif inner.get("type") == "message_stop":
                marks.setdefault("message_stop", ms)
        elif ev.get("type") == "result":
            result = ev
    stderr = proc.stderr.read().decode("utf-8", errors="replace")
    code = proc.wait()
    usage = result.get("usage") or {}
    return {"marks_ms": marks, "exit": code, "is_error": result.get("is_error"), "text": text,
            "thinking_tokens": (usage.get("output_tokens_details") or {}).get("thinking_tokens"),
            "output_tokens": usage.get("output_tokens"), "cost_usd": result.get("total_cost_usd"),
            "resolved_model": init.get("model"), "error_tail": (stderr or str(result.get("result") or ""))[-200:]
            if (code or result.get("is_error")) else ""}


def json_ok(text: str) -> bool:
    try:
        data = json.loads(text.strip())
    except ValueError:
        return False
    return (isinstance(data, dict) and set(data) == {"city"}
            and any(name in str(data["city"]) for name in ("台北", "臺北")))


def med(values):
    values = [v for v in values if isinstance(v, (int, float))]
    return round(statistics.median(values), 4 if values and max(values) < 1 else 0) if values else None


def main():
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--models", default="haiku,sonnet,opus")
    args = ap.parse_args()
    claude = resolve_claude()
    rows = []
    with tempfile.TemporaryDirectory(prefix="bridge-thinking-") as tmp:
        for model in args.models.split(","):
            for cfg, (cargs, cenv) in CONFIGS.items():
                for task, (system, prompt) in TASKS.items():
                    for i in range(args.runs):
                        r = run(claude, model, cargs, cenv, system, prompt, tmp)
                        r.update({"model": model, "config": cfg, "task": task, "run": i + 1})
                        if task == "json":
                            r["json_ok"] = json_ok(r["text"])
                        rows.append(r)
                        print(f"{model:<6} {cfg:<12} {task:<4} #{i + 1}: first_text={r['marks_ms'].get('first_text')} "
                              f"stop={r['marks_ms'].get('message_stop')} think={r['thinking_tokens']} "
                              f"cost={r['cost_usd']} resolved={r['resolved_model']} "
                              f"{'json_ok=' + str(r.get('json_ok')) if task == 'json' else ''} "
                              f"{'ERR ' + r['error_tail'] if r['error_tail'] else ''}", flush=True)

    summary = []
    for model in args.models.split(","):
        for cfg in CONFIGS:
            grp = [r for r in rows if r["model"] == model and r["config"] == cfg]
            js = [r for r in grp if r["task"] == "json"]
            summary.append({
                "model": model, "config": cfg, "resolved": next((r["resolved_model"] for r in grp if r["resolved_model"]), None),
                "first_text_ms": med([r["marks_ms"].get("first_text") for r in grp]),
                "message_stop_ms": med([r["marks_ms"].get("message_stop") for r in grp]),
                "thinking_tokens": med([r["thinking_tokens"] for r in grp]),
                "cost_usd": med([r["cost_usd"] for r in grp]),
                "json_ok": f"{sum(1 for r in js if r['json_ok'])}/{len(js)}",
                "errors": sum(1 for r in grp if r["exit"] or r["is_error"]),
            })
    print("\n摘要(中位數):")
    for s in summary:
        print(json.dumps(s, ensure_ascii=False))
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    path = out / f"{datetime.now():%Y%m%d-%H%M%S}.json"
    path.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("完整輸出:", path)


if __name__ == "__main__":
    main()
