"""Keep Windows package version gates independent of the core/Mac version."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]


def windows_only(paths):
    # Browser-neutral platform seam; only eligible alongside a Windows package change.
    frontend={'desktop_bridge/web/platform.js','desktop_bridge/web/app.js','desktop_bridge/web/style.css',
              'desktop_bridge/web/index.html','desktop_bridge/management.py'}
    code=[p for p in paths if not p.endswith('.md') and not p.startswith(('.github/','tools/tests/','desktop_bridge/tests/'))
          and not (p.startswith('docs/qa/assets/') and Path(p).suffix.lower() in {'.png','.jpg','.webp'})
          and p != 'tools/lint_terms.py']
    native=any(p.startswith(('desktop_bridge/windows_','packaging/windows/')) for p in code)
    return bool(code) and native and all(p.startswith(('desktop_bridge/windows_','packaging/windows/')) or p in frontend or
        p in {'tools/verify_installer_update.py','tools/verify_windows_onboarding.py','tools/verify_windows_locked.py','tools/publish_windows_installer.py','tools/check_product_docs.py','tools/build_byo.ps1'} for p in code)


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
