import argparse
from contextlib import ExitStack
import os
from pathlib import Path
import signal
import sys
import threading
import time

from .service import ApiServer,Runtime
from .store import Store
from .paths import default_directory


def main():
    parser=argparse.ArgumentParser(description="Local subscription LLM bridge")
    parser.add_argument("--data-dir",default=str(default_directory()))
    parser.add_argument("--port",type=int)
    parser.add_argument("--headless",action="store_true")
    parser.add_argument("--background",action="store_true")
    parser.add_argument("--no-activate",action="store_true")
    parser.add_argument("--native-ui",action="store_true",help="Use the legacy Tkinter window")
    args=parser.parse_args()
    if sys.platform=='win32':
        from .windows_http import install as protect_listeners
        protect_listeners()
    from .windows import Instance
    try:
        instance=Instance(args.data_dir)
    except OSError:
        if sys.platform != 'win32': raise
        print('無法取得此設定檔的啟動識別；本次未開啟資料庫或服務。', file=sys.stderr)
        return 2
    if not instance.primary:
        if not args.background and not args.no_activate: instance.notify()
        instance.close(); return 0
    threading.excepthook=lambda _args:None
    machine = None
    try:
        if sys.platform == 'win32':
            from .windows_instance import MachineInstance, BUSY_EXIT, BUSY_MESSAGE
            try:
                machine = MachineInstance()
            except OSError:
                print('無法取得全機 Bridge 啟動鎖；本次未開啟設定檔。請檢查本機 TCP 8919。', file=sys.stderr)
                return 2
            if not machine.primary:
                print(BUSY_MESSAGE, file=sys.stderr)
                return BUSY_EXIT
        if sys.platform == 'darwin':
            from .macos_instance import MachineInstance
            try:
                machine = MachineInstance()
            except OSError:
                print('無法取得全機 Bridge 啟動鎖；為避免多開，本次未啟動。請檢查本機 TCP 8919。', file=sys.stderr)
                return 2
            if not machine.primary:
                print('一台電腦只能執行一個 Bridge。本機已有 Bridge 或 TCP 8919 被占用；請先正常結束既有 Bridge 再切換設定檔。', file=sys.stderr)
                # A rejected LaunchAgent must not retry forever (KeepAlive on failure).
                return 0 if args.background else 2
        return run(args, instance)
    finally:
        if machine is not None: machine.close()
        instance.close()


def run(args, instance):
    # Keep both instance locks until every initialized service has stopped,
    # including failures between API startup and management/relay startup.
    with ExitStack() as lifetime:
        return serve(args, instance, lifetime)


def serve(args, instance, lifetime):
    if sys.platform!='win32':
        from .capacity import ensure_file_limit
        ensure_file_limit()
    store=Store(args.data_dir)
    lifetime.callback(store.close)
    runtime=Runtime(store)
    lifetime.callback(runtime.stop)
    try: api=ApiServer(runtime,port=args.port)
    except OSError:
        if args.headless or (sys.platform=='win32' and args.background): return 2
        import tkinter as tk
        from tkinter import messagebox
        root=tk.Tk(); root.withdraw(); messagebox.showinfo("Bridge 已執行或連接埠被使用","請開啟既有管理視窗，或更換連接埠。",parent=root); root.destroy()
        return 2
    lifetime.callback(api.server.server_close)
    api.start()
    lifetime.callback(api.stop)
    from .relay import Relay
    relay=Relay(store,api.port)
    lifetime.callback(relay.stop)
    if store.get("relay_enabled"):
        try: relay.start()
        except ValueError: pass
    if args.headless:
        done=threading.Event()
        signal.signal(signal.SIGINT,lambda *_:done.set())
        if hasattr(signal,"SIGTERM"): signal.signal(signal.SIGTERM,lambda *_:done.set())
        while not done.wait(30): store.prune(); runtime.cleanup()
        return 0
    if not args.native_ui:
        import webbrowser
        if sys.platform == 'darwin':
            from .macos_management import MacManagementServer as ManagementServer
        else:
            from .management import ManagementServer
        done=threading.Event()
        manager=ManagementServer(store,runtime,api,relay,on_shutdown=done.set)
        manager.start()
        lifetime.callback(manager.stop)
        signal.signal(signal.SIGINT,lambda *_:done.set())
        if hasattr(signal,"SIGTERM"): signal.signal(signal.SIGTERM,lambda *_:done.set())
        def open_console():
            if sys.platform == 'darwin': manager.open_console()
            else: webbrowser.open(manager.url)
        if not args.background and not args.no_activate: open_console()
        last_cleanup=0
        while not done.wait(.5):
            if instance.requested(): open_console()
            if sys.platform == 'darwin':
                requested = store.directory / 'macos-onboarding-open.request'
                if requested.exists():
                    requested.unlink()
                    manager.onboarding.open_requested = True
                    open_console()
            if time.monotonic()-last_cleanup>60:
                store.prune()
                with runtime.lock: runtime.cleanup()
                last_cleanup=time.monotonic()
        return 0
    import tkinter as tk
    from .ui import App
    root=tk.Tk()
    if args.no_activate or args.background: root.withdraw()
    root.report_callback_exception=lambda *_:None
    app=App(root,store,runtime,api,args.background,relay=relay)
    def restore_requested():
        if app.closed: return
        if instance.requested(): root.deiconify(); root.lift()
        root.after(500,restore_requested)
    root.after(500,restore_requested)
    if args.no_activate and os.name=="nt":
        root.update_idletasks()
        import ctypes
        user=ctypes.windll.user32
        hwnd=user.GetParent(root.winfo_id())
        user.ShowWindow(hwnd,4)  # SW_SHOWNOACTIVATE
    elif args.background:
        root.iconify()
    root.mainloop()
    return 0


if __name__=="__main__":
    raise SystemExit(main())
