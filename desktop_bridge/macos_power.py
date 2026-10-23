"""Explicit AC idle-sleep policy. Never changes locks, displays, batteries or lid actions."""
import json
from pathlib import Path
import re
import subprocess
import threading

from .windows_release import atomic_json


def parse_settings(text):
    values, current = {}, None
    for line in text.splitlines():
        if line and not line[0].isspace() and line.endswith(':'):
            current = line[:-1]
            values[current] = {}
        elif current:
            match = re.fullmatch(r'\s+([a-z_]+)\s+(\d+)\s*', line)
            if match:
                values[current][match[1]] = int(match[2])
    if 'sleep' not in values.get('AC Power', {}):
        raise ValueError('AC idle-sleep setting is unavailable.')
    return values


class NativePower:
    def read(self):
        result = subprocess.run(['/usr/bin/pmset', '-g', 'custom'], capture_output=True, text=True, timeout=10)
        if result.returncode:
            raise OSError('Cannot inspect power settings.')
        return parse_settings(result.stdout)

    def write(self, minutes, admin=False):
        if type(minutes) is not int or not 0 <= minutes <= 1440:
            raise ValueError('Invalid sleep interval.')
        command = ['/usr/bin/pmset', '-c', 'sleep', str(minutes)]
        if admin:
            # Fixed executable and validated integer only; no credential, shell input or user path.
            script = 'do shell script "/usr/bin/pmset -c sleep ' + str(minutes) + '" with administrator privileges'
            command = ['/usr/bin/osascript', '-e', script]
        result = subprocess.run(command, capture_output=True, timeout=180)
        if result.returncode:
            raise PermissionError(13, 'Power change was denied or cancelled.')


class PowerPolicy:
    def __init__(self, directory, native=None):
        self.path = Path(directory) / 'macos-power.json'
        self.native = native or NativePower()
        self.lock = threading.RLock()

    def load(self):
        return json.loads(self.path.read_text()) if self.path.exists() else {}

    def inspect(self):
        values = self.native.read()
        saved = self.load()
        sleep = values['AC Power']['sleep']
        return {'enabled': bool(saved.get('enabled')), 'verified': sleep == 0,
                'ac_sleep_minutes': sleep, 'changed': ['AC_sleep'] if saved.get('enabled') and sleep != 0 else [],
                'blockers': [], 'unsupported': [], 'scope': 'AC_idle_sleep_only'}

    def apply(self, consent=False, admin=False):
        if consent is not True:
            raise ValueError('Explicit AC idle-sleep consent is required.')
        with self.lock:
            values = self.native.read()
            saved = self.load()
            if saved.get('enabled'):
                if not self.inspect()['verified']:
                    raise ValueError('Power setting changed; restore or inspect it before applying again.')
                return self.inspect()
            if not saved.get('pending'):
                saved = {'schema': 1, 'enabled': False, 'pending': True, 'original_sleep': values['AC Power']['sleep']}
            atomic_json(self.path, saved)  # Backup must precede the first OS write.
            if values['AC Power']['sleep'] != 0:
                self.native.write(0, admin=admin)
            after = self.native.read()
            expected = {k: dict(v) for k, v in values.items()}
            expected['AC Power']['sleep'] = 0
            if after != expected:
                if after['AC Power']['sleep'] == 0 and saved['original_sleep'] != 0:
                    self.native.write(saved['original_sleep'], admin=admin)
                raise ValueError('Power readback failed; no verified policy was recorded.')
            atomic_json(self.path, {**saved, 'enabled': True, 'pending': False})
            return self.inspect()

    def restore(self, admin=False):
        with self.lock:
            saved = self.load()
            if not saved.get('enabled') and not saved.get('pending'):
                return self.inspect()
            current = self.native.read()['AC Power']['sleep']
            if current == saved['original_sleep'] and saved.get('pending'):
                atomic_json(self.path, {**saved, 'enabled': False, 'pending': False})
                return self.inspect()
            if current != 0:
                raise ValueError('Owner changed the sleep setting; do not overwrite it.')
            if saved['original_sleep'] != 0:
                self.native.write(saved['original_sleep'], admin=admin)
            if self.native.read()['AC Power']['sleep'] != saved['original_sleep']:
                raise ValueError('Restore readback failed.')
            atomic_json(self.path, {**saved, 'enabled': False, 'pending': False})
            return self.inspect()
