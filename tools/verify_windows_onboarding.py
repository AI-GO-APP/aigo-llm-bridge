"""Power-policy acceptance on a disposable hosted Windows runner ONLY.

Developer PCs use fake-adapter tests and read-only inspection. No owner workstation
may opt into the mutating part with a command flag. Lock settings are read-only.
"""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desktop_bridge.windows_power import NativePower, PowerPolicy, SETTINGS
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
    lock_values = [(r'Control Panel\Desktop', 'ScreenSaveActive'),
                   (r'Control Panel\Desktop', 'ScreenSaverIsSecure'),
                   (r'Software\Microsoft\Windows NT\CurrentVersion\Winlogon', 'EnableGoodbye')]
    registry = [native.registry(p, n) for p, n in lock_values]
    untouched = (
        ('7516b95f-f776-4464-8c53-06167f40cc99', '3c0bc021-c8a8-4e07-a973-6b14cbcb2b7e'),
        ('7516b95f-f776-4464-8c53-06167f40cc99', '8ec4b3a5-6868-48c2-be75-4f3044be88a7'),
        ('4f971e89-eebd-4455-a8de-9e59040e7347', '5ca83367-6e45-459f-a27b-476b1d01c936'),
        ('4f971e89-eebd-4455-a8de-9e59040e7347', '96996bc0-ad50-47ec-923b-6f41874dd9eb'),
        ('4f971e89-eebd-4455-a8de-9e59040e7347', '7648efa3-dd9c-4e3e-b566-50f929386280'),
    )
    protected = {}
    for sub, setting in untouched:
        try:
            protected[(sub, setting)] = (native.read(original, sub, setting), native.read(original, sub, setting, dc=True))
        except OSError as error:
            if error.errno not in {2, 50, 87}:
                raise
    values = {}
    for name, sub, setting in SETTINGS:
        try:
            values[name] = (native.read(original, sub, setting), native.read(original, sub, setting, dc=True))
        except OSError as error:
            if error.errno not in {2, 50, 87}:
                raise
    checks, success = {}, False
    try:
        checks['no_managed_sleep_policy'] = not policy.blockers()
        if not checks['no_managed_sleep_policy']:
            raise ValueError('Runner sleep policy prevents native acceptance.')
        checks['apply_and_readback'] = policy.apply(consent=True)['verified']
        saved = policy.load()
        checks['dc_unchanged'] = all(native.read(saved['bridge_scheme'], sub, setting, dc=True) == values[name][1]
                                    for name, sub, setting in SETTINGS if name in values)
        checks['original_plan_unchanged'] = all(native.read(original, sub, setting) == values[name][0]
                                               for name, sub, setting in SETTINGS if name in values)
        checks['display_and_buttons_unchanged'] = all(
            (native.read(saved['bridge_scheme'], sub, setting), native.read(saved['bridge_scheme'], sub, setting, dc=True)) == value
            for (sub, setting), value in protected.items())
        checks['lock_registry_unchanged_during_apply'] = [native.registry(p, n) for p, n in lock_values] == registry
        policy.restore()
        checks['original_plan_restored'] = native.scheme() == original
        checks['lock_registry_still_unchanged_after_restore'] = [native.registry(p, n) for p, n in lock_values] == registry
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
