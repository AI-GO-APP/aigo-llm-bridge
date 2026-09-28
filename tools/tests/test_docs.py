"""文件結構檢查:連結都指到存在的檔案、每份文件都列在 README、Release 附件都存在。"""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINK = re.compile(r"\]\(([^)\s]+)\)")


def tracked_markdown() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True,
                         encoding="utf-8", check=True).stdout
    return [ROOT / p for p in out.splitlines() if p]


def test_relative_links_resolve():
    missing = []
    for md in tracked_markdown():
        text = md.read_text(encoding="utf-8")
        text = re.sub(r"```.*?```", "", text, flags=re.S)       # 程式碼區塊裡的不是連結
        for target in LINK.findall(text):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            path = target.split("#")[0]
            if not (md.parent / path).exists():
                missing.append(f"{md.relative_to(ROOT).as_posix()} → {target}")
    assert not missing, "連到不存在的檔案:\n" + "\n".join(missing)


def test_every_doc_is_listed_in_readme():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    unlisted = [p.name for p in sorted((ROOT / "docs").glob("*.md")) if f"docs/{p.name}" not in readme]
    assert not unlisted, f"README 的文件表缺少:{unlisted}"


def test_release_assets_exist():
    text = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assets = re.findall(r"^\s+((?:worker|clients)/\S+)", text, re.M)
    assert assets, "release.yml 沒有列出任何附件"
    assert all((ROOT / a).exists() for a in assets), assets
    names = [a.rsplit("/", 1)[-1] for a in assets]
    assert len(names) == len(set(names)), "Release 附件檔名重複,下載網址會衝突"
    # docs/04 教使用者用這個檔名下載
    assert "aigo_bridge_worker.py" in names


def test_no_leftover_skill_sync_references():
    """0.3.0 移除了 skill 同步機制;文件與設定不該再指向它(CHANGELOG 的歷史紀錄除外)。"""
    stale = []
    for md in tracked_markdown():
        if md.name == "CHANGELOG.md":
            continue
        text = md.read_text(encoding="utf-8")
        for needle in ("check_update", "SKILL.md", "npx skills", "resources/hooks", "SessionStart"):
            if needle in text:
                stale.append(f"{md.relative_to(ROOT).as_posix()}: {needle}")
    assert not stale, stale
