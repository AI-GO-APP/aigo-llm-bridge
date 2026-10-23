"""Isolated real WKWebView renderer probe. Synthetic metadata, no OAuth or OS power writes."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def wait_js(window, expression, timeout=20):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        try:
            if window.run_js(expression):
                return
        except Exception:
            pass  # WKWebView can evaluate while classic scripts are still initializing.
        time.sleep(.1)
    raise ValueError('Renderer did not become ready.')


def snapshot(window, path):
    from PyObjCTools import AppHelper
    from AppKit import NSBitmapImageRep, NSPNGFileType
    from webview.platforms.cocoa import BrowserView
    event = threading.Event()
    outcome = []
    def capture():
        def completed(image, error):
            try:
                if image is None or error:
                    return
                bitmap = NSBitmapImageRep.imageRepWithData_(image.TIFFRepresentation())
                data = bitmap.representationUsingType_properties_(NSPNGFileType, {})
                outcome.append(bool(data.writeToFile_atomically_(str(path), True)))
            finally:
                event.set()
        BrowserView.instances[window.uid].webview.takeSnapshotWithConfiguration_completionHandler_(None, completed)
    AppHelper.callAfter(capture)
    if not event.wait(20) or outcome != [True]:
        raise ValueError('Native snapshot failed.')


def native_dialog_export(native, directory, save):
    """Drive only this process's real NSSavePanel, including the real cancel path."""
    from PyObjCTools import AppHelper
    from AppKit import NSApp, NSSavePanel
    from Foundation import NSURL
    finished = threading.Event()
    selected = threading.Event()
    def choose():
        if selected.is_set() or finished.is_set():
            return
        panel = NSApp.modalWindow()
        if panel and panel.isKindOfClass_(NSSavePanel):
            if save:
                panel.setDirectoryURL_(NSURL.fileURLWithPath_(str(directory)))
                panel.setNameFieldStringValue_('原生測試-metadata.csv')
                # Return the real panel's chosen URL without invoking a second
                # overwrite/permission dialog in this unattended synthetic probe.
                panel.orderOut_(None)
                NSApp.stopModalWithCode_(1)
            else:
                panel.cancel_(None)
            selected.set()
    def drive():
        until = time.monotonic() + 15
        while not finished.wait(.1) and not selected.is_set():
            if time.monotonic() >= until:
                AppHelper.callAfter(NSApp.abortModal)
                return
            AppHelper.callAfter(choose)
    threading.Thread(target=drive, daemon=True).start()
    try:
        value = native.export_logs('')
        print(json.dumps({'stage': 'native_save_panel', 'save': save, 'selected': selected.is_set(), 'result': value}), flush=True)
        time.sleep(.5)
        return selected.is_set() and value == {'saved': save}
    finally:
        finished.set()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if sys.platform != 'darwin':
        parser.error('Requires macOS Cocoa/WKWebView.')
    output = Path(args.output).resolve(); output.mkdir(parents=True, exist_ok=True)
    from desktop_bridge.store import Store
    from desktop_bridge.service import Runtime, ApiServer
    from desktop_bridge.macos_management import MacManagementServer
    from desktop_bridge import providers, secret
    from desktop_bridge import macos_console
    from desktop_bridge import windows_onboarding as shared_onboarding
    # These patches are confined to this isolated synthetic process.
    providers.status = lambda *_: {'ready': True}
    secret.load = lambda *_args, **_kwargs: ''
    shared_onboarding.cloud_accounts = lambda *_: []
    results = {'screens': [], 'success': False}
    with tempfile.TemporaryDirectory(prefix='bridge-mac-console-') as tmp:
        store = Store(tmp)
        runtime = Runtime(store)
        api = ApiServer(runtime, port=0); api.start()
        manager = MacManagementServer(store, runtime, api, preview=True)
        manager.start()
        store.insert_request({'id': 'synthetic-render', 'model': store.get('models')[1]['id'], 'provider': 'codex',
            'status': 'completed', 'http_status': 200, 'created_ts': time.time(), 'finished_ts': time.time(),
            'duration_ms': 1200, 'prompt_tokens': 17, 'completion_tokens': 9, 'cost_usd': .012345})
        def probe(window, native):
            clipboard = None
            try:
                wait_js(window, 'typeof state !== "undefined" && !!state && !!document.querySelector("#macos-onboarding")')
                wait_js(window, 'window.BridgePlatform?.name === "macos-wkwebview"')
                time.sleep(.6)
                # Capture the actual first-run dialog; defer is an explicit product action.
                wait_js(window, 'document.querySelector("#macos-onboarding").open')
                snapshot(window, output / 'macos-onboarding-light.png')
                window.run_js('document.querySelector("#ob-defer").click()')
                for theme in ('light', 'dark'):
                    # Force theme media rules for deterministic renderer evidence.
                    window.run_js('''(() => {
                      if (!window.__probeThemeRules) {
                        window.__probeThemeRules = [];
                        for (const sheet of document.styleSheets) for (const rule of sheet.cssRules)
                          if (rule.conditionText?.includes('prefers-color-scheme')) window.__probeThemeRules.push(rule);
                      }
                      for (const rule of window.__probeThemeRules) rule.media.mediaText = '(min-width: ''' + ('0' if theme == 'dark' else '99999') + '''px)';
                    })()''')
                    background = window.run_js('getComputedStyle(document.documentElement).getPropertyValue("--page").trim()')
                    if background != ('#050506' if theme == 'dark' else '#f9f9f7'):
                        raise ValueError('Theme did not change: ' + theme)
                    for width in (1200, 480):
                        window.resize(width, 820)
                        time.sleep(.3)
                        for page in ('overview', 'integration', 'keys', 'logs', 'models', 'settings'):
                            window.run_js('navigate(' + json.dumps(page) + '); window.scrollTo(0,0); document.querySelector("#main").scrollTop=0')
                            window.run_js('document.querySelector("#toast").hidden=true')
                            time.sleep(.15)
                            dimensions = json.loads(window.run_js('JSON.stringify({width:innerWidth, scroll:document.documentElement.scrollWidth})'))
                            if dimensions['scroll'] > dimensions['width'] + 1:
                                raise ValueError('Whole-page horizontal overflow: ' + page)
                            name = f'macos-{page}-{theme}-{width}.png'
                            snapshot(window, output / name)
                            results['screens'].append(name)
                        window.run_js('navigate("settings"); document.querySelector(".macos-update-card").scrollIntoView({block:"center"})')
                        name = f'macos-platform-card-{theme}-{width}.png'
                        snapshot(window, output / name)
                        results['screens'].append(name)
                        for panel in range(5):
                            window.run_js('document.querySelector("#macos-onboarding").showModal(); document.querySelector(\'[data-ob-step="' + str(panel) + '"]\').click()')
                            name = f'macos-onboarding-{panel + 1}-{theme}-{width}.png'
                            snapshot(window, output / name)
                            results['screens'].append(name)
                        window.run_js('document.querySelector("#ob-defer").click()')
                # Keep personal clipboard only in memory and restore it after the native round-trip.
                clipboard = subprocess.run(['/usr/bin/pbpaste'], capture_output=True, timeout=5).stdout
                window.run_js('window.__probeCopy=false; window.BridgePlatform.copyText("BRIDGE_NATIVE_COPY_測試").then(()=>window.__probeCopy=true)')
                wait_js(window, 'window.__probeCopy === true')
                copied = subprocess.run(['/usr/bin/pbpaste'], capture_output=True, timeout=5).stdout
                results['native_clipboard'] = copied.decode() == 'BRIDGE_NATIVE_COPY_測試'
                subprocess.run(['/usr/bin/pbcopy'], input=clipboard, timeout=5)
                clipboard = None  # Restore before opening any modal dialog.
                # Exercise the real CSV adapter with deterministic chooser return and cancel.
                chooser = window.create_file_dialog
                window.create_file_dialog = lambda *_a, **_kw: None
                results['cancelled_export'] = native.export_logs('') == {'saved': False}
                destination = output / 'synthetic-metadata.csv'
                window.create_file_dialog = lambda *_a, **_kw: [str(destination)]
                results['csv_export'] = native.export_logs('')['saved'] and '0.012345' in destination.read_text(encoding='utf-8-sig')
                window.create_file_dialog = chooser
                results['real_save_panel_cancel'] = native_dialog_export(native, output, False)
                results['real_save_panel_save'] = native_dialog_export(native, output, True)
                window.run_js('document.querySelector("#macos-open-onboarding").click()')
                window.run_js('document.querySelector("#ob-key").value="SYNTHETIC_KEY_ONLY"; document.querySelector("#ob-defer").click()')
                results['key_cleared_on_close'] = window.run_js('document.querySelector("#ob-key").value === ""')
                # External navigation must be rejected before loading another origin.
                window.run_js('location.href="https://example.invalid/"')
                time.sleep(.3)
                results['navigation_bound'] = macos_console.local_page(window.get_current_url(), manager.origin)
                results['success'] = all(results.get(k) for k in ('native_clipboard', 'cancelled_export', 'csv_export', 'real_save_panel_cancel', 'real_save_panel_save', 'key_cleared_on_close', 'navigation_bound'))
            except Exception as error:
                results['error_type'] = type(error).__name__
                # This probe contains synthetic content only; keep diagnostic stage local.
                results['diagnostic'] = str(error)[:2000]
                try:
                    results['renderer'] = window.run_js('JSON.stringify({ready:document.readyState,stateType:typeof state,wizard:!!document.querySelector("#macos-onboarding"),adapter:window.BridgePlatform?.name,bridge:typeof window.pywebview,functions:Object.keys(window.pywebview?.api||{}),createApi:window.pywebview?._createApi.toString().slice(0,120)})')
                except Exception as diagnostic:
                    results['renderer_error'] = str(diagnostic)[:1000]
                results['success'] = False
            finally:
                if clipboard is not None:
                    subprocess.run(['/usr/bin/pbcopy'], input=clipboard, timeout=5)
                window.destroy()
        try:
            macos_console.run({'origin': manager.origin, 'token': manager.token, 'directory': tmp}, probe=probe)
            import urllib.request
            with urllib.request.urlopen(f'http://127.0.0.1:{api.port}/health', timeout=5) as response:
                results['service_after_viewer_close'] = response.status == 200
            results['success'] = results['success'] and results['service_after_viewer_close']
        finally:
            manager.stop(); runtime.stop(); api.stop(); store.close()
    (output / 'result.json').write_text(json.dumps(results, indent=2))
    print(json.dumps({k: v for k, v in results.items() if k != 'screens'}))
    return 0 if results['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
