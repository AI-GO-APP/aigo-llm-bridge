#!/usr/bin/env python3
"""Windows 個人端點安裝、更新、服務移除。無須系統管理員。"""
import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'desktop'))
from install_core import install_files
from aigo_desktop import home_dir


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--uninstall', action='store_true')
    ap.add_argument('--no-start', action='store_true')
    ap.add_argument('--port', type=int, default=8790)
    args = ap.parse_args()
    if platform.system() != 'Windows':
        ap.error('這個安裝程式只支援 Windows')
    if not 1024 <= args.port <= 65535:
        ap.error('port 必須介於 1024 與 65535')
    home = home_dir().absolute()
    script = Path(__file__).with_name('service.ps1')
    base = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script),
            '-Python', sys.executable, '-InstallDir', str(home)]
    if args.uninstall:
        subprocess.run(base + ['-Uninstall'], check=True)
        print(f'已移除背景服務。設定保留於 {home}')
        return
    if not args.no_start:
        subprocess.run(base + ['-Uninstall'], check=True)
    install_files(ROOT, home, args.port)
    if not args.no_start:
        subprocess.run(base, check=True)


if __name__ == '__main__':
    main()
