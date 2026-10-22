"""Create a public policy from verified build artifacts. Signing key is stdin only."""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from desktop_bridge.windows_updates import canonical, verify, version, transport


def sign(build, release_url, sequence, minimum_version, key):
    root = Path(build)
    report = json.loads((root / 'artifacts.json').read_text())
    cfg = report['config']
    transport(release_url, cfg)
    for item in report['artifacts']:
        if Path(item['name']).name != item['name']:
            raise ValueError('Invalid artifact path.')
        path = root / 'Releases' / item['name']
        if path.is_symlink() or path.stat().st_size != item['size'] or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Build artifact changed.')
    feed = root / 'Releases' / ('releases.' + cfg['framework_channel'] + '.json')
    assets = json.loads(feed.read_bytes())['Assets']
    if len(assets) != 1:
        raise ValueError('Release must contain exactly one full package.')
    asset = assets[0]
    if asset['Type'] != 'Full' or asset['Version'] != cfg['version'] or asset['PackageId'] != cfg['pack_id']:
        raise ValueError('Feed target mismatch.')
    package = root / 'Releases' / asset['FileName']
    if Path(asset['FileName']).name != asset['FileName'] or not any(a['name'] == package.name for a in report['artifacts']):
        raise ValueError('Package is not part of this build.')
    if not cfg['local_probe'] and not cfg['redistributable']:
        raise ValueError('Cannot announce a non-distributable build.')
    payload = {k: cfg[k] for k in ('platform', 'arch', 'channel', 'pack_id', 'version', 'commit')}
    payload.update(schema=1, minimum_version=minimum_version, sequence=sequence,
        expires_at=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat(), release_url=release_url,
        feed_sha256=hashlib.sha256(feed.read_bytes()).hexdigest(), package_sha256=hashlib.sha256(package.read_bytes()).hexdigest())
    result = {'payload': payload, 'signature': base64.b64encode(key.sign(canonical(payload))).decode()}
    verify(result, cfg)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--build', required=True); p.add_argument('--release-url', required=True)
    p.add_argument('--sequence', required=True, type=int); p.add_argument('--minimum-version', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(sys.stdin.read().strip(), validate=True))
    result = sign(args.build, args.release_url, args.sequence, args.minimum_version, key)
    Path(args.output).write_text(json.dumps(result, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
