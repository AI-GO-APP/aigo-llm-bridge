"""tools/version.py:在一份暫存的 repo 副本上跑,不動到真的檔案。"""

import importlib.util
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FILES = ["VERSION", "CHANGELOG.md", "hosted/bridge/config.py", "worker/aigo_bridge_worker.py",
         "clients/python/aigo_bridge.py"]


@pytest.fixture
def repo(tmp_path, monkeypatch):
    for rel in FILES:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)
    spec = importlib.util.spec_from_file_location("version_tool", ROOT / "tools" / "version.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setattr(mod, "VERSION_FILE", tmp_path / "VERSION")
    monkeypatch.setattr(mod, "CHANGELOG", tmp_path / "CHANGELOG.md")
    monkeypatch.setattr(mod, "CONSTANTS", [tmp_path / rel for rel in FILES[2:]])
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: None)   # 不跑 sync_clients
    return mod, tmp_path


def test_real_repo_is_consistent():
    spec = importlib.util.spec_from_file_location("version_tool_real", ROOT / "tools" / "version.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.problems() == []


def test_mismatch_is_reported(repo):
    mod, root = repo
    (root / "VERSION").write_text("9.9.9\n", encoding="utf-8")
    found = mod.problems()
    assert any("config.py" in p for p in found)
    assert any("CHANGELOG" in p for p in found)


@pytest.mark.parametrize("how,expected", [("patch", "+0.0.1"), ("minor", "+0.1.0"), ("major", "+1.0.0")])
def test_bump_updates_everything(repo, how, expected):
    mod, root = repo
    before = mod.read_version()
    new = mod.bump(how)
    assert new == mod.next_version(before, how)
    assert mod.problems() == []
    text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    assert text.index("## [Unreleased]") < text.index(f"## [{new}]")


def test_bump_refuses_to_go_backwards(repo):
    mod, _ = repo
    with pytest.raises(SystemExit):
        mod.bump("0.0.1")


def test_compare_rules():
    spec = importlib.util.spec_from_file_location("version_tool_cmp", ROOT / "tools" / "version.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.parse("0.10.0") > mod.parse("0.9.9")
    assert mod.parse("1.0.0") > mod.parse("1.0.0-rc1")


def test_notes(repo):
    mod, _ = repo
    assert mod.notes(mod.read_version())
    assert mod.notes("99.0.0") is None
