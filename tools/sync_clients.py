"""把 clients/ 的正本同步進 examples/(或只檢查有沒有飄移)。

    python tools/sync_clients.py           # 寫入
    python tools/sync_clients.py --check   # 只檢查;有差異就結束碼 1(CI 用)

正本:
- clients/browser/bridge.ts       → examples/*/src/lib/bridge.ts(整檔)
- clients/python/aigo_bridge.py   → examples/*/aigo_bridge.py(整檔)
- clients/custom-app/bridge_block.py 的「從這裡開始貼 … 到此為止」區段
                                  → examples/*/actions/*.py 裡同樣標記之間的區段
範例裡的副本只能由這支工具改;直接改副本會在 CI 被擋下。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BROWSER = ROOT / "clients" / "browser" / "bridge.ts"
BLOCK = ROOT / "clients" / "custom-app" / "bridge_block.py"
PYTHON = ROOT / "clients" / "python" / "aigo_bridge.py"
START = "# ── 從這裡開始貼"
END = "# ── 貼上的區塊到此為止"


def block_text() -> str:
    text = BLOCK.read_text(encoding="utf-8")
    start, end = text.index(START), text.index(END)
    end = text.index("\n", end) + 1
    return text[start:end]


def plan() -> list[tuple[Path, str]]:
    """回 [(檔案, 應有的完整內容)]。"""
    out = []
    browser = BROWSER.read_text(encoding="utf-8")
    for target in sorted(ROOT.glob("examples/*/src/lib/bridge.ts")):
        out.append((target, browser))
    python = PYTHON.read_text(encoding="utf-8")
    for target in sorted(ROOT.glob("examples/*/aigo_bridge.py")):
        out.append((target, python))
    block = block_text()
    for action in sorted(ROOT.glob("examples/*/actions/*.py")):
        text = action.read_text(encoding="utf-8")
        if START not in text:
            continue
        start, end = text.index(START), text.index(END)
        end = text.index("\n", end) + 1
        out.append((action, text[:start] + block + text[end:]))
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Windows 主控台預設不是 UTF-8
    check = "--check" in sys.argv[1:]
    stale = []
    for path, wanted in plan():
        if path.read_text(encoding="utf-8") != wanted:
            stale.append(path.relative_to(ROOT).as_posix())
            if not check:
                path.write_bytes(wanted.encode("utf-8"))
    if check and stale:
        print("範例裡的副本和 clients/ 正本不一致(請跑 python tools/sync_clients.py):")
        for name in stale:
            print("  -", name)
        return 1
    print(("已同步:" + ", ".join(stale)) if stale and not check else "✓ 範例與正本一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
