import importlib.util
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / 'install.py'
spec = importlib.util.spec_from_file_location('install_windows', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_installer_invokes_platform_service_without_shell(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(m.platform, 'system', lambda: 'Windows')
    monkeypatch.setattr(m, 'home_dir', lambda: tmp_path / '含 空白')
    monkeypatch.setattr(m, 'install_files', lambda *_: {})
    monkeypatch.setattr(m.subprocess, 'run', lambda cmd, **kw: calls.append((cmd, kw)))
    monkeypatch.setattr(m.sys, 'argv', ['install.py'])
    m.main()
    assert len(calls) == 2 and calls[0][0][-1] == '-Uninstall'
    assert calls[1][0][-1] == str(tmp_path / '含 空白')
    assert all(not kw.get('shell') for _, kw in calls)
