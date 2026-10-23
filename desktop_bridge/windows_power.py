"""Windows AC-only availability settings. No machine security-policy overrides.

Native calls live behind a small adapter so tests cannot change the host policy.
The original power scheme and HKCU values are backed up before the first write.
"""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import threading
import uuid

from .windows_release import atomic_json

SLEEP = '238c9fa8-0aad-41ed-83f4-97be242c8f20'
VIDEO = '7516b95f-f776-4464-8c53-06167f40cc99'
BUTTONS = '4f971e89-eebd-4455-a8de-9e59040e7347'
# name, subgroup, setting; all indexes are AC-only, 0 = never / do nothing.
SETTINGS = (
    ('sleep', SLEEP, '29f6c1db-86da-48c5-9fdb-f2b67b1f44da'),
    ('hibernate', SLEEP, '9d7815a6-7ee4-497e-8888-515a05f02364'),
    ('unattended_sleep', SLEEP, '7bc4a2f9-d8fc-4469-b07b-33eb785aaca0'),
    ('display', VIDEO, '3c0bc021-c8a8-4e07-a973-6b14cbcb2b7e'),
    ('locked_display', VIDEO, '8ec4b3a5-6868-48c2-be75-4f3044be88a7'),
    ('lid', BUTTONS, '5ca83367-6e45-459f-a27b-476b1d01c936'),
    ('sleep_button', BUTTONS, '96996bc0-ad50-47ec-923b-6f41874dd9eb'),
    ('power_button', BUTTONS, '7648efa3-dd9c-4e3e-b566-50f929386280'),
)
USER_VALUES = (
    (r'Control Panel\Desktop', 'ScreenSaveActive', '0'),
    (r'Control Panel\Desktop', 'ScreenSaverIsSecure', '0'),
    (r'Software\Microsoft\Windows NT\CurrentVersion\Winlogon', 'EnableGoodbye', 0),
)


class GUID(ctypes.Structure):
    _fields_ = [('a', wintypes.DWORD), ('b', wintypes.WORD), ('c', wintypes.WORD), ('d', ctypes.c_ubyte * 8)]

    @classmethod
    def parse(cls, text):
        return cls.from_buffer_copy(uuid.UUID(text).bytes_le)

    def text(self):
        return str(uuid.UUID(bytes_le=bytes(self)))


class NativePower:
    def __init__(self):
        import winreg
        self.reg = winreg
        self.dll = ctypes.WinDLL('powrprof', use_last_error=True)
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        ptr = ctypes.POINTER(GUID)
        self.dll.PowerGetActiveScheme.argtypes = [wintypes.HKEY, ctypes.POINTER(ptr)]
        self.dll.PowerDuplicateScheme.argtypes = [wintypes.HKEY, ptr, ctypes.POINTER(ptr)]
        self.dll.PowerSetActiveScheme.argtypes = [wintypes.HKEY, ptr]
        self.dll.PowerDeleteScheme.argtypes = [wintypes.HKEY, ptr]
        for name in ('PowerReadACValueIndex', 'PowerReadDCValueIndex'):
            getattr(self.dll, name).argtypes = [wintypes.HKEY, ptr, ptr, ptr, ctypes.POINTER(wintypes.DWORD)]
        self.dll.PowerWriteACValueIndex.argtypes = [wintypes.HKEY, ptr, ptr, ptr, wintypes.DWORD]
        self.kernel.LocalFree.argtypes = [ctypes.c_void_p]
        self.kernel.LocalFree.restype = ctypes.c_void_p

    @staticmethod
    def check(code):
        if code:
            raise OSError(code, 'Windows power operation failed.')

    def scheme(self, duplicate=None):
        out = ctypes.POINTER(GUID)()
        if duplicate:
            value = GUID.parse(duplicate)
            code = self.dll.PowerDuplicateScheme(None, ctypes.byref(value), ctypes.byref(out))
        else:
            code = self.dll.PowerGetActiveScheme(None, ctypes.byref(out))
        self.check(code)
        try:
            return out.contents.text()
        finally:
            self.kernel.LocalFree(out)

    def read(self, scheme, sub, setting, dc=False):
        values = [GUID.parse(v) for v in (scheme, sub, setting)]
        out = wintypes.DWORD()
        self.check(getattr(self.dll, 'PowerReadDCValueIndex' if dc else 'PowerReadACValueIndex')(
            None, *(ctypes.byref(v) for v in values), ctypes.byref(out)))
        return out.value

    def write(self, scheme, sub, setting, value):
        values = [GUID.parse(v) for v in (scheme, sub, setting)]
        self.check(self.dll.PowerWriteACValueIndex(None, *(ctypes.byref(v) for v in values), value))

    def activate(self, scheme):
        self.check(self.dll.PowerSetActiveScheme(None, ctypes.byref(GUID.parse(scheme))))

    def delete(self, scheme):
        self.check(self.dll.PowerDeleteScheme(None, ctypes.byref(GUID.parse(scheme))))

    def registry(self, path, name, *, machine=False):
        hive = self.reg.HKEY_LOCAL_MACHINE if machine else self.reg.HKEY_CURRENT_USER
        try:
            with self.reg.OpenKey(hive, path) as key:
                value, kind = self.reg.QueryValueEx(key, name)
                return {'exists': True, 'value': value, 'type': kind}
        except FileNotFoundError:
            return {'exists': False}

    def set_registry(self, path, name, value):
        if self.registry(path, name) == value:
            return
        with self.reg.CreateKey(self.reg.HKEY_CURRENT_USER, path) as key:
            if value['exists']:
                self.reg.SetValueEx(key, name, 0, value['type'], value['value'])
            else:
                try:
                    self.reg.DeleteValue(key, name)
                except FileNotFoundError:
                    pass
        if path == r'Control Panel\Desktop' and name == 'ScreenSaveActive':
            active = value.get('value', '0') == '1'
            if not self.user.SystemParametersInfoW(0x0011, int(active), None, 2):
                raise OSError('Screen saver setting could not be applied.')

    def ac(self):
        class Status(ctypes.Structure):
            _fields_ = [('ac', ctypes.c_byte), ('flag', ctypes.c_byte), ('percent', ctypes.c_byte),
                        ('reserved', ctypes.c_byte), ('life', wintypes.DWORD), ('full', wintypes.DWORD)]
        value = Status()
        self.check(0 if self.kernel.GetSystemPowerStatus(ctypes.byref(value)) else 1)
        return value.ac == 1  # Unknown / disconnected restores the original user lock settings.


class PowerPolicy:
    def __init__(self, directory, native=None):
        self.path = Path(directory) / 'windows-power.json'
        self.native = native or NativePower()
        self.lock = threading.RLock()
        self.suspended = False

    def load(self):
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding='utf-8'))

    def blockers(self, include_user=True):
        checks = (
            (True, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System', 'InactivityTimeoutSecs'),
            (True, r'SOFTWARE\Microsoft\PolicyManager\current\device\DeviceLock', 'MaxInactivityTimeDeviceLock'),
            (False, r'Software\Policies\Microsoft\Windows\Control Panel\Desktop', 'ScreenSaveActive'),
            (False, r'Software\Policies\Microsoft\Windows\Control Panel\Desktop', 'ScreenSaverIsSecure'),
        )
        blocked = []
        for machine, path, name in checks:
            if not machine and not include_user:
                continue
            value = self.native.registry(path, name, machine=machine)
            if value['exists'] and str(value['value']) not in {'', '0'}:
                blocked.append(name)
        for name, _sub, setting in SETTINGS:
            value = self.native.registry(r'SOFTWARE\Policies\Microsoft\Power\PowerSettings' + '\\' + setting,
                                         'ACSettingIndex', machine=True)
            if value['exists'] and value['value'] != 0:
                blocked.append('AC_' + name)
        return blocked

    def inspect(self, check_user=True):
        with self.lock:
            saved = self.load()
            blocked = self.blockers(include_user=check_user)
            changed = []
            if saved.get('enabled'):
                if self.native.scheme() != saved['bridge_scheme']:
                    changed.append('active_scheme')
                for name, sub, setting in SETTINGS:
                    if name in saved['settings'] and self.native.read(saved['bridge_scheme'], sub, setting) != 0:
                        changed.append(name)
                if check_user and self.native.ac():
                    for path, name, expected in USER_VALUES:
                        value = self.native.registry(path, name)
                        if not value['exists'] or value['value'] != expected:
                            changed.append(name)
            return {'enabled': bool(saved.get('enabled')), 'verified': bool(saved.get('enabled')) and not blocked and not changed,
                    'blockers': blocked, 'changed': changed, 'ac_connected': self.native.ac(),
                    'requires_manual_check': ['presence_sensing', 'vendor_power_tools', 'forced_shutdown'],
                    'unsupported': saved.get('unsupported', [])}

    def apply(self, consent=False, *, user_values=None, manage_user=True):
        if consent is not True:
            raise ValueError('Explicit AC power and lock-setting consent is required.')
        with self.lock:
            if self.blockers(include_user=manage_user):
                raise ValueError('Managed lock policy must be resolved by the device administrator first.')
            saved = self.load()
            if saved.get('enabled'):
                return self.inspect(check_user=manage_user)
            original = self.native.scheme()
            # Capture all supported values (including DC) before changing anything.
            settings, unsupported = {}, []
            for name, sub, setting in SETTINGS:
                try:
                    settings[name] = {'ac': self.native.read(original, sub, setting),
                                      'dc': self.native.read(original, sub, setting, dc=True)}
                except OSError as error:
                    if error.errno not in {2, 50, 87}:
                        raise
                    unsupported.append(name)
            if not all(k in settings for k in ('sleep', 'display')):
                raise ValueError('This device does not expose the required power controls.')
            scheme = self.native.scheme(duplicate=original)
            saved = {'schema': 1, 'enabled': False, 'original_scheme': original, 'bridge_scheme': scheme,
                     'settings': settings, 'unsupported': unsupported,
                     'user_values': user_values if user_values is not None else [self.native.registry(p, n) for p, n, _ in USER_VALUES]}
            atomic_json(self.path, saved)
            try:
                for name, sub, setting in SETTINGS:
                    if name in settings:
                        self.native.write(scheme, sub, setting, 0)
                        if self.native.read(scheme, sub, setting) != 0 or self.native.read(scheme, sub, setting, dc=True) != settings[name]['dc']:
                            raise OSError('Power readback did not match the AC-only plan.')
                self.native.activate(scheme)
                saved['enabled'] = True
                atomic_json(self.path, saved)
                if manage_user:
                    self.tick()
                return self.inspect(check_user=manage_user)
            except Exception:
                self.native.activate(original)
                if manage_user:
                    self._restore_user(saved)
                saved['enabled'] = False
                atomic_json(self.path, saved)
                raise

    def _restore_user(self, saved):
        for (path, name, expected), value in zip(USER_VALUES, saved.get('user_values', [])):
            current = self.native.registry(path, name)
            # Preserve a later change made by the owner outside Bridge.
            if current.get('value') == expected:
                self.native.set_registry(path, name, value)

    def tick(self):
        with self.lock:
            if self.suspended:
                return
            saved = self.load()
            if not saved.get('enabled'):
                return
            if self.native.ac():
                for path, name, value in USER_VALUES:
                    self.native.set_registry(path, name, {'exists': True, 'value': value, 'type': 4 if isinstance(value, int) else 1})
                if not saved.get('user_relaxed'):
                    saved['user_relaxed'] = True
                    atomic_json(self.path, saved)
            elif saved.get('user_relaxed'):
                self._restore_user(saved)
                saved['user_relaxed'] = False
                atomic_json(self.path, saved)

    def restore(self, *, manage_user=True):
        with self.lock:
            saved = self.load()
            if saved.get('bridge_scheme'):
                # Do not replace an unrelated power plan selected by the owner later.
                if self.native.scheme() == saved['bridge_scheme']:
                    self.native.activate(saved['original_scheme'])
                if manage_user:
                    self._restore_user(saved)
                saved['enabled'] = False
                saved['user_relaxed'] = False
                atomic_json(self.path, saved)
            return {'restored': True}

    def stop(self):
        # Power plan persists; user lock settings are only relaxed while the guard runs on AC.
        with self.lock:
            saved = self.load()
            if saved.get('enabled'):
                self._restore_user(saved)
                saved['user_relaxed'] = False
                atomic_json(self.path, saved)
