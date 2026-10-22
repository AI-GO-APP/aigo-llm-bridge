"""Install a source checkout on Windows/macOS without admin access or CLI login changes."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import venv

SOURCE = Path(__file__).resolve().parent.parent


def install(root, data_dir=None, *, dependencies=True):
    if sys.version_info < (3,12):raise ValueError('Python 3.12+ is required.')
    root=Path(root).absolute();manifest=root/'source-install.json'
    previous=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else None
    data=Path(data_dir or (previous['data_dir'] if previous else root/'data')).absolute()
    if previous and data.resolve()!=Path(previous['data_dir']).resolve():
        raise ValueError('An update must preserve data_dir. Use a new install root for another device.')
    if os.name=='nt' and any(c in str(root)+str(data) for c in '\r\n"%!'):
        raise ValueError('Windows install/data paths cannot contain quotes, percent, exclamation or newlines.')
    if (root/'install.json').exists():raise ValueError('This directory belongs to the native Windows installer; choose a separate source install root.')
    root.mkdir(parents=True,exist_ok=True)
    env=root/'runtime'
    if not env.exists():venv.EnvBuilder(with_pip=True).create(env)
    python=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if dependencies:
        result=subprocess.run([str(python),'-m','pip','install','--disable-pip-version-check','-r',str(SOURCE/'desktop_bridge/requirements.txt')],capture_output=True)
        if result.returncode:raise ValueError('Dependency installation failed. Check Python/network and retry; no provider login was changed.')
    version={}
    exec((SOURCE/'desktop_bridge/__init__.py').read_text(encoding='utf-8'),version)
    release=root/'versions'/(version['__version__']+'-'+uuid.uuid4().hex[:12])
    release.mkdir(parents=True)
    for folder in ('desktop_bridge','cloudflare/src','skills/byo-cloudflare'):
        source=SOURCE/folder
        if any(p.is_symlink() for p in source.rglob('*')):raise ValueError('Refusing symbolic links in distributable sources.')
        shutil.copytree(source,release/folder,ignore=shutil.ignore_patterns('__pycache__','tests','*.pyc'))
    (release/'docs').mkdir()
    for name in ('BYO-QUICKSTART.md','DEVICE-IDENTITY.md','AI-AGENT-SETUP.md','OPENROUTER-PRICING.md','THIRD-PARTY-INTEGRATION.md','CROSS-PLATFORM-INSTALL.md'):
        shutil.copyfile(SOURCE/'docs'/name,release/'docs'/name)
    for name in ('AGENTS.md','CLAUDE.md'):shutil.copyfile(SOURCE/name,release/name)
    (release/'tools').mkdir();shutil.copyfile(SOURCE/'tools/byo_setup.py',release/'tools/byo_setup.py')
    launcher=root/'Bridge.pyw'
    launcher.write_text("import json, pathlib, runpy, sys\np=pathlib.Path(__file__).parent\nm=json.loads((p/'source-install.json').read_text(encoding='utf-8'))\nsys.path.insert(0,m['app'])\nsys.argv=[sys.argv[0],'--data-dir',m['data_dir'],*sys.argv[1:]]\nrunpy.run_module('desktop_bridge',run_name='__main__')\n",encoding='utf-8')
    data.mkdir(parents=True,exist_ok=True)
    if os.name!='nt':root.chmod(0o700);data.chmod(0o700)
    value={'version':version['__version__'],'python':str(python),'app':str(release),'data_dir':str(data),'launcher':str(launcher),'install_root':str(root)}
    temporary=manifest.with_suffix('.tmp');temporary.write_text(json.dumps(value,indent=2),encoding='utf-8');os.replace(temporary,manifest)
    if os.name=='nt':
        # ASCII script with runtime-expanded paths also works under CP950/CP1252
        # when the Windows user/install directory contains non-ASCII characters.
        (root/'Bridge.cmd').write_text('@echo off\r\n"%~dp0runtime\\Scripts\\python.exe" "%~dp0Bridge.pyw" %*\r\n',encoding='ascii')
    else:
        import shlex
        command=root/'Bridge.command'
        command.write_text('#!/bin/sh\nexec '+shlex.join([str(python),str(launcher)])+' "$@"\n',encoding='utf-8');command.chmod(0o700)
    return value


def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    default=(Path.home()/'Library/Application Support/AIGO LLM Bridge' if sys.platform=='darwin'
             else Path(os.environ.get('LOCALAPPDATA',Path.home()))/'AIGO LLM Bridge Source')
    parser.add_argument('--install-root',default=str(default));parser.add_argument('--data-dir')
    args=parser.parse_args()
    if os.name!='nt' and sys.platform!='darwin':parser.error('Supported installation targets are Windows and macOS.')
    try:print(json.dumps(install(args.install_root,args.data_dir),ensure_ascii=False))
    except (ValueError,OSError):
        print('Installation incomplete; check Python 3.12+, network, write access and original data_dir. No CLI login was modified.',file=sys.stderr);return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
