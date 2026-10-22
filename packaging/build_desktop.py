"""僅封裝明列的公開原始檔,不掃描工作目錄或本機設定。"""
import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(target, output):
    if target not in ('macos', 'windows'):
        raise ValueError('unknown target')
    version = (ROOT / 'VERSION').read_text().strip()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    paths = ['VERSION', 'LICENSE', 'desktop/aigo_desktop.py', 'desktop/install_core.py',
             f'desktop_platform/{target}/install.py',
             f'desktop_platform/{target}/README.md']
    paths += ['desktop_platform/macos/Install.command'] if target == 'macos' else [
        'desktop_platform/windows/Install.cmd', 'desktop_platform/windows/service.ps1']
    package = output / f'aigo-llm-bridge-{target}-{version}.zip'
    with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('aigo-llm-bridge/README.txt',
                   f'AI GO LLM Bridge {version} ({target})\n'
                   'Requires Python 3.10+ and your own signed-in Claude Code / Codex CLI.\n'
                   f'See desktop_platform/{target}/README.md for install and uninstall.\n'
                   'Full documentation: https://github.com/AI-GO-APP/aigo-llm-bridge/blob/main/docs/13-desktop.md\n')
        for path in paths:
            z.write(ROOT / path, 'aigo-llm-bridge/' + path)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    manifest = {'target': target, 'version': version, 'commit': commit, 'dirty': dirty,
                'package': package.name, 'size': package.stat().st_size,
                'sha256': hashlib.sha256(package.read_bytes()).hexdigest(),
                'format': 'python-source-installer', 'requires_python': '>=3.10', 'signed': False}
    (output / f'{target}-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(package)
    return package


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--target', choices=['macos', 'windows'], required=True)
    ap.add_argument('--output', default='dist')
    args = ap.parse_args()
    build(args.target, args.output)
