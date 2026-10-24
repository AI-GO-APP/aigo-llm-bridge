"""Build the current BYO Mac source installer from tracked public files only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_ROOTS = ('desktop_bridge/', 'cloudflare/src/', 'skills/byo-cloudflare/', 'docs/')
PUBLIC_FILES = {'VERSION', 'LICENSE', 'AGENTS.md', 'CLAUDE.md', 'README.md', 'README-LEGACY.md',
                'CONTEXT.md', 'CONTRIBUTING.md', 'CHANGELOG.md', 'tools/install.py',
                'tools/byo_setup.py', 'tools/mac_service.py', 'tools/mac_key_handoff.py',
                'tools/benchmark_api_latency.py', 'tools/benchmark_warm_cli.py', 'tools/warm_cli_pool.py'}
REQUIRED = {'tools/install.py', 'desktop_bridge/__main__.py', 'desktop_bridge/macos_instance.py',
            'desktop_bridge/macos_console.py', 'desktop_bridge/requirements-macos.txt',
            'cloudflare/src/worker.js', 'docs/MACOS-SETUP.md', 'docs/AI-AGENT-SETUP.md',
            'tools/benchmark_api_latency.py', 'tools/benchmark_warm_cli.py', 'tools/warm_cli_pool.py'}
PREFIX = 'aigo-llm-bridge/'
INSTALL = '''#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Install Python 3.12+ first, then run this installer again.' >&2
  exit 1
fi
exec python3 tools/install.py "$@"
'''


def build(output, *, allow_dirty=False):
    version = (ROOT / 'VERSION').read_text().strip()
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    if dirty and not allow_dirty:
        raise ValueError('Commit all reviewed changes before building a distributable Mac package.')
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    paths = sorted(p for p in tracked if p in PUBLIC_FILES or p.startswith(PUBLIC_ROOTS))
    paths = [p for p in paths if '/tests/' not in p and '__pycache__' not in p and not p.endswith('.pyc')]
    if not REQUIRED <= set(paths): raise ValueError('Current Mac BYO installer sources are incomplete.')
    output = Path(output).resolve(); output.mkdir(parents=True, exist_ok=True)
    package = output / f'aigo-llm-bridge-macos-source-{version}.zip'
    source = {'schema': 1, 'version': version, 'commit': commit, 'format': 'macos-byo-source'}
    with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED) as archive:
        for relative in paths:
            path = ROOT / relative
            if path.is_symlink() or not path.is_file(): raise ValueError('Only regular tracked source files can be packaged.')
            archive.write(path, PREFIX + relative)
        command = zipfile.ZipInfo(PREFIX + 'Install.command')
        command.create_system = 3; command.external_attr = (stat.S_IFREG | 0o755) << 16
        archive.writestr(command, INSTALL)
        archive.writestr(PREFIX + 'source-release.json', json.dumps(source, indent=2) + '\n')
    with zipfile.ZipFile(package) as archive:
        names = set(archive.namelist())
        assert all(PREFIX + p in names for p in REQUIRED)
        assert PREFIX + 'Install.command' in names
        assert archive.getinfo(PREFIX + 'Install.command').external_attr >> 16 & 0o111
        assert not any('/desktop/' in p or '/.wrangler/' in p or '/.desktop-data/' in p or 'bridge.sqlite' in p for p in names)
    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    manifest = {**source, 'target': 'macos', 'dirty': dirty, 'redistributable': not dirty,
                'package': package.name, 'size': package.stat().st_size, 'sha256': digest,
                'requires_python': '>=3.12', 'architecture': 'universal-source', 'signed': False,
                'entrypoint': 'Install.command'}
    (output / 'macos-source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (output / (package.name + '.sha256')).write_text(digest + '  ' + package.name + '\n')
    (output / 'macos-source-self-test.json').write_text(json.dumps({
        'success': True, 'format': source['format'], 'current_byo_sources': True,
        'installer_executable': True, 'no_legacy_runtime': True, 'commit': commit,
        'redistributable': not dirty}, indent=2) + '\n')
    print(json.dumps({'package': str(package), 'version': version, 'commit': commit, 'dirty': dirty}))
    return package


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=str(ROOT / 'dist/macos-source'))
    parser.add_argument('--allow-dirty', action='store_true', help='Local tests only; not distributable.')
    args = parser.parse_args()
    build(args.output, allow_dirty=args.allow_dirty)
