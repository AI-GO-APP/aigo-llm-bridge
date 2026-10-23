"""Separate Cocoa/WKWebView viewer; closing it leaves the LaunchAgent serving."""
import json
from pathlib import Path
import subprocess
import sys
import threading
import urllib.request
from urllib.parse import parse_qsl, urlencode, urlsplit

from .connection_test import NoRedirect
from .windows import Instance


def local_page(url, origin):
    if not isinstance(url, str):
        return False
    parsed = urlsplit(url)
    return parsed.scheme == 'http' and parsed.netloc == urlsplit(origin).netloc and parsed.path == '/' and not parsed.query


def request_owner(owner, path):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(owner['origin'] + path, headers={'Authorization': 'Bearer ' + owner['token']})
    with opener.open(request, timeout=5) as response:
        return response.read(4_000_001)


class NativeApi:
    def __init__(self, owner):
        self._owner, self._window = owner, None

    def _check(self):
        if not self._window or not local_page(self._window.get_current_url(), self._owner['origin']):
            raise ValueError('Native access is limited to the bound local console.')

    def copy_text(self, text):
        self._check()
        if not isinstance(text, str) or not 0 < len(text) <= 65536 or '\0' in text:
            raise ValueError('Invalid clipboard text.')
        # pbcopy accepts the secret over stdin, without a file or shell interpolation.
        result = subprocess.run(['/usr/bin/pbcopy'], input=text.encode(), capture_output=True, timeout=5)
        if result.returncode:
            raise OSError('Clipboard is unavailable.')
        return {'ok': True}

    def export_logs(self, query):
        self._check()
        if not isinstance(query, str) or len(query) > 1024:
            raise ValueError('Invalid filter.')
        items = parse_qsl(query, keep_blank_values=True)
        if any(k not in {'status', 'provider', 'key_id'} for k, _ in items):
            raise ValueError('Invalid filter.')
        import webview
        paths = self._window.create_file_dialog(webview.FileDialog.SAVE,
            save_filename='bridge-request-metadata.csv', file_types=('CSV (*.csv)',))
        if not paths:
            return {'saved': False}
        selected = paths if isinstance(paths, str) else paths[0]
        Path(selected).write_bytes(request_owner(self._owner, '/manage/export?' + urlencode(items)))
        return {'saved': True}

    def open_browser(self):
        self._check()
        import webbrowser
        return {'opened': bool(webbrowser.open(self._owner['origin'] + '/#session=' + self._owner['token']))}


def run(owner, probe=None):
    if sys.platform != 'darwin' or not local_page(owner['origin'] + '/', owner['origin']) or urlsplit(owner['origin']).hostname != '127.0.0.1':
        raise ValueError('Invalid Mac management origin.')
    instance = Instance(Path(owner['directory']) / 'console')
    if not instance.primary:
        instance.notify(); instance.close()
        return 0
    stopped = threading.Event()
    url = owner['origin'] + '/#session=' + owner['token']
    try:
        import logging
        logging.getLogger('pywebview').disabled = True
        import webview
        import webview.util
        original_loader = webview.util.load_js_files
        def csp_loader(target, platform):
            code, finish = original_loader(target, platform)
            if platform == 'cocoa':
                finish = (Path(__file__).parent / 'web/macos-native.js').read_text() + '\n' + finish
            return code, finish
        webview.util.load_js_files = csp_loader
        webview.settings['ALLOW_FILE_URLS'] = False
        webview.settings['ALLOW_DOWNLOADS'] = False
        webview.settings['OPEN_DEVTOOLS_IN_DEBUG'] = False
        api = NativeApi(owner)
        window = webview.create_window('LLM Bridge — macOS', url, js_api=api,
            width=1200, height=820, min_size=(420, 560), text_select=True)
        # pywebview's callback dispatcher normally wraps trusted native scripts in
        # JavaScript eval(), which our CSP rejects. Cocoa can run them directly.
        window.evaluate_js = window.run_js
        api._window = window
        def bind_navigation():
            from webview.platforms.cocoa import BrowserView
            class BoundMacNavigationDelegate(BrowserView.BrowserDelegate):
                def webView_decidePolicyForNavigationAction_decisionHandler_(self, view, action, handler):
                    requested = str(action.request().URL().absoluteString())
                    handler(1 if local_page(requested, owner['origin']) else 0)
            native = BrowserView.instances[window.uid]
            native._bridge_navigation = BoundMacNavigationDelegate.alloc().init()
            native.webview.setNavigationDelegate_(native._bridge_navigation)
        window.events.before_show += bind_navigation
        def loading():
            current = window.get_current_url()
            if current and not local_page(current, owner['origin']):
                window.destroy()
        window.events.loaded += loading
        window.events.closed += stopped.set
        def watch():
            while not stopped.wait(.5):
                try:
                    request_owner(owner, '/manage/state')
                except Exception:
                    window.destroy(); break
                if instance.requested():
                    window.restore(); window.show()
        threading.Thread(target=watch, daemon=True, name='mac-console-owner-watch').start()
        webview.start(func=(lambda: probe(window, api)) if probe else None, gui='cocoa', private_mode=True, debug=False)
        webview.util.load_js_files = original_loader
        return 0
    except Exception:
        if probe:
            raise
        import webbrowser
        webbrowser.open(url)
        return 0
    finally:
        stopped.set()
        instance.close()


if __name__ == '__main__':
    try:
        raise SystemExit(run(json.loads(sys.stdin.buffer.read(65537))))
    except (ValueError, OSError, KeyError):
        raise SystemExit(1)
