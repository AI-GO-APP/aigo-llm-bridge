"""tools/check_update.py:全部在暫存目錄裡跑,網路以假的 _fetch／_fetch_bytes 取代。

狀態檔與 SKILL_DIR 都改指到暫存目錄,不會登記或同步到這台機器上真正的安裝。
"""

import importlib.util
import io
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def make_zip(files: dict[str, str], top: str = "aigo-llm-bridge-main") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for rel, content in files.items():
            zf.writestr(f"{top}/{rel}", content)
    return buf.getvalue()


@pytest.fixture
def cu(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("check_update", ROOT / "tools" / "check_update.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    install = tmp_path / "install"
    install.mkdir()
    (install / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    monkeypatch.setattr(mod, "SKILL_DIR", install)
    monkeypatch.setattr(mod, "STATE_FILE", tmp_path / "state.json")
    calls = {"version": 0}

    def fake_fetch(url):
        if url == mod.REMOTE_VERSION_URL:
            calls["version"] += 1
            return "0.2.0\n"
        if url == mod.REMOTE_CHANGELOG_URL:
            return "# Changelog\n\n## [0.2.0] - 2026-01-01\n\n### Added\n- 新東西\n\n## [0.1.0]\n"
        return None

    monkeypatch.setattr(mod, "_fetch", fake_fetch)
    monkeypatch.setattr(mod, "_fetch_bytes", lambda url, timeout: make_zip(
        {"VERSION": "0.2.0\n", "SKILL.md": "new\n", "docs/a.md": "a\n"}))
    return mod, install, calls


def test_versions(cu):
    mod, _, _ = cu
    assert mod._is_newer("0.10.0", "0.9.0")
    assert mod._is_newer("1.0.0", "1.0.0-rc1")
    assert not mod._is_newer("0.2.0", "0.2.0")


def test_outdated_copy_install_is_mirrored(cu):
    mod, install, _ = cu
    (install / "stale.md").write_text("old", encoding="utf-8")
    (install / "bridge.env").write_text("SECRET=1", encoding="utf-8")
    (install / ".aigo").mkdir()
    (install / ".aigo" / "token.json").write_text("{}", encoding="utf-8")

    result = mod.check()
    assert result["status"] == "outdated" and result["breaking"] is False
    assert "新東西" in result["changelog"]

    state = mod._load_state()
    results = mod._sync_all(state, "0.2.0", force=False)
    assert [r["action"] for r in results] == ["synced"]
    assert (install / "VERSION").read_text(encoding="utf-8").strip() == "0.2.0"
    assert (install / "docs" / "a.md").exists()
    assert not (install / "stale.md").exists()          # 遠端沒有的檔案被刪
    assert (install / "bridge.env").exists()            # 金鑰檔保留
    assert (install / ".aigo" / "token.json").exists()  # 憑證目錄保留


def test_remote_is_throttled_for_three_hours(cu):
    mod, _, calls = cu
    mod.check()
    mod.check()
    assert calls["version"] == 1
    mod.check(force=True)
    assert calls["version"] == 2


def test_stale_cache_is_used_when_offline(cu, monkeypatch):
    mod, _, _ = cu
    state = {"remote_cache": {"version": "0.3.0", "fetched_at": time.time() - 10 * 3600}}
    monkeypatch.setattr(mod, "_fetch", lambda url: None)
    assert mod._resolve_remote(state, force=False) == "0.3.0"


def test_newer_local_is_dev_copy(cu):
    mod, install, _ = cu
    (install / "VERSION").write_text("0.9.0\n", encoding="utf-8")
    assert mod.check()["status"] == "dev"
    results = mod._sync_all(mod._load_state(), "0.2.0", force=False)
    assert results[0]["action"] == "dev-skip"
    assert (install / "VERSION").read_text(encoding="utf-8").strip() == "0.9.0"


@pytest.mark.skipif(shutil.which("git") is None, reason="需要 git")
def test_git_feature_branch_is_dev_copy(cu):
    mod, install, _ = cu
    run = lambda *a: subprocess.run(["git", "-C", str(install), *a], check=True, capture_output=True)
    run("init", "-q", "-b", "feat/x")
    assert "feat/x" in mod._dev_checkout_reason(install, "0.1.0", "0.2.0")


def test_failed_sync_is_not_retried_within_window(cu, monkeypatch):
    mod, install, _ = cu
    monkeypatch.setattr(mod, "_fetch_bytes", lambda url, timeout: None)
    mod.check()
    state = mod._load_state()
    assert mod._sync_all(state, "0.2.0", force=False)[0]["action"] == "failed"
    assert mod._sync_all(state, "0.2.0", force=False)[0]["action"] == "throttled"
    assert mod._sync_all(state, "0.2.0", force=True)[0]["action"] == "failed"


def test_archive_without_wrapper_is_rejected(cu):
    mod, _, _ = cu
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("VERSION", "0.2.0")
    assert mod._archive_entries(buf.getvalue()) is None


def test_archive_skips_preserved_paths(cu):
    mod, _, _ = cu
    entries = mod._archive_entries(make_zip({"VERSION": "1", ".env": "x", "a/prod.env": "y", "a/b.py": "z"}))
    assert set(entries) == {"VERSION", "a/b.py"}


def test_breaking_marker(cu, monkeypatch):
    mod, _, _ = cu
    monkeypatch.setattr(mod, "_fetch", lambda url: "0.2.0" if url == mod.REMOTE_VERSION_URL
                        else "## [0.2.0]\n\n**破壞性**:表結構改了\n")
    assert mod.check(force=True)["breaking"] is True


def test_state_file_is_separate_from_builder():
    text = (ROOT / "tools" / "check_update.py").read_text(encoding="utf-8")
    assert "llm_bridge_update_check.json" in text
    assert 'REPO = "AI-GO-APP/aigo-llm-bridge"' in text
