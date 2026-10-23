"""Windows AC-only automatic sleep settings. Lock and display settings are untouched.

Native calls live behind a small adapter so tests cannot change the host policy.
The original power scheme is backed up before the first write.
"""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import threading
import uuid

from .windows_release import atomic_json

SLEEP = '238c9fa8-0aad-41ed-83f4-97be242c8f20'
# name, subgroup, setting; all indexes are AC-only, 0 = never / do nothing.
SETTINGS = (
    ('sleep', SLEEP, '29f6c1db-86da-48c5-9fdb-f2b67b1f44da'),
    ('hibernate', SLEEP, '9d7815a6-7ee4-497e-8888-515a05f02364'),
    ('unattended_sleep', SLEEP, '7bc4a2f9-d8fc-4469-b07b-33eb785aaca0'),
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

    def ac(self):
        class Status(ctypes.Structure):
            _fields_ = [('ac', ctypes.c_byte), ('flag', ctypes.c_byte), ('percent', ctypes.c_byte),
                        ('reserved', ctypes.c_byte), ('life', wintypes.DWORD), ('full', wintypes.DWORD)]
        value = Status()
        self.check(0 if self.kernel.GetSystemPowerStatus(ctypes.byref(value)) else 1)
        return value.ac == 1


class PowerPolicy:
    def __init__(self, directory, native=None):
        self.path = Path(directory) / 'windows-power.json'
        self.native = native or NativePower()
        self.lock = threading.RLock()

    def load(self):
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding='utf-8'))

    def blockers(self):
        blocked = []
        # Screen-lock / screensaver policies are deliberately irrelevant here.
        for name, _sub, setting in SETTINGS:
            value = self.native.registry(r'SOFTWARE\Policies\Microsoft\Power\PowerSettings' + '\\' + setting,
                                         'ACSettingIndex', machine=True)
            if value['exists'] and value['value'] != 0:
                blocked.append('AC_' + name)
        return blocked

    def inspect(self):
        with self.lock:
            saved = self.load()
            blocked = self.blockers()
            changed = []
            if saved.get('enabled'):
                if saved.get('schema') != 2:
                    changed.append('legacy_unreleased_settings')
                if self.native.scheme() != saved['bridge_scheme']:
                    changed.append('active_scheme')
                for name, sub, setting in SETTINGS:
                    if name in saved['settings'] and self.native.read(saved['bridge_scheme'], sub, setting) != 0:
                        changed.append(name)
            return {'enabled': bool(saved.get('enabled')), 'verified': bool(saved.get('enabled')) and not blocked and not changed,
                    'blockers': blocked, 'changed': changed, 'ac_connected': self.native.ac(),
                    'requires_manual_check': ['vendor_sleep_tools', 'manual_sleep_or_lid', 'forced_shutdown'],
                    'unsupported': saved.get('unsupported', [])}

    @staticmethod
    def current_schema(saved):
        if saved.get('enabled') and saved.get('schema') != 2:
            raise ValueError('Restore the unreleased legacy power settings using their original candidate before continuing.')

    def apply(self, consent=False):
        if consent is not True:
            raise ValueError('Explicit AC automatic-sleep setting consent is required.')
        with self.lock:
            if self.blockers():
                raise ValueError('Managed sleep policy must be resolved by the device administrator first.')
            saved = self.load()
            self.current_schema(saved)
            if saved.get('enabled'):
                return self.inspect()
            original = self.native.scheme()
            settings, unsupported = {}, []
            for name, sub, setting in SETTINGS:
                try:
                    settings[name] = {'ac': self.native.read(original, sub, setting),
                                      'dc': self.native.read(original, sub, setting, dc=True)}
                except OSError as error:
                    if error.errno not in {2, 50, 87}:
                        raise
                    unsupported.append(name)
            if 'sleep' not in settings:
                raise ValueError('This device does not expose the required sleep control.')
            scheme = self.native.scheme(duplicate=original)
            saved = {'schema': 2, 'enabled': False, 'original_scheme': original, 'bridge_scheme': scheme,
                     'settings': settings, 'unsupported': unsupported}
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
                return self.inspect()
            except Exception:
                self.native.activate(original)
                saved['enabled'] = False
                atomic_json(self.path, saved)
                raise

    def restore(self):
        with self.lock:
            saved = self.load()
            self.current_schema(saved)
            if saved.get('bridge_scheme'):
                # Preserve a different plan selected by the owner later.
                if self.native.scheme() == saved['bridge_scheme']:
                    self.native.activate(saved['original_scheme'])
                saved['enabled'] = False
                atomic_json(self.path, saved)
            return {'restored': True}
