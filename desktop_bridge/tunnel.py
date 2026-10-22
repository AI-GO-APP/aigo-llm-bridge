"""Named Cloudflare tunnels only. No random URL is presented as persistent."""
from pathlib import Path
import shutil
import subprocess
import threading


class Tunnel:
    def __init__(self):
        self.proc=None
        self.state="未啟動"
    def start(self,name):
        if self.proc and self.proc.poll() is None: return
        binary=shutil.which("cloudflared")
        if not binary: raise ValueError("尚未安裝 cloudflared。請依設定文件安裝並建立 Named Tunnel。")
        if not name or len(name)>100 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in name):
            raise ValueError("請填入已建立的 tunnel 名稱或 UUID。")
        self.proc=subprocess.Popen([binary,"tunnel","--no-autoupdate","run",name],stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        self.state="連線中"
        def read(proc):
            for line in proc.stderr:
                if b"Registered tunnel connection" in line: self.state="已連線"
            if self.proc is proc: self.state="已停止／請檢查 Cloudflare 設定"
        threading.Thread(target=read,args=(self.proc,),daemon=True).start()
    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try: self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired: self.proc.kill(); self.proc.wait(timeout=5)
        self.proc=None; self.state="未啟動"
