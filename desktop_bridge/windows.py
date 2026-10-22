import os
from pathlib import Path
import subprocess
import sys
import hashlib


class Instance:
    """Per-data-directory event: a second shortcut restores the existing UI."""
    def __init__(self,data_dir):
        self.handle=None; self.primary=True; self.lockfile=None
        if os.name!="nt":
            import fcntl
            directory=Path(data_dir).resolve(); directory.mkdir(parents=True,exist_ok=True)
            self.activation=directory/'activate.request'
            self.lockfile=open(directory/'instance.lock','a+b')
            try:fcntl.flock(self.lockfile,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:self.primary=False
            return
        import ctypes
        from ctypes import wintypes as w
        self.kernel=ctypes.WinDLL("kernel32",use_last_error=True)
        self.kernel.CreateEventW.argtypes=[ctypes.c_void_p,w.BOOL,w.BOOL,w.LPCWSTR]
        self.kernel.CreateEventW.restype=w.HANDLE
        self.kernel.SetEvent.argtypes=[w.HANDLE]
        self.kernel.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD]
        self.kernel.CloseHandle.argtypes=[w.HANDLE]
        name="Local\\AigoLlmBridge_"+hashlib.sha256(str(Path(data_dir).resolve()).casefold().encode()).hexdigest()
        ctypes.set_last_error(0)
        self.handle=self.kernel.CreateEventW(None,False,False,name)
        if not self.handle: raise OSError("無法建立 Bridge 程序識別。")
        self.primary=ctypes.get_last_error()!=183
    def notify(self):
        if self.handle: self.kernel.SetEvent(self.handle)
        elif self.lockfile:self.activation.touch()
    def requested(self):
        if self.lockfile:
            try:self.activation.unlink();return True
            except FileNotFoundError:return False
        return bool(self.handle and self.kernel.WaitForSingleObject(self.handle,0)==0)
    def close(self):
        if self.handle: self.kernel.CloseHandle(self.handle); self.handle=None
        if self.lockfile:self.lockfile.close();self.lockfile=None


def startup_command(data_dir):
    if getattr(sys,"frozen",False):
        args=[sys.executable]
    else:
        python=Path(sys.executable).with_name("pythonw.exe")
        entry=Path(sys.argv[0])
        launcher=entry.absolute() if entry.name=='Bridge.pyw' and entry.is_file() else Path(__file__).with_name('launcher.py')
        args=[str(python if python.exists() else Path(sys.executable)),str(launcher)]
    return subprocess.list2cmdline(args+["--data-dir",str(Path(data_dir).resolve()),"--background"])


def mac_startup_path(data_dir=None):
    from .paths import default_directory
    identity=hashlib.sha256(str(Path(data_dir or default_directory()).resolve()).encode()).hexdigest()[:20]
    return Path.home()/'Library/LaunchAgents'/('org.aigo.llm-bridge.'+identity+'.plist')


def startup_enabled(data_dir=None):
    if sys.platform=='darwin':return mac_startup_path(data_dir).is_file()
    if os.name!="nt": return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
            return bool(winreg.QueryValueEx(key,"AigoLlmBridge")[0])
    except OSError: return False


def set_startup(enabled,data_dir):
    if sys.platform=='darwin':
        import plistlib
        path=mac_startup_path(data_dir)
        if not enabled:
            path.unlink(missing_ok=True)
            return
        path.parent.mkdir(parents=True,exist_ok=True)
        command=[sys.executable,str(Path(__file__).with_name('launcher.py')),'--data-dir',str(Path(data_dir).resolve()),'--background']
        if Path(sys.argv[0]).name=='Bridge.pyw' and Path(sys.argv[0]).is_file():
            command=[sys.executable,str(Path(sys.argv[0]).absolute()),'--background']
        if getattr(sys,'frozen',False):command=[sys.executable,*command[2:]]
        value={'Label':path.stem,'ProgramArguments':command,'RunAtLoad':True,
               'StandardOutPath':'/dev/null','StandardErrorPath':'/dev/null',
               'EnvironmentVariables':{'PATH':os.environ.get('PATH','/usr/bin:/bin:/usr/sbin:/sbin')}}
        temporary=path.with_suffix('.tmp');temporary.write_bytes(plistlib.dumps(value));temporary.chmod(0o600)
        os.replace(temporary,path)
        return
    if os.name!="nt": raise ValueError("自動啟動目前只支援 Windows。")
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
        if enabled: winreg.SetValueEx(key,"AigoLlmBridge",0,winreg.REG_SZ,startup_command(data_dir))
        else:
            try: winreg.DeleteValue(key,"AigoLlmBridge")
            except FileNotFoundError: pass
