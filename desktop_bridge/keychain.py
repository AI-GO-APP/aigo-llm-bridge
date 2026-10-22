"""macOS login Keychain, via Security.framework; secrets never enter argv/files."""
import ctypes as c
import hashlib
from pathlib import Path

SERVICE = b'org.aigo.llm-bridge.device'
NOT_FOUND = -25300


def account(directory, pending=False):
    return (hashlib.sha256(str(Path(directory).resolve()).encode()).hexdigest()
            + ('.pending' if pending else '.active')).encode()


class Keychain:
    def __init__(self):
        self.api = c.CDLL('/System/Library/Frameworks/Security.framework/Security')
        self.core = c.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        self.core.CFRelease.argtypes = [c.c_void_p]
        signatures = {
            'SecKeychainFindGenericPassword': [c.c_void_p,c.c_uint32,c.c_char_p,c.c_uint32,c.c_char_p,c.POINTER(c.c_uint32),c.POINTER(c.c_void_p),c.POINTER(c.c_void_p)],
            'SecKeychainAddGenericPassword': [c.c_void_p,c.c_uint32,c.c_char_p,c.c_uint32,c.c_char_p,c.c_uint32,c.c_void_p,c.POINTER(c.c_void_p)],
            'SecKeychainItemModifyAttributesAndData': [c.c_void_p,c.c_void_p,c.c_uint32,c.c_void_p],
            'SecKeychainItemFreeContent': [c.c_void_p,c.c_void_p],
            'SecKeychainItemDelete': [c.c_void_p],
        }
        for name, args in signatures.items():
            function = getattr(self.api, name); function.argtypes = args; function.restype = c.c_int32

    def find(self, name):
        size, data, item = c.c_uint32(), c.c_void_p(), c.c_void_p()
        code = self.api.SecKeychainFindGenericPassword(None,len(SERVICE),SERVICE,len(name),name,c.byref(size),c.byref(data),c.byref(item))
        if code == NOT_FOUND: return '', None
        if code: raise ValueError('無法存取 macOS 登入鑰匙圈；請解鎖原使用者的 Keychain。')
        try: value = c.string_at(data,size.value).decode()
        finally: self.api.SecKeychainItemFreeContent(None,data)
        return value, item

    def get(self, name):
        value, item = self.find(name)
        if item: self.core.CFRelease(item)
        return value

    def put(self, name, value):
        _, item = self.find(name); data = value.encode()
        try:
            if item:
                code = self.api.SecKeychainItemModifyAttributesAndData(item,None,len(data),data)
            else:
                code = self.api.SecKeychainAddGenericPassword(None,len(SERVICE),SERVICE,len(name),name,len(data),data,None)
            if code: raise ValueError('macOS 無法保存裝置憑證；未改用明文檔。')
        finally:
            if item: self.core.CFRelease(item)

    def delete(self, name):
        _, item = self.find(name)
        if not item: return
        try:
            if self.api.SecKeychainItemDelete(item): raise ValueError('無法清除未完成的鑰匙圈配對。')
        finally: self.core.CFRelease(item)
