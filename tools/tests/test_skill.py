"""SKILL.md 與文件的結構檢查:agent 照著走的路徑都要真的存在。

skill 裝在使用者機器上是 main 的鏡像,SKILL.md 指到一個不存在的檔案,agent 就會卡住或自己亂猜。
"""

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "SKILL.md"
# SKILL.md 裡以這些開頭的反引號字串視為 repo 內路徑
PATH_PREFIXES = ("docs/", "tools/", "clients/", "examples/", "worker/", "hosted/", "resources/")
ROOT_FILES = ("CONTEXT.md", "CHANGELOG.md", "CONTRIBUTING.md", "README.md", "VERSION", "LICENSE")


def frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md 開頭必須是 --- 包起來的 frontmatter"
    out: dict[str, str] = {}
    key = None
    for line in m.group(1).splitlines():
        if re.match(r"^[a-z_]+:", line):
            key, _, value = line.partition(":")
            out[key] = value.strip()
        elif key:
            out[key] += " " + line.strip()
    return out


def test_frontmatter():
    meta = frontmatter(SKILL.read_text(encoding="utf-8"))
    assert meta.get("name") == "aigo-llm-bridge"
    desc = meta.get("description", "").lstrip(">").strip()
    # 描述決定 agent 會不會觸發這個 skill:要有內容,也不能超過多數 agent 的上限
    assert 50 < len(desc) <= 1024


def referenced_paths(text: str) -> set[str]:
    found = set()
    for token in re.findall(r"`([^`\s]+)`", text):
        token = token.rstrip("/").split("#")[0]
        if token.startswith(PATH_PREFIXES) or token in ROOT_FILES:
            if "<" in token or "*" in token or "{" in token:
                continue
            found.add(token)
    return found


def test_skill_paths_exist():
    missing = sorted(p for p in referenced_paths(SKILL.read_text(encoding="utf-8"))
                     if not (ROOT / p).exists())
    assert not missing, f"SKILL.md 指到不存在的路徑:{missing}"


def test_readme_links_exist():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    links = re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text)
    local = [link for link in links if not re.match(r"^[a-z]+:", link)]
    missing = sorted(link for link in local if not (ROOT / link).exists())
    assert not missing, f"README 連到不存在的檔案:{missing}"


def test_hook_templates_point_at_update_script():
    claude = json.loads((ROOT / "resources/hooks/claude-code.settings.example.json").read_text(encoding="utf-8"))
    cmd = claude["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    codex = tomllib.loads((ROOT / "resources/hooks/codex.config.example.toml").read_text(encoding="utf-8"))
    cmd2 = codex["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    for c in (cmd, cmd2):
        assert "<SKILL_DIR>/tools/check_update.py" in c
    assert (ROOT / "tools/check_update.py").exists()
