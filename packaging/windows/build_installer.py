"""Native Windows installer; independent of the legacy ZIP and Mac release."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from desktop_bridge.windows_updates import version, transport
from build_resources import stage_documents


def main(argv=None):
    target = json.loads((ROOT / 'packaging/windows/release-target.json').read_text())
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', default=target['version'])
    parser.add_argument('--public-key', required=True)
    parser.add_argument('--policy-url', required=True)
    parser.add_argument('--vpk', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--local-probe', action='store_true')
    parser.add_argument('--pack-id')
    parser.add_argument('--probe-data-dir')
    args = parser.parse_args(argv)
    if sys.platform != 'win32':
        parser.error('Build this installer on Windows.')
    version(args.version)
    if args.pack_id and (not args.local_probe or not args.pack_id.startswith('AIGO.LLMBridge.Probe.')):
        parser.error('Only local probes may override package identity.')
    if args.probe_data_dir and not args.local_probe:
        parser.error('An embedded profile is only permitted in a non-distributable local probe.')
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    Ed25519PublicKey.from_public_bytes(base64.b64decode(args.public_key, validate=True))
    cfg = {**target, 'version': args.version, 'local_probe': args.local_probe, 'public_key': args.public_key,
           'policy_url': args.policy_url, 'core_version': (ROOT / 'VERSION').read_text().strip(),
           'pack_id': args.pack_id or target['pack_id'], 'authenticode_signed': False,
           'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()}
    cfg['dirty'] = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    if args.probe_data_dir:
        cfg['probe_data_dir'] = str(Path(args.probe_data_dir).resolve())
    cfg['redistributable'] = not cfg['local_probe'] and not cfg['dirty']
    if cfg['dirty'] and not cfg['local_probe']:
        parser.error('Distributable installers require a clean committed tree.')
    transport(args.policy_url, cfg)
    out = Path(args.output).resolve()
    if out == ROOT or out == Path(out.anchor):
        parser.error('Use a dedicated output directory.')
    if out.exists() and any(out.iterdir()) and not (out / '.bridge-windows-build').is_file():
        parser.error('Output directory is not owned by this builder.')
    out.mkdir(parents=True, exist_ok=True)
    (out / '.bridge-windows-build').write_text('Windows installer build', encoding='utf-8')
    stage = out / 'stage'; stage.mkdir(exist_ok=True)
    (stage / 'windows-release.json').write_text(json.dumps(cfg), encoding='utf-8')
    stage_documents(ROOT, stage, cfg['commit'])
    shutil.copytree(ROOT / 'desktop_bridge/web', stage / 'web', dirs_exist_ok=True)
    with (stage / 'web/app.js').open('a', encoding='utf-8') as stream:
        stream.write('\n' + (ROOT / 'packaging/windows/console_extension.js').read_text(encoding='utf-8'))
    env = dict(os.environ, BRIDGE_WINDOWS_STAGE=str(stage))
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--distpath', str(out / 'dist'),
        '--workpath', str(out / 'work'), str(ROOT / 'packaging/windows/bridge.spec')], cwd=ROOT, env=env, check=True)
    app = out / 'dist/AIGO LLM Bridge'
    test = subprocess.check_output([str(app / 'aigo-bridge.exe'), '--self-test'], cwd=out, text=True)
    report = json.loads(test.strip().splitlines()[-1])
    assert report['version'] == cfg['version'] and report['resources'] and report['ca_bundle']
    (out / 'self-test.json').write_text(json.dumps(report), encoding='utf-8')
    vpk = ['dotnet', args.vpk] if args.vpk.endswith('.dll') else [args.vpk]
    subprocess.run(vpk + ['--skip-updates', '--yes', 'pack', '--packId', cfg['pack_id'],
        '--packVersion', cfg['version'], '--packDir', str(app), '--mainExe', 'AIGO-LLM-Bridge.exe',
        '--channel', cfg['framework_channel'], '--runtime', 'win-x64', '--packTitle',
        ('LLM Bridge Probe ' + cfg['pack_id'].split('.')[-1]) if cfg['local_probe'] else 'LLM Bridge Internal',
        '--outputDir', str(out / 'Releases')], cwd=ROOT, check=True)
    files = [{'name': p.name, 'size': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
             for p in sorted((out / 'Releases').iterdir()) if p.is_file()]
    (out / 'artifacts.json').write_text(json.dumps({'config': cfg, 'artifacts': files}, indent=2), encoding='utf-8')
    print(json.dumps({'built': True, 'version': cfg['version'], 'redistributable': cfg['redistributable'], 'output': str(out)}))


if __name__ == '__main__':
    main()
