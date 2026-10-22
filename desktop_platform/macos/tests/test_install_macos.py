import importlib.util
import plistlib
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / 'install.py'
spec = importlib.util.spec_from_file_location('install_macos', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_launch_agent_paths_and_restart_policy(tmp_path):
    home = tmp_path / '含 空白的路徑'
    data = plistlib.loads(plistlib.dumps(m.make_plist(home, '/Python Path/python3')))
    assert data['ProgramArguments'] == ['/Python Path/python3', str(home / 'aigo_desktop.py'), 'serve']
    assert data['EnvironmentVariables']['AIGO_DESKTOP_HOME'] == str(home)
    assert data['KeepAlive'] == {'SuccessfulExit': False}
    assert data['RunAtLoad'] and data['ThrottleInterval'] == 60
