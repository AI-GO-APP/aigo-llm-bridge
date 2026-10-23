"""Power-policy acceptance on a disposable hosted Windows runner ONLY.

Developer PCs use fake-adapter tests and read-only inspection. No owner workstation
may opt into the mutating part with a command flag.
"""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desktop_bridge.windows_power import NativePower, PowerPolicy, SETTINGS, USER_VALUES
from desktop_bridge.windows_release import atomic_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if (sys.platform != 'win32' or os.environ.get('GITHUB_ACTIONS') != 'true'
            or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted'):
        parser.error('Mutating power acceptance is restricted to a disposable GitHub-hosted Windows runner.')
    output = Path(args.output).resolve()
    if output.exists():
        parser.error('Use a new isolated receipt directory.')
    output.mkdir(parents=True)
    native = NativePower()
    policy = PowerPolicy(output, native)
    original = native.scheme()
    registry = [native.registry(p, n) for p, n, _ in USER_VALUES]
    values = {}
    for name, sub, setting in SETTINGS:
        try:
            values[name] = (native.read(original, sub, setting), native.read(original, sub, setting, dc=True))
        except OSError as error:
            if error.errno not in {2, 50, 87}:
                raise
    checks, success = {}, False
    try:
        checks['no_managed_lock_policy'] = not policy.blockers()
        if not checks['no_managed_lock_policy']:
            raise ValueError('Runner lock policy prevents native acceptance.')
        checks['apply_and_readback'] = policy.apply(consent=True)['verified']
        saved = policy.load()
        checks['dc_unchanged'] = all(native.read(saved['bridge_scheme'], sub, setting, dc=True) == values[name][1]
                                    for name, sub, setting in SETTINGS if name in values)
        checks['original_plan_unchanged'] = all(native.read(original, sub, setting) == values[name][0]
                                               for name, sub, setting in SETTINGS if name in values)
        policy.restore()
        checks['original_plan_restored'] = native.scheme() == original
        checks['registry_restored'] = [native.registry(p, n) for p, n, _ in USER_VALUES] == registry
        success = all(checks.values())
    finally:
        policy.restore()
        saved = policy.load()
        if saved.get('bridge_scheme') and native.scheme() != saved['bridge_scheme']:
            native.delete(saved['bridge_scheme'])
        atomic_json(output / 'acceptance.json', {'success': success, 'checks': checks,
            'scope': 'disposable Windows runner power policy only; not real owner login or Cloud deployment'})
    print(json.dumps({'success': success, 'checks': checks}))
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
