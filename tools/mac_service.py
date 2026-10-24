"""Manage only this source installation's macOS LaunchAgent. No provider login changes."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import time


def manifest_at(root):
    root = Path(root).expanduser().resolve()
    value = json.loads((root / 'source-install.json').read_text(encoding='utf-8'))
    if Path(value['install_root']).resolve() != root:
        raise ValueError('Installation root mismatch.')
    return value


def setup(manifest, action, timeout=180):
    command = [manifest['python'], str(Path(manifest['app']) / 'tools/byo_setup.py'), action,
               '--data-dir', manifest['data_dir']]
    if action == 'wait-idle': command += ['--timeout', str(timeout)]
    result = subprocess.run(command, capture_output=True, timeout=timeout + 10)
    if result.returncode: raise ValueError('Bridge must drain before stopping; inspect setup status.')
    return result.stdout.decode()


def control(action, root, timeout=180, workers=None, accepting=True, pending=None, resident=None):
    if sys.platform != 'darwin': raise ValueError('This command requires macOS.')
    m = manifest_at(root)
    sys.path.insert(0, m['app'])
    from desktop_bridge.capacity import STANDARD_CONCURRENCY
    if action == 'workers':
        from desktop_bridge.service import Runtime
        from desktop_bridge.store import Store
        # Validate both values before pause/bootout; preserve omitted pending.
        store=Store(m['data_dir'],startup=False)
        try:
            accepting=store.get('accepting')
            effective_pending=store.get('inference_pending') if pending is None else pending
            # Older profiles may have no pending row; increasing workers retains
            # the old command's behavior without shrinking an explicit queue.
            if pending is None:effective_pending=max(workers,effective_pending) if type(workers) is int else effective_pending
            Runtime.validate_capacity(workers,effective_pending)
            effective_resident=store.get('inference_resident') if resident is None else resident
            Runtime.validate_resident(effective_resident,workers)
        finally:store.close()
    from desktop_bridge.windows import mac_startup_path, set_startup
    data = m['data_dir']; agent = mac_startup_path(data)
    domain = f'gui/{os.getuid()}'; label = agent.stem; target = domain + '/' + label
    def launch(*args):
        return subprocess.run(['/bin/launchctl', *args], capture_output=True, timeout=30)
    def loaded(): return launch('print', target).returncode == 0
    if action in ('stop', 'restart', 'disable', 'rollback', 'workers'):
        setup(m, 'pause'); setup(m, 'wait-idle', timeout)
        if loaded() and launch('bootout', target).returncode:
            raise ValueError('LaunchAgent did not stop.')
        # The profile lock proves that a manual instance has also exited.
        import fcntl
        with open(Path(data) / 'instance.lock', 'a+b') as lock:
            deadline = time.monotonic() + 15
            while True:
                try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB); break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise ValueError('A manually started Bridge still owns this profile; stop it before updating.')
                    time.sleep(.2)
    if action == 'workers':
        from desktop_bridge.store import Store
        store=Store(data,startup=False)
        try:
            with store.lock,store.db:
                store.db.executemany('insert or replace into settings values (?,?)',
                    [('inference_workers',json.dumps(workers)),('inference_pending',json.dumps(effective_pending)),('inference_resident',json.dumps(effective_resident))])
        finally: store.close()
    if action == 'disable': set_startup(False, data)
    if action == 'rollback':
        root=Path(root).expanduser().resolve()
        old=json.loads((root/'source-install.previous.json').read_text(encoding='utf-8'))
        if Path(old['data_dir']).resolve()!=Path(data).resolve() or not Path(old['app']).is_dir() or not Path(old['app']).resolve().is_relative_to(root/'versions'):
            raise ValueError('Rollback must preserve this profile and use an installed release.')
        pending=root/'source-install.rollback.tmp'
        pending.write_text(json.dumps(old,indent=2),encoding='utf-8');os.replace(pending,root/'source-install.json')
        (root/'source-install.previous.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
        m=old
    if action in ('start', 'restart', 'enable', 'rollback', 'workers'):
        # Runs from the installed source, so set_startup discovers its stable Bridge.pyw.
        set_startup(True, data)
        if action != 'enable':
            setup(m, 'resume' if accepting else 'pause')
            if not loaded() and launch('bootstrap', domain, str(agent)).returncode:
                raise ValueError('LaunchAgent bootstrap failed; use the logged-in macOS GUI session.')
            if launch('kickstart', target).returncode: raise ValueError('LaunchAgent did not start.')
    result = {'manifest': str(Path(root).expanduser().resolve() / 'source-install.json'),
              'data_dir': data, 'launch_agent': str(agent), 'loaded': loaded(),
              'enabled_at_login': agent.exists(), 'status': json.loads(setup(m, 'status'))}
    return result


def update(root, source, timeout=180):
    """Apply an explicitly selected local source; restore the prior manifest on failure."""
    import fcntl
    root = Path(root).expanduser().resolve()
    source = Path(source).expanduser().resolve()
    installer = source / 'tools/install.py'
    if not installer.is_file() or not (source / 'desktop_bridge/__init__.py').is_file():
        raise ValueError('Select a Bridge source checkout.')
    original = manifest_at(root)
    import sqlite3
    database = Path(original['data_dir']) / 'bridge.sqlite'
    accepting = True
    if database.exists():
        with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as db:
            row = db.execute("select value from settings where name='accepting'").fetchone()
            if row: accepting = json.loads(row[0])
    sys.path.insert(0, original['app'])
    from desktop_bridge.windows_release import atomic_json
    def record(value):
        atomic_json(root / 'macos-update.json', {**value, 'checked_at': time.time()})
    with open(root / 'macos-update.lock', 'a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Drain failure does not permit installation or manifest replacement.
        control('stop', root, timeout)
        record({'status': 'updating', 'previous_version': original['version']})
        try:
            result = subprocess.run([original['python'], str(installer), '--install-root', str(root)],
                                    capture_output=True, timeout=300)
            if result.returncode:
                raise ValueError('Source installation did not complete.')
            current = manifest_at(root)
            if Path(current['data_dir']).resolve() != Path(original['data_dir']).resolve():
                raise ValueError('Update changed the profile.')
            state = control('start', root, timeout, accepting=accepting)
            # Launchctl loaded alone does not establish HTTP readiness.
            import urllib.request
            import urllib.error
            until = time.monotonic() + 30
            while True:
                from desktop_bridge.store import Store
                store = Store(current['data_dir'], startup=False)
                try: port = store.get('port')
                finally: store.close()
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=2) as response:
                        healthy = json.loads(response.read())
                    if healthy.get('ok') and healthy.get('version') == current['version']:
                        break
                except (OSError, ValueError): pass
                if time.monotonic() >= until:
                    raise ValueError('Updated Bridge did not become healthy.')
                time.sleep(.2)
            value = {'updated': True, 'previous_version': original['version'], 'version': current['version'],
                     'profile_preserved': True, 'loaded': state['loaded']}
            record({'status': 'completed', **value})
            return value
        except Exception:
            # Stop a failed new process before returning to the saved launcher manifest.
            try: control('stop', root, timeout)
            except Exception:
                record({'status': 'failed', 'recovered': False, 'previous_version': original['version']})
                raise
            temporary = root / 'source-install.recovery.tmp'
            temporary.write_text(json.dumps(original), encoding='utf-8')
            os.replace(temporary, root / 'source-install.json')
            try:
                control('start', root, timeout, accepting=accepting)
                record({'status': 'failed', 'recovered': True, 'previous_version': original['version']})
            except Exception:
                record({'status': 'failed', 'recovered': False, 'previous_version': original['version']})
                raise
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status','enable','disable','start','stop','restart','rollback','workers','update','onboarding-open','onboarding-status'])
    parser.add_argument('--source', help='Explicit local Bridge source checkout for update.')
    parser.add_argument('--count',type=int,help='Parallel isolated inference processes (workers action, 1–64; default profile is 64).')
    parser.add_argument('--resident',type=int,help='Initialize-only Codex residents (0–count); zero disables prewarm.')
    parser.add_argument('--pending',type=int,help='Total admitted running plus queued requests (workers action, count–64).')
    parser.add_argument('--install-root', default=str(Path.home() / 'Library/Application Support/AIGO LLM Bridge'))
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    try:
        if (args.pending is not None or args.resident is not None) and args.action!='workers':raise ValueError('--pending/--resident require workers.')
        if args.action == 'update':
            if not args.source: raise ValueError('update requires --source.')
            value = update(args.install_root, args.source, args.timeout)
        elif args.action.startswith('onboarding-'):
            m = manifest_at(args.install_root)
            if args.action == 'onboarding-open':
                (Path(m['data_dir']) / 'macos-onboarding-open.request').touch(mode=0o600)
                value = {'open_requested': True}
            else:
                path = Path(m['data_dir']) / 'macos-onboarding.json'
                value = json.loads(path.read_text()) if path.exists() else {'completed_at': None}
        else:
            value = control(args.action, args.install_root, args.timeout, args.count,pending=args.pending,resident=args.resident)
        print(json.dumps(value, ensure_ascii=False)); return 0
    except (OSError, ValueError, subprocess.SubprocessError):
        print('Mac service operation incomplete. Check this installation and drain/stop only its Bridge.', file=sys.stderr)
        return 1


if __name__ == '__main__': raise SystemExit(main())
