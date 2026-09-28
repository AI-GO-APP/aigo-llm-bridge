#!/usr/bin/env python3
"""檢查 repo 裡有沒有被提交的金鑰、token 或不該進版控的檔案。

這是公開 repo:一把金鑰只要進過任何一個 commit,就要當成已外洩處理(換掉),刪檔救不回來。
所以 CI 在每個 PR 與 main 上都跑這支,本機提交前也可以先跑。

檢查兩件事:
  1. 檔案內容:常見的金鑰格式(OpenRouter、Anthropic、OpenAI、GitHub、AWS、Slack、JWT、私鑰),
     以及本套件自己的機敏環境變數被賦予了看起來像真值的內容(`BRIDGE_KEY__X=...` 之類)
  2. 檔名:`*.env`、`.banned-terms`、worker 的 `worker.json`、平台 token 快取等不該被追蹤的檔案

輸出**不印出命中的內容**,只印檔案、行號與規則名稱——公開 repo 的 CI 紀錄是公開的。

誤判時在那一行加上 `scan-secrets: allow`(例如測試裡刻意寫的假金鑰)。

用法:
  python tools/scan_secrets.py              # 檢查目前所有被追蹤的檔案
  python tools/scan_secrets.py --history    # 另外檢查所有 commit 新增過的每一行(CI 用)
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOW = "scan-secrets: allow"

# 套件自己的機敏變數:值至少 16 個「像金鑰的字元」才算,避免 `...`、`<your-key>` 這類佔位誤判
SENSITIVE_VARS = (
    r"BRIDGE_KEY__[A-Z0-9_]+|BRIDGE_KEY|BRIDGE_SESSION_SECRET|OPENROUTER_API_KEY|ANTHROPIC_API_KEY"
    r"|AIGO_TOKEN|AIGO_API_TOKEN|AIGO_PASSWORD|AIGO_DEPLOY_TOKEN__[A-Z0-9_]+|INTERNAL_KEY"
)

RULES: list[tuple[str, re.Pattern[str]]] = [
    ("OpenRouter 金鑰", re.compile(r"sk-or-[A-Za-z0-9_-]{20,}")),
    ("Anthropic 金鑰", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI 金鑰", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("私鑰", re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")),
    ("機敏變數被賦予真值", re.compile(
        rf"\b(?:{SENSITIVE_VARS})\s*[=:]\s*[\"']?[A-Za-z0-9_\-+/]{{16,}}")),
]

# 不該被追蹤的檔名(比對路徑最後一段)
FORBIDDEN_NAMES = re.compile(
    r"^(?:.+\.env|\.env|\.env\..+|\.banned-terms|worker\.json|token\.json|.+\.pem|.+\.key|id_rsa.*)$"
)
FORBIDDEN_OK = re.compile(r"\.example$|\.sample$")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=True).stdout


def scan_line(where: str, line: str) -> list[str]:
    if ALLOW in line:
        return []
    return [f"{where}:{name}" for name, pattern in RULES if pattern.search(line)]


def scan_tracked() -> list[str]:
    hits: list[str] = []
    for rel in git("ls-files", "-z").split("\0"):
        if not rel:
            continue
        name = rel.rsplit("/", 1)[-1]
        if FORBIDDEN_NAMES.match(name) and not FORBIDDEN_OK.search(name):
            hits.append(f"{rel}:不該被追蹤的檔案")
        path = ROOT / rel
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if b"\0" in data[:8000]:   # 二進位檔
            continue
        for i, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
            hits.extend(scan_line(f"{rel}:{i}", line))
    return hits


def scan_history() -> list[str]:
    """所有 commit 新增過的行。只報 commit 與檔名,行號在歷史裡沒有意義。"""
    hits: list[str] = []
    commit, current = "", ""
    log = git("log", "--all", "-p", "--no-color", "--format=commit %H", "--unified=0")
    for line in log.splitlines():
        if line.startswith("commit "):
            commit = line[7:15]
        elif line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else ""
        elif line.startswith("+") and current:
            hits.extend(scan_line(f"(commit {commit}) {current}", line[1:]))
    return sorted(set(hits))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows 主控台預設不是 UTF-8
    hits = scan_tracked()
    if "--history" in sys.argv[1:]:
        hits += scan_history()
    if hits:
        print(f"✗ 發現 {len(hits)} 處疑似機敏資訊(內容不顯示):")
        for h in hits:
            print("  ", h)
        print("\n真的是金鑰的話:先到發行方換掉(已進過 commit 就視為外洩),再移除。"
              f"\n確定是假值的話:在那一行加上 `{ALLOW}`。")
        return 1
    print("✓ 沒有發現機敏資訊")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
