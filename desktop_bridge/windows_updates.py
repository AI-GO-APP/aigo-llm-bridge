"""Signed target-bound policy; Velopack owns native installation, not our data."""
import base64
from contextlib import contextmanager, closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time
import urllib.request
from urllib.parse import urlsplit

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from .windows_release import atomic_json


class UpdateError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', value):
        raise UpdateError('Invalid release version.')
    return tuple(map(int, value.split('.')))


def transport(url, cfg):
    parsed = urlsplit(url)
    local = cfg['local_probe'] and parsed.scheme == 'http' and parsed.hostname == '127.0.0.1'
    if (parsed.scheme != 'https' and not local) or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise UpdateError('Invalid update transport.')


def fetch(url, cfg, limit):
    transport(url, cfg)
    class SafeRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            transport(newurl, cfg)
            source, dest = urlsplit(url), urlsplit(newurl)
            if dest.hostname != source.hostname and not (source.hostname == 'github.com' and dest.hostname == 'release-assets.githubusercontent.com'):
                raise UpdateError('Update metadata redirect host is not permitted.')
            return super().redirect_request(req, fp, code, msg, headers, newurl)
    import ssl
    import certifi
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), SafeRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
    try:
        with opener.open(urllib.request.Request(url, headers={'Cache-Control': 'no-cache'}), timeout=15) as response:
            raw = response.read(limit + 1)
        if len(raw) > limit:
            raise UpdateError('Update metadata is too large.')
        return raw
    except UpdateError:
        raise
    except Exception:
        raise UpdateError('Update source unavailable; the installed service was not stopped.') from None


FIELDS = {'schema', 'platform', 'arch', 'channel', 'pack_id', 'version', 'minimum_version',
          'sequence', 'expires_at', 'release_url', 'feed_sha256', 'package_sha256', 'commit'}


def verify(envelope, cfg, now=None):
    try:
        payload = envelope['payload']
        Ed25519PublicKey.from_public_bytes(base64.b64decode(cfg['public_key'], validate=True)).verify(
            base64.b64decode(envelope['signature'], validate=True), canonical(payload))
        if set(payload) != FIELDS or type(payload['schema']) is not int or payload['schema'] != 1:
            raise ValueError()
        if any(payload[k] != cfg[k] for k in ('platform', 'arch', 'channel', 'pack_id')):
            raise ValueError()
        if payload['platform'] != 'windows' or payload['arch'] != 'x64':
            raise ValueError()
        if type(payload['sequence']) is not int or not 0 < payload['sequence'] <= 9007199254740991:
            raise ValueError()
        if version(payload['minimum_version']) > version(payload['version']):
            raise ValueError()
        current = now or datetime.now(timezone.utc)
        expires = datetime.fromisoformat(payload['expires_at'].replace('Z', '+00:00'))
        if not 0 < (expires - current).total_seconds() <= 90 * 86400:
            raise ValueError()
        for key in ('feed_sha256', 'package_sha256'):
            if not re.fullmatch('[0-9a-f]{64}', payload[key]):
                raise ValueError()
        if not re.fullmatch('[0-9a-f]{40}', payload['commit']):
            raise ValueError()
        transport(payload['release_url'], cfg)
        return payload
    except Exception:
        raise UpdateError('Update signature, target, validity or version is invalid.') from None


def check(cfg, directory):
    if os.name == 'nt':
        with lock(directory, name='policy'):
            return _check(cfg, directory)
    return _check(cfg, directory)


def _check(cfg, directory):
    envelope = json.loads(fetch(cfg['policy_url'], cfg, 65536))
    payload = verify(envelope, cfg)
    state_path = Path(directory) / 'updates' / (cfg['pack_id'] + '-policy.json')
    state = json.loads(state_path.read_text()) if state_path.is_file() else {}
    previous = state.get('payload')
    if previous:
        if (payload['sequence'] < previous['sequence'] or version(payload['version']) < version(previous['version'])
                or version(payload['minimum_version']) < version(previous['minimum_version'])):
            raise UpdateError('Rejected an older release policy.')
        if payload['sequence'] == previous['sequence'] and payload != previous:
            raise UpdateError('A release sequence cannot be changed.')
        if payload['version'] == previous['version'] and any(payload[k] != previous[k] for k in ('feed_sha256', 'package_sha256', 'commit')):
            raise UpdateError('A published version cannot be replaced.')
    if version(cfg['version']) > version(payload['version']):
        raise UpdateError('The installed release is newer than this channel; no downgrade was applied.')
    atomic_json(state_path, envelope)
    return {'installed': cfg['version'], 'latest': payload['version'],
            'available': version(cfg['version']) < version(payload['version']),
            'required': version(cfg['version']) < version(payload['minimum_version']), 'policy': payload}


@contextmanager
def lock(directory, name='apply'):
    import msvcrt
    path = Path(directory) / 'updates' / (name + '.lock')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        if not handle.tell():
            handle.write(b'0'); handle.flush()
        handle.seek(0)
        until = time.monotonic() + (20 if name == 'policy' else 0)
        while True:
            try:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.monotonic() >= until:
                    raise UpdateError('Another update is running.') from None
                time.sleep(.1)
        try:
            yield
        finally:
            handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def control(directory, action, data=None, pack_id=None):
    from .secret import protect
    path = Path(directory) / 'windows-control.dpapi'
    if not path.is_file():
        return None
    try:
        metadata = json.loads(protect(path.read_bytes(), decrypt=True))
        if pack_id and metadata['pack_id'] != pack_id:
            raise ValueError()
        url = metadata['origin']
        parsed = urlsplit(url)
        if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.path:
            raise ValueError()
        request = urllib.request.Request(url + '/manage/windows-update/' + action,
            data=json.dumps(data or {}).encode(), headers={'Authorization': 'Bearer ' + metadata['token'],
                'Content-Type': 'application/json'}, method='POST')
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=5) as response:
            return json.load(response)
    except Exception:
        raise UpdateError('Cannot contact this profile; no process was terminated.') from None


def backup(directory, target):
    directory = Path(directory)
    root = directory / 'updates' / ('before-' + target)
    root.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(directory / 'bridge.sqlite')) as source, closing(sqlite3.connect(root / 'bridge.sqlite')) as dest:
        source.backup(dest)
    for name in ('relay-device.dpapi', 'relay-device.pending.dpapi', 'windows-onboarding.json', 'windows-power.json'):
        source = directory / name
        if source.is_file():
            (root / name).write_bytes(source.read_bytes())
    return root


def schema_digest(directory):
    with closing(sqlite3.connect(Path(directory) / 'bridge.sqlite')) as db:
        rows = db.execute("select type,name,sql from sqlite_master where sql is not null order by type,name").fetchall()
    return hashlib.sha256(canonical(rows)).hexdigest()


def recover(cfg, directory):
    """Only resume the original binary when its DB schema has not changed."""
    from .windows import Instance
    from .store import Store
    directory = Path(directory)
    with lock(directory):
        instance = Instance(directory); primary = instance.primary; instance.close()
        if not primary:
            raise UpdateError('Stop this profile normally before recovery.')
        path = directory / 'updates' / 'pending.json'
        if not path.is_file():
            return {'recovered': False, 'reason': 'no_pending_update'}
        pending = json.loads(path.read_text())
        if (pending['pack_id'] != cfg['pack_id'] or pending['from_version'] != cfg['version']
                or pending.get('schema_sha256') != schema_digest(directory)):
            raise UpdateError('Cannot safely resume an old binary; retain data and install a higher repair release.')
        store = Store(directory, startup=False)
        try:
            store.set('accepting', pending['previous_accepting'])
        finally:
            store.close()
        atomic_json(directory / 'updates' / 'last-recovery.json', {**pending, 'recovered_version': cfg['version']})
        path.unlink()
        return {'recovered': True, 'version': cfg['version']}


def apply(cfg, directory, timeout=180):
    import sys
    import velopack
    directory = Path(directory).resolve()
    with lock(directory):
        checked = check(cfg, directory)
        if not checked['available']:
            return checked
        policy = checked['policy']
        base = policy['release_url'].rstrip('/')
        feed_bytes = fetch(base + '/releases.' + cfg['framework_channel'] + '.json', cfg, 2_000_000)
        if hashlib.sha256(feed_bytes).hexdigest() != policy['feed_sha256']:
            raise UpdateError('Release feed hash mismatch.')
        assets = json.loads(feed_bytes)['Assets']
        if len(assets) != 1:
            raise UpdateError('Expected exactly one full update package.')
        asset = assets[0]
        name = asset['FileName']
        if (asset['Type'] != 'Full' or asset['Version'] != policy['version'] or asset['PackageId'] != cfg['pack_id']
                or not re.fullmatch('[a-zA-Z0-9_.-]+', name)):
            raise UpdateError('Release feed target mismatch.')
        # A github.com string selects GithubSource, not this immutable static feed.
        manager = velopack.UpdateManager(velopack.HttpSource(base), velopack.UpdateOptions(False, 0, cfg['framework_channel']))
        info = manager.check_for_updates()
        if (not info or info.TargetFullRelease.Version != policy['version'] or info.TargetFullRelease.FileName != name
                or info.TargetFullRelease.PackageId != cfg['pack_id'] or info.TargetFullRelease.Size != asset['Size']
                or info.TargetFullRelease.SHA1 != asset['SHA1']):
            raise UpdateError('Native updater disagrees with authenticated feed.')
        manager.download_updates(info)
        package = Path(sys.executable).resolve().parent.parent / 'packages' / name
        if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != policy['package_sha256']:
            raise UpdateError('Downloaded package hash mismatch.')
        from .store import Store
        store = Store(directory, startup=False)
        original = store.get('accepting'); store.close()
        floor_path = directory / 'updates' / 'minimum-block.json'
        floor = json.loads(floor_path.read_text()) if floor_path.is_file() else None
        if floor and floor['pack_id'] != cfg['pack_id']:
            raise UpdateError('Minimum-version state belongs to another package.')
        if floor:
            original = floor['previous_accepting']
        drained = False
        try:
            until = time.monotonic() + max(1, timeout)
            while True:
                result = control(directory, 'drain', pack_id=cfg['pack_id'])
                if result is None:
                    from .windows import Instance
                    instance = Instance(directory)
                    primary = instance.primary; instance.close()
                    if not primary:
                        raise UpdateError('Running legacy/headless instance must be stopped by its owner first.')
                    break
                if not floor:
                    original = result['previous_accepting']
                drained = True
                if result['active_requests'] == 0:
                    # Allow completed HTTP responses to reach callers before releasing RAM receipts.
                    time.sleep(2)
                    break
                if time.monotonic() >= until:
                    raise UpdateError('Requests are still active; update deferred.')
                time.sleep(.25)
            # Backups contain metadata and protected transport credentials, never request bodies.
            backup(directory, policy['version'])
            atomic_json(directory / 'updates' / 'pending.json', {'target': policy['version'],
                'commit': policy['commit'], 'pack_id': cfg['pack_id'], 'previous_accepting': original,
                'from_version': cfg['version'], 'schema_sha256': schema_digest(directory)})
            if drained:
                control(directory, 'shutdown', pack_id=cfg['pack_id'])
                from .windows import Instance
                until = time.monotonic() + 20
                while True:
                    instance = Instance(directory); primary = instance.primary; instance.close()
                    console = Instance(directory / 'console'); console_closed=console.primary; console.close()
                    if primary and console_closed:
                        break
                    if time.monotonic() >= until:
                        raise UpdateError('Service did not shut down; no process was killed.')
                    time.sleep(.2)
                from .windows_console import wait_for_exit
                wait_for_exit(directory)
            manager.apply_updates_and_restart_with_args(info, ['--data-dir', str(directory), '--background'])
            return {'applying': True, 'target': policy['version']}
        except Exception:
            if drained:
                try:
                    control(directory, 'resume', pack_id=cfg['pack_id'])
                except UpdateError:
                    pass
            raise


def finish(cfg, store):
    path = store.directory / 'updates' / 'pending.json'
    if not path.is_file():
        return
    pending = json.loads(path.read_text())
    if pending['pack_id'] != cfg['pack_id'] or pending['target'] != cfg['version'] or pending['commit'] != cfg['commit']:
        raise UpdateError('Incomplete update; use the recovery CLI. Data was preserved.')
    store.set('accepting', pending['previous_accepting'])
    atomic_json(store.directory / 'updates' / 'last-result.json', {**pending, 'installed_verified': True})
    (store.directory / 'updates' / 'minimum-block.json').unlink(missing_ok=True)
    path.unlink()
