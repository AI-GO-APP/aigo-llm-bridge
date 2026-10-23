import argparse
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
    from .windows import Instance
    instance=Instance(args.data_dir)
    if not instance.primary:
        if not args.background and not args.no_activate: instance.notify()
        instance.close(); return 0
    threading.excepthook=lambda _args:None
    store=Store(args.data_dir); runtime=Runtime(store)
    try: api=ApiServer(runtime,port=args.port)
    except OSError:
        runtime.stop(); store.close()
        instance.close()
        if args.headless: return 2
        import tkinter as tk
        from tkinter import messagebox
        root=tk.Tk(); root.withdraw(); messagebox.showinfo("Bridge 已執行或連接埠被使用","請開啟既有管理視窗，或更換連接埠。",parent=root); root.destroy()
        return 2
    api.start()
    from .relay import Relay
    relay=Relay(store,api.port)
    if store.get("relay_enabled"):
        try: relay.start()
        except ValueError: pass
    if args.headless:
        done=threading.Event()
        signal.signal(signal.SIGINT,lambda *_:done.set())
        if hasattr(signal,"SIGTERM"): signal.signal(signal.SIGTERM,lambda *_:done.set())
        try:
            while not done.wait(30): store.prune(); runtime.cleanup()
        finally: relay.stop(); runtime.stop(); api.stop(); store.close(); instance.close()
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
        signal.signal(signal.SIGINT,lambda *_:done.set())
        if hasattr(signal,"SIGTERM"): signal.signal(signal.SIGTERM,lambda *_:done.set())
        def open_console():
            if sys.platform == 'darwin': manager.open_console()
            else: webbrowser.open(manager.url)
        if not args.background and not args.no_activate: open_console()
        last_cleanup=0
        try:
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
        finally:
            manager.stop(); relay.stop(); runtime.stop(); api.stop(); store.close(); instance.close()
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
    store.close()
    instance.close()
    return 0


if __name__=="__main__":
    raise SystemExit(main())
