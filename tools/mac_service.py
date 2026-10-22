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


def control(action, root, timeout=180):
    if sys.platform != 'darwin': raise ValueError('This command requires macOS.')
    m = manifest_at(root)
    sys.path.insert(0, m['app'])
    from desktop_bridge.windows import mac_startup_path, set_startup
    data = m['data_dir']; agent = mac_startup_path(data)
    domain = f'gui/{os.getuid()}'; label = agent.stem; target = domain + '/' + label
    def launch(*args):
        return subprocess.run(['/bin/launchctl', *args], capture_output=True, timeout=30)
    def loaded(): return launch('print', target).returncode == 0
    if action in ('stop', 'restart', 'disable', 'rollback'):
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
    if action in ('start', 'restart', 'enable', 'rollback'):
        # Runs from the installed source, so set_startup discovers its stable Bridge.pyw.
        set_startup(True, data)
        if action != 'enable':
            setup(m, 'resume')
            if not loaded() and launch('bootstrap', domain, str(agent)).returncode:
                raise ValueError('LaunchAgent bootstrap failed; use the logged-in macOS GUI session.')
            if launch('kickstart', target).returncode: raise ValueError('LaunchAgent did not start.')
    result = {'manifest': str(Path(root).expanduser().resolve() / 'source-install.json'),
              'data_dir': data, 'launch_agent': str(agent), 'loaded': loaded(),
              'enabled_at_login': agent.exists(), 'status': json.loads(setup(m, 'status'))}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status','enable','disable','start','stop','restart','rollback'])
    parser.add_argument('--install-root', default=str(Path.home() / 'Library/Application Support/AIGO LLM Bridge'))
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    try: print(json.dumps(control(args.action, args.install_root, args.timeout), ensure_ascii=False)); return 0
    except (OSError, ValueError, subprocess.SubprocessError):
        print('Mac service operation incomplete. Check this installation and drain/stop only its Bridge.', file=sys.stderr)
        return 1


if __name__ == '__main__': raise SystemExit(main())
