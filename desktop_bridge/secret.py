"""Device relay secret: Windows DPAPI or macOS Keychain; never plaintext."""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import sys


def uses_keychain():return sys.platform=='darwin'


class Blob(ctypes.Structure):
    _fields_=[("cbData",wintypes.DWORD),("pbData",ctypes.POINTER(ctypes.c_byte))]


def protect(data,decrypt=False):
    if os.name!="nt": raise ValueError("P1 裝置憑證儲存目前僅支援 Windows DPAPI。")
    buffer=ctypes.create_string_buffer(data)
    source=Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_byte))); target=Blob()
    crypt=ctypes.WinDLL("crypt32",use_last_error=True)
    function=crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    if not function(ctypes.byref(source),None,None,None,None,1,ctypes.byref(target)):
        raise ValueError("Windows 無法存取裝置憑證。請使用原安裝帳號重新設定。")
    try: return ctypes.string_at(target.pbData,target.cbData)
    finally:
        kernel=ctypes.WinDLL("kernel32"); kernel.LocalFree.argtypes=[ctypes.c_void_p]
        kernel.LocalFree(target.pbData)


def credential_path(directory,pending=False):
    return Path(directory)/('relay-device.pending.dpapi' if pending else 'relay-device.dpapi')


def save(directory,value,*,pending=False):
    if not isinstance(value,str) or not 32<=len(value)<=256:
        raise ValueError("裝置配對 key 長度需介於 32–256 字。")
    if uses_keychain():
        from .keychain import Keychain,account
        Keychain().put(account(directory,pending),value)
    else:
        path=credential_path(directory,pending)
        # Write atomically so power loss cannot truncate an existing credential.
        temporary=path.with_suffix('.tmp')
        temporary.write_bytes(protect(value.encode()))
        os.replace(temporary,path)


def load(directory,*,pending=False):
    if uses_keychain():
        from .keychain import Keychain,account
        return Keychain().get(account(directory,pending))
    path=credential_path(directory,pending)
    if not path.exists(): return ""
    return protect(path.read_bytes(),decrypt=True).decode()


def commit_pending(directory):
    if uses_keychain():
        from .keychain import Keychain,account
        value=load(directory,pending=True)
        if not value:raise ValueError('缺少未完成的配對憑證。')
        save(directory,value)
        Keychain().delete(account(directory,True))
    else:
        os.replace(credential_path(directory,True),credential_path(directory))
