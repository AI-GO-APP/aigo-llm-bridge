"""安裝共用核心;背景服務由各平台自行管理。"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def install_files(root, home, port):
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Windows 不依賴 POSIX mode;限制整個安裝目錄為目前使用者。
    if os.name == 'nt':
        identity = subprocess.run(['whoami', '/user', '/fo', 'csv', '/nh'], capture_output=True,
                                  text=True, check=True).stdout
        import csv
        sid = next(csv.reader([identity.strip()]))[1]
        subprocess.run(['icacls', str(home), '/inheritance:r', '/grant:r', f'*{sid}:(OI)(CI)F'],
                       check=True, capture_output=True)
    for name in ('aigo_desktop.py',):
        source, target = root / 'desktop' / name, home / name
        if source.resolve() != target.resolve():
            temporary = target.with_suffix('.new')
            shutil.copyfile(source, temporary)
            os.replace(temporary, target)
    result = subprocess.run([sys.executable, str(home / 'aigo_desktop.py'), 'setup', '--port', str(port)],
                            env={**os.environ, 'AIGO_DESKTOP_HOME': str(home), 'PYTHONUTF8': '1'}, capture_output=True,
                            text=True, encoding='utf-8', check=True)
    print(result.stdout, end='')
    return json.loads((home / 'desktop.json').read_text(encoding='utf-8'))
