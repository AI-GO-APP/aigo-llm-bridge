"""版本號的單一來源是根目錄的 `VERSION`;這支工具把它同步到程式碼裡的常數,並檢查 CHANGELOG。

為什麼要這支:版本號同時出現在四個地方,任何一個沒跟上都會出事——
- `VERSION`                        tag、Release 與 CHANGELOG 段落都以它為準
- `hosted/bridge/config.py`         Bridge 的 `/healthz` 與 `/worker/heartbeat` 回報
- `worker/aigo_bridge_worker.py`    worker 的心跳與 User-Agent
- `clients/python/aigo_bridge.py`   Python 客戶端的 User-Agent(examples/ 的副本由 sync_clients 同步)

用法:
    python tools/version.py                  # 列出每個地方的版本號
    python tools/version.py --check          # 不一致、或 CHANGELOG 沒有這一版的段落 → 結束碼 1(CI 用)
    python tools/version.py --bump minor     # 或 major / patch / 0.3.0:
                                             #   改 VERSION 與三個常數、同步 examples/、
                                             #   把 CHANGELOG 的 [Unreleased] 改成這一版的段落
    python tools/version.py --newer-than 0.1.0   # VERSION 必須嚴格新於給的版本(PR 檢查用)
    python tools/version.py --notes          # 印出 CHANGELOG 裡這一版的段落(release workflow 用)
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "VERSION"
CHANGELOG = ROOT / "CHANGELOG.md"
# 每個檔案裡寫著 `VERSION = "x.y.z"` 的那一行
CONSTANTS = [
    ROOT / "hosted" / "bridge" / "config.py",
    ROOT / "worker" / "aigo_bridge_worker.py",
    ROOT / "clients" / "python" / "aigo_bridge.py",
]
CONST_RE = re.compile(r'^VERSION = "([^"]+)"$', re.MULTILINE)
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?$")
UNRELEASED = "## [Unreleased]"


def parse(v: str) -> tuple:
    """SemVer 比較:pre-release 排在同版號正式版之前。"""
    base, _, pre = v.partition("-")
    return (tuple(int(c) for c in base.split(".")), 0 if pre else 1, pre)


def read_version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8-sig").strip().splitlines()[0].strip()


def read_constants() -> dict[Path, str | None]:
    out: dict[Path, str | None] = {}
    for path in CONSTANTS:
        m = CONST_RE.search(path.read_text(encoding="utf-8"))
        out[path] = m.group(1) if m else None
    return out


def changelog_has(version: str) -> bool:
    heading = re.compile(rf"^## \[{re.escape(version)}\](?:\s|$)", re.MULTILINE)
    return bool(heading.search(CHANGELOG.read_text(encoding="utf-8")))


def notes(version: str) -> str | None:
    """CHANGELOG 裡 `## [version]` 那一段的內文(不含標題),找不到回 None。"""
    lines = CHANGELOG.read_text(encoding="utf-8").splitlines()
    heading = re.compile(rf"^## \[{re.escape(version)}\](?:\s|$)")
    start = next((i for i, ln in enumerate(lines) if heading.match(ln)), None)
    if start is None:
        return None
    body = []
    for ln in lines[start + 1:]:
        if ln.startswith("## "):
            break
        body.append(ln)
    return "\n".join(body).strip()


def problems() -> list[str]:
    version = read_version()
    found = []
    if not SEMVER_RE.match(version):
        found.append(f"VERSION 不是 x.y.z 格式:{version!r}")
    for path, value in read_constants().items():
        rel = path.relative_to(ROOT).as_posix()
        if value is None:
            found.append(f"{rel} 找不到 VERSION = \"…\" 這一行")
        elif value != version:
            found.append(f"{rel} 是 {value},VERSION 是 {version}")
    if not changelog_has(version):
        found.append(f"CHANGELOG.md 沒有 `## [{version}]` 段落")
    return found


def next_version(current: str, how: str) -> str:
    if SEMVER_RE.match(how):
        return how
    major, minor, patch = parse(current)[0]
    if how == "major":
        return f"{major + 1}.0.0"
    if how == "minor":
        return f"{major}.{minor + 1}.0"
    if how == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise SystemExit(f"--bump 只接受 major / minor / patch 或 x.y.z,收到 {how!r}")


def bump(how: str) -> str:
    current = read_version()
    new = next_version(current, how)
    if parse(new) <= parse(current):
        raise SystemExit(f"新版本 {new} 必須大於目前的 {current}")

    VERSION_FILE.write_bytes(f"{new}\n".encode("utf-8"))
    for path in CONSTANTS:
        text = path.read_text(encoding="utf-8")
        path.write_bytes(CONST_RE.sub(f'VERSION = "{new}"', text, count=1).encode("utf-8"))

    text = CHANGELOG.read_text(encoding="utf-8")
    if UNRELEASED not in text:
        raise SystemExit("CHANGELOG.md 找不到 `## [Unreleased]`,請先補上再 bump")
    today = dt.date.today().isoformat()
    text = text.replace(UNRELEASED, f"{UNRELEASED}\n\n## [{new}] - {today}", 1)
    CHANGELOG.write_bytes(text.encode("utf-8"))

    # examples/ 裡的 Python 客戶端副本也帶著版本號
    subprocess.run([sys.executable, str(ROOT / "tools" / "sync_clients.py")], check=True)
    return new


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows 主控台預設不是 UTF-8
    ap = argparse.ArgumentParser(description="同步與檢查版本號")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="不一致就結束碼 1")
    g.add_argument("--bump", metavar="major|minor|patch|x.y.z")
    g.add_argument("--newer-than", metavar="x.y.z", help="VERSION 必須嚴格新於這個版本")
    g.add_argument("--notes", action="store_true", help="印出 CHANGELOG 裡這一版的段落")
    args = ap.parse_args()

    if args.notes:
        text = notes(read_version())
        if text is None:
            print(f"CHANGELOG.md 沒有 [{read_version()}] 段落", file=sys.stderr)
            return 1
        print(text)
        return 0

    if args.bump:
        new = bump(args.bump)
        print(f"✓ 版本改為 {new}。請在 CHANGELOG.md 的 [{new}] 段落寫下這一版的變更。")
        return 0

    if args.newer_than:
        version = read_version()
        if parse(version) <= parse(args.newer_than):
            print(f"VERSION 是 {version},沒有大於 main 的 {args.newer_than}。"
                  "這個 PR 會改到使用者拿到的內容,請跑 python tools/version.py --bump patch|minor|major")
            return 1
        print(f"✓ VERSION {args.newer_than} → {version}")
        return 0

    if args.check:
        found = problems()
        for line in found:
            print("✗", line)
        if not found:
            print(f"✓ 版本號一致:{read_version()}")
        return 1 if found else 0

    print(f"VERSION                          {read_version()}")
    for path, value in read_constants().items():
        print(f"{path.relative_to(ROOT).as_posix():<32} {value}")
    print(f"CHANGELOG 有 [{read_version()}] 段落   {'是' if changelog_has(read_version()) else '否'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
