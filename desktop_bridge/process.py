"""Own-process lifecycle only: never kill a user's existing CLI by name."""
from __future__ import annotations

import ctypes
import os
import signal
import subprocess
import threading
import time

from .errors import BridgeError


class Child:
    def __init__(self, command, cwd, env, *, memory_limit=None):
        self.job=None
        flags=0
        if os.name=="nt":
            flags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        self.proc=subprocess.Popen(command,cwd=cwd,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,creationflags=flags,start_new_session=os.name!="nt")
        if os.name=="nt":
            from ctypes import wintypes as w
            class Basic(ctypes.Structure):
                _fields_=[("ProcessTime",ctypes.c_longlong),("JobTime",ctypes.c_longlong),("Flags",w.DWORD),
                    ("MinWorking",ctypes.c_size_t),("MaxWorking",ctypes.c_size_t),("Active",w.DWORD),
                    ("Affinity",ctypes.c_size_t),("Priority",w.DWORD),("Scheduling",w.DWORD)]
            class IO(ctypes.Structure):
                _fields_=[(name,ctypes.c_ulonglong) for name in ("ReadOps","WriteOps","OtherOps","ReadBytes","WriteBytes","OtherBytes")]
            class Extended(ctypes.Structure):
                _fields_=[("Basic",Basic),("Io",IO),("ProcessMemory",ctypes.c_size_t),("JobMemory",ctypes.c_size_t),
                          ("PeakProcess",ctypes.c_size_t),("PeakJob",ctypes.c_size_t)]
            kernel=ctypes.WinDLL("kernel32",use_last_error=True)
            kernel.CreateJobObjectW.restype=w.HANDLE
            kernel.CreateJobObjectW.argtypes=[ctypes.c_void_p,w.LPCWSTR]
            kernel.SetInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD]
            kernel.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE]
            kernel.CloseHandle.argtypes=[w.HANDLE]
            job=kernel.CreateJobObjectW(None,None)
            limits=Extended(); limits.Basic.Flags=0x2000  # KILL_ON_JOB_CLOSE
            if memory_limit is not None:
                limits.Basic.Flags |= 0x100  # JOB_OBJECT_LIMIT_PROCESS_MEMORY
                limits.ProcessMemory=memory_limit
            if not job or not kernel.SetInformationJobObject(job,9,ctypes.byref(limits),ctypes.sizeof(limits)) or not kernel.AssignProcessToJobObject(job,w.HANDLE(int(self.proc._handle))):
                if job: kernel.CloseHandle(job)
                self.proc.terminate(); self.proc.wait(timeout=10)
                raise BridgeError(503,"process_isolation","無法建立獨立 CLI 程序群組；未執行推論。")
            self.job=(job,kernel)

    def close(self):
        if self.job:
            job,kernel=self.job; self.job=None
            kernel.CloseHandle(job)
        elif self.proc.poll() is None:
            if os.name!="nt":
                try: os.killpg(self.proc.pid,signal.SIGTERM)
                except ProcessLookupError: pass
            else: self.proc.terminate()
        try: self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill(); self.proc.wait(timeout=5)
        for stream in (self.proc.stdin,self.proc.stdout,self.proc.stderr):
            if stream:
                try: stream.close()
                except OSError: pass

    def communicate(self, data, cancel, timeout):
        # Drain both pipes concurrently and cap retained output. Never create a log file.
        stdout=bytearray(); exceeded=threading.Event()
        def drain(stream, target=None):
            while True:
                part=stream.read(65536)
                if not part: break
                if target is not None:
                    if len(target)+len(part)>4_000_000:
                        exceeded.set(); break
                    target.extend(part)
        readers=[threading.Thread(target=drain,args=(self.proc.stdout,stdout),daemon=True),
                 threading.Thread(target=drain,args=(self.proc.stderr,),daemon=True)]
        for reader in readers: reader.start()
        self.proc.stdin.write(data); self.proc.stdin.close()
        deadline=time.monotonic()+timeout
        while self.proc.poll() is None:
            check_cancel(cancel,deadline)
            if exceeded.is_set():
                raise BridgeError(502,"output_too_large","CLI 輸出超過服務上限。")
            time.sleep(.05)
        for reader in readers: reader.join(timeout=3)
        if exceeded.is_set(): raise BridgeError(502,"output_too_large","CLI 輸出超過服務上限。")
        return bytes(stdout)


def check_cancel(cancel,deadline):
    if cancel.is_set(): raise BridgeError(499,"cancelled","請求已取消。")
    if time.monotonic()>deadline: raise BridgeError(408,"timeout","CLI 執行逾時。")
