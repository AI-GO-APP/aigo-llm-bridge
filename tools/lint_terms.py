#!/usr/bin/env python3
"""檢查 repo 內容有沒有出現「不該出現在通用套件裡」的字詞(客戶、租戶、專案、人名)。

為什麼字詞清單不放在 repo 裡:清單本身就是那些字詞。所以清單從外部讀——

  1. 環境變數 BANNED_TERMS(CI 用;設成 GitHub Actions 的 repository secret——
     不能用 variable,variable 會以明文印在公開的 CI 紀錄裡)
  2. 本機檔案 .banned-terms(已列入 .gitignore)

格式:一行一個,或以逗號分隔;`#` 開頭的行是註解。

比對規則:
  - 純 ASCII 的詞:不分大小寫、以「字邊界」比對(前後不能緊接英數字),避免誤傷一般單字的片段
  - 含非 ASCII 的詞(例如中文):子字串比對

輸出刻意**不印出命中的詞**,只印檔案、行號與詞在清單中的序號——公開 repo 的 CI 紀錄是公開的,
印出來就等於把清單公告了。

用法:
  python tools/lint_terms.py              # 檢查工作區內所有未被忽略的檔案與路徑
  python tools/lint_terms.py --commits    # 另外檢查所有 commit 訊息
  python tools/lint_terms.py --require    # 讀不到清單就視為失敗(本 repo 的 CI 用)
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL_LIST = ROOT / ".banned-terms"


def load_terms() -> list[str]:
    raw = os.environ.get("BANNED_TERMS", "")
    if not raw.strip() and LOCAL_LIST.exists():
        raw = LOCAL_LIST.read_text(encoding="utf-8")
    terms: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        terms.extend(t.strip() for t in line.split(",") if t.strip())
    # 去重但保留順序(序號要穩定,才對得回清單)
    seen: set[str] = set()
    return [t for t in terms if not (t.lower() in seen or seen.add(t.lower()))]


def compile_terms(terms: list[str]) -> list[re.Pattern[str]]:
    patterns = []
    for term in terms:
        escaped = re.escape(term)
        if term.isascii():
            patterns.append(re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.IGNORECASE))
        else:
            patterns.append(re.compile(escaped))
    return patterns


def repo_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout.decode("utf-8")
    return [ROOT / p for p in out.split("\0") if p]


def scan_text(label: str, text: str, patterns: list[re.Pattern[str]]) -> list[str]:
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for idx, pattern in enumerate(patterns, 1):
            if pattern.search(line):
                hits.append(f"{label}:{lineno}: 命中清單第 {idx} 項")
    return hits


def main() -> int:
    # Windows 主控台預設不是 UTF-8(例如 cp950),中文與 ✓ 會讓 print 直接丟例外
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = set(sys.argv[1:])
    terms = load_terms()
    if not terms:
        msg = "讀不到字詞清單(BANNED_TERMS 或 .banned-terms)"
        if "--require" in args:
            print(f"✗ {msg}", file=sys.stderr)
            return 1
        print(f"⚠ {msg},略過檢查")
        return 0
    patterns = compile_terms(terms)

    hits: list[str] = []
    for path in repo_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel == ".banned-terms":
            continue
        hits.extend(scan_text(f"(路徑) {rel}", rel, patterns))
        try:
            text = path.read_bytes().decode("utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue  # 二進位檔或已刪除
        hits.extend(scan_text(rel, text, patterns))

    if "--commits" in args:
        # 作者 email 刻意不檢查:它常含託管平台帳號名,不是 repo 內容能決定的
        proc = subprocess.run(
            ["git", "log", "--format=%H%x00%an%x00%B%x1e"],
            cwd=ROOT, capture_output=True,
        )
        # 還沒有任何 commit 時 git log 會回非零,視為「沒有訊息要檢查」
        log = proc.stdout.decode("utf-8") if proc.returncode == 0 else ""
        for record in filter(None, (r.strip() for r in log.split("\x1e"))):
            sha, name, body = (record.split("\x00") + ["", ""])[:3]
            hits.extend(scan_text(f"(commit {sha[:8]} 作者名)", name, patterns))
            hits.extend(scan_text(f"(commit {sha[:8]} 訊息)", body, patterns))

    if hits:
        print(f"✗ 發現 {len(hits)} 處不該出現在通用套件的字詞:")
        for hit in hits:
            print("  " + hit)
        return 1
    print(f"✓ 已檢查 {len(terms)} 個字詞,沒有命中")
    return 0


if __name__ == "__main__":
    sys.exit(main())
