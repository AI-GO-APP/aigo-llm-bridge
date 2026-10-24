"""Windows-only WebView2 process. The service and browser frontend are independent."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import urllib.request
from urllib.parse import parse_qsl, urlencode, urlsplit
import webbrowser

from .secret import protect
from .windows import Instance
from .windows_release import atomic_json, config, stable_entry
_open_browser = webbrowser.open


def owner(directory, cfg):
    value = json.loads(protect((Path(directory)/'windows-control.dpapi').read_bytes(), decrypt=True))
    parsed = urlsplit(value['origin'])
    if (value['pack_id'] != cfg['pack_id'] or parsed.scheme != 'http' or parsed.hostname != '127.0.0.1'
            or parsed.path or parsed.username or parsed.password or not parsed.port):
        raise ValueError('Invalid local management owner.')
    return value


def session_url(value):
    return value['origin'] + '/#session=' + value['token']


def request_owner(value, path, data=None):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *_args, **_kwargs):
            raise ValueError('Management redirects are not permitted.')
    if not path.startswith('/manage/') or path.startswith('//'):raise ValueError('Invalid management path.')
    request=urllib.request.Request(value['origin']+path,
        data=None if data is None else json.dumps(data).encode(),
        headers={'Authorization':'Bearer '+value['token'],'Content-Type':'application/json'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(request,timeout=15) as response:raw=response.read(16_000_001)
    if len(raw)>16_000_000:raise ValueError('Management response too large.')
    return raw


def local_page(url, origin):
    value, expected = urlsplit(url or ''), urlsplit(origin)
    return (value.scheme, value.netloc, value.path) == (expected.scheme, expected.netloc, '/') and not value.query


def runtime_available():
    import winreg
    for hive in (winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_32KEY,winreg.KEY_WOW64_64KEY):
            try:
                with winreg.OpenKey(hive,r'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
                                    0,winreg.KEY_READ|view) as key:
                    if winreg.QueryValueEx(key,'pv')[0] not in ('','0.0.0.0'):return True
            except OSError:pass
    return False


def clipboard_text(text):
    if not isinstance(text, str) or not 0 < len(text) <= 65536 or '\0' in text:
        raise ValueError('Invalid clipboard text.')
    user = ctypes.WinDLL('user32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GlobalAlloc.argtypes=[wintypes.UINT,ctypes.c_size_t];kernel.GlobalAlloc.restype=wintypes.HGLOBAL
    kernel.GlobalLock.argtypes=[wintypes.HGLOBAL];kernel.GlobalLock.restype=ctypes.c_void_p
    kernel.GlobalUnlock.argtypes=[wintypes.HGLOBAL]
    kernel.GlobalFree.argtypes=[wintypes.HGLOBAL]
    user.CreateWindowExW.argtypes=[wintypes.DWORD,wintypes.LPCWSTR,wintypes.LPCWSTR,wintypes.DWORD,
        ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.HWND,wintypes.HMENU,
        wintypes.HINSTANCE,ctypes.c_void_p]
    user.CreateWindowExW.restype=wintypes.HWND
    user.DestroyWindow.argtypes=[wintypes.HWND]
    user.OpenClipboard.argtypes=[wintypes.HWND]
    user.SetClipboardData.argtypes=[wintypes.UINT,wintypes.HANDLE];user.SetClipboardData.restype=wintypes.HANDLE
    raw=(text+'\0').encode('utf-16-le')
    # EmptyClipboard after OpenClipboard(NULL) leaves a NULL owner and makes
    # SetClipboardData fail. A message-only window belongs to this calling
    # thread, without borrowing another app's foreground window or UI input.
    window=user.CreateWindowExW(0,'STATIC','',0,0,0,0,0,wintypes.HWND(-3),None,None,None)
    if not window:raise OSError('Clipboard owner unavailable.')
    memory=None
    transferred=False
    try:
        memory=kernel.GlobalAlloc(2,len(raw))
        if not memory:raise OSError('Clipboard memory unavailable.')
        pointer=kernel.GlobalLock(memory)
        if not pointer:raise OSError('Clipboard memory unavailable.')
        ctypes.memmove(pointer,raw,len(raw));kernel.GlobalUnlock(memory)
        for _ in range(20):
            if user.OpenClipboard(window):break
            time.sleep(.025)
        else:raise OSError('Clipboard is busy.')
        try:
            if not user.EmptyClipboard() or not user.SetClipboardData(13,memory):raise OSError('Clipboard unavailable.')
            transferred=True
        finally:user.CloseClipboard()
    finally:
        if memory and not transferred:kernel.GlobalFree(memory)
        user.DestroyWindow(window)


class NativeApi:
    def __init__(self, value):
        self._owner = value
        self._window = None

    def _check(self):
        if not self._window or not local_page(self._window.get_current_url(), self._owner['origin']):
            raise ValueError('Only the local management page can use the Windows adapter.')

    def copy_text(self, text):
        self._check()
        clipboard_text(text)
        return {'ok':True}

    def export_logs(self, query):
        self._check()
        if not isinstance(query,str) or len(query)>1024:raise ValueError('Invalid filter.')
        items=parse_qsl(query,keep_blank_values=True)
        if any(k not in {'status','provider','key_id'} for k,v in items):raise ValueError('Invalid filter.')
        import webview
        paths=self._window.create_file_dialog(webview.FileDialog.SAVE,
            save_filename='bridge-request-metadata.csv',file_types=('CSV (*.csv)',))
        if not paths:return {'saved':False}
        # The filename comes only from the owner's native Save dialog, never JavaScript.
        raw=request_owner(self._owner,'/manage/export?'+urlencode(items))
        Path(paths[0]).write_bytes(raw)
        return {'saved':True}

    def open_browser(self):
        self._check()
        return {'opened':bool(_open_browser(session_url(self._owner)))}


def launch(directory, browser=False):
    args=[str(stable_entry()),'--console','--data-dir',str(directory)]
    if browser:args.append('--browser')
    process=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    def watch_exit():
        if process.wait()!=0:
            try:
                value=owner(directory,config())
                atomic_json(Path(directory)/'windows-console.json',{'mode':'browser','reason':'console_process_failed',
                    'version':config()['version'],'pid':process.pid})
                _open_browser(session_url(value))
            except (OSError,ValueError):pass
    threading.Thread(target=watch_exit,daemon=True,name='console-process-watch').start()
    return process.pid


def wait_for_exit(directory, timeout=20):
    """Wait for this profile's exact viewer process, not just its released event."""
    path=Path(directory)/'windows-console.json'
    if not path.is_file():return
    pid=json.loads(path.read_text()).get('pid')
    if type(pid) is not int or pid<=0:return
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD];kernel.WaitForSingleObject.restype=wintypes.DWORD
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    process=kernel.OpenProcess(0x101000,False,pid)
    if not process:
        if ctypes.get_last_error()==87:return  # Already exited.
        raise OSError('Cannot verify viewer exit.')
    try:
        image=ctypes.create_unicode_buffer(32768);size=wintypes.DWORD(len(image))
        if not kernel.QueryFullProcessImageNameW(process,0,image,ctypes.byref(size)):
            raise OSError('Cannot verify viewer identity.')
        if Path(image.value).resolve()!=Path(sys.executable).resolve().with_name('AIGO-LLM-Bridge.exe'):
            return  # A stale PID now belongs to another program; never touch it.
        if kernel.WaitForSingleObject(process,int(timeout*1000))!=0:
            raise OSError('Viewer did not exit; no process was terminated.')
    finally:kernel.CloseHandle(process)


def ensure_service(directory):
    cfg=config()
    try:
        value=owner(directory,cfg)
        request_owner(value,'/manage/state')
        return value
    except (OSError,ValueError):pass
    def start():
        return subprocess.Popen([str(stable_entry()),'--background','--data-dir',str(directory)],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    process = start()
    until=time.monotonic()+40
    while time.monotonic()<until:
        try:
            value=owner(directory,cfg)
            request_owner(value,'/manage/state')
            return value
        except (OSError,ValueError):
            code = process.poll()
            from .windows_instance import BUSY_EXIT, BUSY_MESSAGE, RuntimeBusyError
            if code == BUSY_EXIT:
                raise RuntimeBusyError(BUSY_MESSAGE)
            if code == 0:
                # The previous service may have deleted its owner file but still
                # hold the profile instance lock while shutting down. A second
                # launch then exits cleanly without becoming the new service.
                instance = Instance(directory)
                available = instance.primary
                instance.close()
                if available:
                    process = start()
            elif code is not None:
                raise ValueError('The background service could not start.') from None
            time.sleep(.2)
    raise ValueError('The background service did not become ready.')


def run(directory, browser=False, probe=False, hidden=False):
    directory=Path(directory)
    cfg=config();value=owner(directory,cfg)
    if (probe or hidden) and not cfg['local_probe']:raise ValueError('Acceptance options require an isolated LocalProbe build.')
    status=directory/'windows-console.json'
    def record(mode, **extra):
        atomic_json(status,{'mode':mode,'pid':os.getpid(),'version':cfg['version'],**extra})
    if browser:
        _open_browser(session_url(value));record('browser');return 0
    instance=Instance(directory/'console')
    if not instance.primary:
        instance.notify();instance.close();return 0
    stopped=threading.Event();window=None;watcher=None
    try:
        if not runtime_available():raise ValueError('WebView2 runtime not installed.')
        import logging
        logging.getLogger('pywebview').disabled=True
        import webview
        webview.settings['ALLOW_FILE_URLS']=False
        webview.settings['ALLOW_DOWNLOADS']=False
        webview.settings['REMOTE_DEBUGGING_PORT']=None
        webview.settings['OPEN_DEVTOOLS_IN_DEBUG']=False
        api=NativeApi(value)
        window=webview.create_window('Local Token Buffet Bridge — Windows', session_url(value),js_api=api,
            width=1200,height=820,min_size=(820,600),text_select=True,hidden=(probe or hidden))
        api._window=window
        def before_show():
            # Force WebView2 and deny navigation out of the management origin.
            def navigation(_sender,event):
                if not local_page(str(event.Uri),value['origin']):event.Cancel=True
            window.native.webview.NavigationStarting += navigation
        window.events.before_show += before_show
        ready=threading.Event()
        def loaded():
            ready.set();record('webview2',ready=True)
        window.events.loaded += loaded
        window.events.closed += stopped.set
        def watch():
            while not stopped.wait(.4):
                try:
                    current=owner(directory,cfg)
                    if current!=value:raise ValueError()
                except (OSError,ValueError):
                    window.destroy();break
                if instance.requested():window.restore();window.show()
        watcher=threading.Thread(target=watch,daemon=True,name='console-owner-watch')
        watcher.start()
        if probe:
            from .windows_console_probe import acceptance
            callback=lambda: acceptance(window,api,directory,value)
        else:callback=None
        webview.start(func=callback,gui='edgechromium',private_mode=True,debug=False)
        if not ready.is_set():raise ValueError('WebView2 did not load.')
        record('closed')
        if probe:
            result=json.loads((directory/'windows-console-probe.json').read_text())
            if not result['success']:return 2
        return 0
    except Exception:
        # No exception text, URLs, credentials or JS values are persisted.
        if probe:
            record('probe_failed');return 2
        record('browser',reason='webview2_unavailable')
        _open_browser(session_url(value))
        return 0
    finally:
        stopped.set()
        if watcher:watcher.join(timeout=2)
        instance.close()
