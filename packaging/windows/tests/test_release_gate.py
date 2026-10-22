import importlib.util
from pathlib import Path
import sys
import pytest

spec=importlib.util.spec_from_file_location('windows_release_gate',Path(__file__).resolve().parents[1]/'check_release.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)


def test_windows_package_has_independent_version_gate():
    assert gate.windows_only(['desktop_bridge/windows_updates.py','packaging/windows/entry.py','README.md'])
    assert gate.windows_only(['desktop_bridge/web/style.css','packaging/windows/release-target.json',
                             'docs/qa/assets/windows-overview.png','tools/check_product_docs.py'])
    assert not gate.windows_only(['packaging/windows/entry.py','docs/qa/assets/script.py'])


def test_shared_runtime_or_mac_changes_still_require_core_gate():
    assert not gate.windows_only(['desktop_bridge/service.py','packaging/windows/entry.py'])
    assert not gate.windows_only(['packaging/macos/build.py'])
    assert not gate.windows_only(['README.md','.github/workflows/ci.yml'])
    assert not gate.windows_only(['desktop_bridge/web/app.js'])
    assert gate.windows_only(['desktop_bridge/web/app.js','desktop_bridge/web/platform.js','desktop_bridge/windows_console.py'])


def test_installed_profile_cannot_be_deleted_by_native_update_or_uninstall(tmp_path,monkeypatch):
    from desktop_bridge.windows_release import profile
    root=tmp_path/'app';(root/'current').mkdir(parents=True);(root/'Update.exe').touch()
    monkeypatch.setattr(sys,'frozen',True,raising=False)
    monkeypatch.setattr(sys,'executable',str(root/'current/aigo-bridge.exe'))
    cfg={'local_probe':False,'pack_id':'fixture'}
    with pytest.raises(ValueError):profile(cfg,root/'current/data')
    with pytest.raises(ValueError):profile(cfg,root/'data')
    assert profile(cfg,tmp_path/'persistent')==tmp_path/'persistent'
