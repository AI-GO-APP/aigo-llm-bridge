import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('windows_release_gate',Path(__file__).resolve().parents[1]/'check_release.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)


def test_windows_package_has_independent_version_gate():
    assert gate.windows_only(['desktop_bridge/windows_updates.py','packaging/windows/entry.py','README.md'])


def test_shared_runtime_or_mac_changes_still_require_core_gate():
    assert not gate.windows_only(['desktop_bridge/service.py','packaging/windows/entry.py'])
    assert not gate.windows_only(['packaging/macos/build.py'])
    assert not gate.windows_only(['README.md','.github/workflows/ci.yml'])
