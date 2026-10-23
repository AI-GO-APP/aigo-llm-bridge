"""Narrow UAC helper: power plan only, never the administrator's HKCU or credentials."""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import secrets
import subprocess
import time

from .windows_power import PowerPolicy, USER_VALUES
from .windows_release import atomic_json, stable_entry


def elevated(directory, nonce, operation):
    """Console entry called after UAC. No arbitrary executable / registry / shell operation."""
    if not ctypes.windll.shell32.IsUserAnAdmin():
        return 1
    path = Path(directory) / 'windows-power-elevation.json'
    request = json.loads(path.read_text(encoding='utf-8'))
    if (request.get('nonce') != nonce or operation not in {'apply', 'restore'}
            or request.get('operation') != operation or not 0 <= time.time() - request['created_at'] <= 300):
        return 1
    policy = PowerPolicy(directory)
    values = request['user_values']
    if not isinstance(values, list) or len(values) != len(USER_VALUES):
        return 1
    for value in values:
        if not isinstance(value, dict) or type(value.get('exists')) is not bool:
            return 1
        if value['exists'] and (value.get('type') not in {1, 4} or type(value.get('value')) not in {str, int}):
            return 1
    try:
        if operation == 'apply':
            result = policy.apply(consent=True, user_values=values, manage_user=False)
            return 0 if result['verified'] else 1
        policy.restore(manage_user=False)
        return 0
    finally:
        path.unlink(missing_ok=True)


def request(policy, operation):
    policy.suspended = True
    try:
        return _request(policy, operation)
    finally:
        policy.suspended = False


def _request(policy, operation):
    if operation not in {'apply', 'restore'}:
        raise ValueError()
    if policy.blockers():
        raise ValueError('Managed security policy must be handled by its administrator.')
    if operation == 'restore':
        # Always restore the installing user's values in that user's process.
        policy.stop()
    values = [policy.native.registry(p, n) for p, n, _ in USER_VALUES]
    if policy.load().get('enabled'):
        values = policy.load()['user_values']
    path = policy.path.parent / 'windows-power-elevation.json'
    nonce = secrets.token_hex(16)
    atomic_json(path, {'schema': 1, 'nonce': nonce, 'operation': operation,
                       'created_at': time.time(), 'user_values': values})
    class Execute(ctypes.Structure):
        _fields_ = [('cbSize', wintypes.DWORD), ('fMask', wintypes.ULONG), ('hwnd', wintypes.HWND),
                    ('lpVerb', wintypes.LPCWSTR), ('lpFile', wintypes.LPCWSTR), ('lpParameters', wintypes.LPCWSTR),
                    ('lpDirectory', wintypes.LPCWSTR), ('nShow', ctypes.c_int), ('hInstApp', wintypes.HINSTANCE),
                    ('lpIDList', ctypes.c_void_p), ('lpClass', wintypes.LPCWSTR), ('hkeyClass', wintypes.HKEY),
                    ('dwHotKey', wintypes.DWORD), ('hIcon', wintypes.HANDLE), ('hProcess', wintypes.HANDLE)]
    info = Execute()
    info.cbSize = ctypes.sizeof(info)
    info.fMask = 0x40  # SEE_MASK_NOCLOSEPROCESS
    info.lpVerb = 'runas'
    info.lpFile = str(stable_entry('aigo-bridge.exe'))
    info.lpParameters = subprocess.list2cmdline(['power-admin', '--data-dir', str(policy.path.parent),
                                               '--nonce', nonce, '--operation', operation])
    info.nShow = 0
    shell = ctypes.WinDLL('shell32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    shell.ShellExecuteExW.argtypes = [ctypes.POINTER(Execute)]
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    try:
        if not shell.ShellExecuteExW(ctypes.byref(info)):
            raise OSError(5, 'UAC consent was cancelled or unavailable.')
        try:
            # This waits on a background onboarding thread; management stays responsive.
            if kernel.WaitForSingleObject(info.hProcess, 300000) != 0:
                raise OSError('Power administrator helper did not finish; inspect settings before retrying.')
            code = wintypes.DWORD()
            if not kernel.GetExitCodeProcess(info.hProcess, ctypes.byref(code)) or code.value != 0:
                raise OSError(5, 'Power administrator helper failed.')
        finally:
            kernel.CloseHandle(info.hProcess)
        policy.suspended = False
        policy.tick()
        return policy.inspect() if operation == 'apply' else {'restored': True}
    finally:
        path.unlink(missing_ok=True)
