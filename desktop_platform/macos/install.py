#!/usr/bin/env python3
"""macOS 個人端點安裝、更新、服務移除。無須 sudo。"""
import argparse
import os
import platform
import plistlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'desktop'))
from install_core import install_files
from aigo_desktop import home_dir

LABEL = 'com.aigo.llm-bridge-desktop'


def make_plist(home, python):
    return {'Label': LABEL, 'ProgramArguments': [python, str(home / 'aigo_desktop.py'), 'serve'],
            'WorkingDirectory': str(home), 'EnvironmentVariables': {
                'AIGO_DESKTOP_HOME': str(home), 'PYTHONUNBUFFERED': '1',
                'PATH': os.environ.get('PATH', '/usr/bin:/bin')},
            'RunAtLoad': True, 'KeepAlive': {'SuccessfulExit': False}, 'ThrottleInterval': 60,
            'StandardOutPath': str(home / 'service.log'), 'StandardErrorPath': str(home / 'service.log')}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--uninstall', action='store_true', help='停止並移除背景服務;保留金鑰和設定')
    ap.add_argument('--no-start', action='store_true', help='安裝檔案與設定,略過背景服務')
    ap.add_argument('--port', type=int, default=8790)
    args = ap.parse_args()
    if platform.system() != 'Darwin':
        ap.error('這個安裝程式只支援 macOS')
    if not 1024 <= args.port <= 65535:
        ap.error('port 必須介於 1024 與 65535')
    home = home_dir().absolute()
    plist = Path.home() / 'Library/LaunchAgents' / (LABEL + '.plist')
    domain = f'gui/{os.getuid()}'
    if args.uninstall:
        stop_service(domain)
        plist.unlink(missing_ok=True)
        print(f'已移除背景服務。設定保留於 {home}')
        return
    if not args.no_start:
        stop_service(domain)
    install_files(ROOT, home, args.port)
    if args.no_start:
        return
    plist.parent.mkdir(parents=True, exist_ok=True)
    plist.write_bytes(plistlib.dumps(make_plist(home, sys.executable)))
    plist.chmod(0o600)
    subprocess.run(['launchctl', 'bootstrap', domain, str(plist)], check=True)
    print('已啟動。登入後會自動執行。用 credentials 指令查看金鑰。')


def stop_service(domain):
    result = subprocess.run(['launchctl', 'bootout', domain + '/' + LABEL], capture_output=True)
    # 3/113 = 找不到服務;其他錯誤必須回報,避免覆蓋仍在執行的服務。
    if result.returncode not in (0, 3, 113):
        raise SystemExit('無法停止既有服務,請先檢查 launchctl 狀態')


if __name__ == '__main__':
    main()
