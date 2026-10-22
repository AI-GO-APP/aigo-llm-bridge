"""Keep Windows package version gates independent of the core/Mac version."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]


def windows_only(paths):
    code=[p for p in paths if not p.endswith('.md') and not p.startswith('.github/')]
    return bool(code) and all(p.startswith(('desktop_bridge/windows_','packaging/windows/')) or
        p in {'tools/verify_installer_update.py','tools/publish_windows_installer.py'} for p in code)


def version(value):
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)',value):
        raise ValueError('Invalid Windows package version.')
    return tuple(map(int,value.split('.')))


def main():
    p=argparse.ArgumentParser();p.add_argument('--base-sha',required=True);args=p.parse_args()
    paths=subprocess.check_output(['git','diff','--name-only',args.base_sha+'...HEAD'],cwd=ROOT,text=True).splitlines()
    if not windows_only(paths):return
    previous=subprocess.run(['git','show',args.base_sha+':packaging/windows/release-target.json'],cwd=ROOT,capture_output=True,text=True)
    before=json.loads(previous.stdout)['version'] if previous.returncode==0 else '0.0.0'
    after=json.loads((ROOT/'packaging/windows/release-target.json').read_text())['version']
    if version(after)<=version(before):raise ValueError('Advance Windows release-target.json version for Windows package changes.')
    if os.environ.get('GITHUB_ENV'):
        with open(os.environ['GITHUB_ENV'],'a',encoding='utf-8') as stream:stream.write('BRIDGE_WINDOWS_ONLY=1\n')
    print('Windows-only package version gate passed; core/Mac version is unchanged.')


if __name__=='__main__':main()
