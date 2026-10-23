"""Fixed, hidden-renderer acceptance for non-distributable LocalProbe builds only."""
import csv
import ctypes
from ctypes import wintypes
import io
import json
from pathlib import Path
import time
import urllib.request

from .store import LOG_COLUMNS
from .windows_release import atomic_json
from .windows_console import request_owner, clipboard_text


def read_clipboard():
    user=ctypes.WinDLL('user32');kernel=ctypes.WinDLL('kernel32')
    user.GetClipboardData.argtypes=[wintypes.UINT];user.GetClipboardData.restype=wintypes.HANDLE
    kernel.GlobalLock.argtypes=[wintypes.HGLOBAL];kernel.GlobalLock.restype=ctypes.c_void_p
    kernel.GlobalUnlock.argtypes=[wintypes.HGLOBAL]
    if not user.OpenClipboard(None):return None
    try:
        handle=user.GetClipboardData(13)
        if not handle:return None
        pointer=kernel.GlobalLock(handle)
        try:return ctypes.wstring_at(pointer) if pointer else None
        finally:
            if pointer:kernel.GlobalUnlock(handle)
    finally:user.CloseClipboard()


def acceptance(window,api,directory,value):
    checks={};stage='renderer_ready';created=None;success=False
    def progress(name):
        atomic_json(Path(directory)/'windows-console-progress.json',{'stage':name})
    def wait(predicate):
        until=time.monotonic()+30
        while time.monotonic()<until:
            try:
                if predicate():return
            except Exception:pass
            time.sleep(.1)
        raise RuntimeError('Acceptance step timed out.')
    try:
        progress(stage)
        wait(lambda:window.evaluate_js("Boolean(window.BridgePlatform?.native && typeof showToken==='function')"))
        checks['actual_webview2_adapter_ready']=True
        stage='onboarding_renderer'
        progress(stage)
        wait(lambda:window.evaluate_js("Boolean(document.querySelector('#windows-onboarding') && state?.windows_onboarding)"))
        wait(lambda:window.evaluate_js("document.querySelector('#windows-onboarding').open === state.windows_onboarding.required"))
        checks['onboarding_first_launch_or_daily_bypass']=True
        checks['onboarding_five_steps_rendered']=bool(window.evaluate_js("document.querySelectorAll('[data-ob-panel]').length === 5"))
        checks['onboarding_consent_defaults_off']=bool(window.evaluate_js("!document.querySelector('#ob-power-consent').checked && !document.querySelector('#ob-deploy-consent').checked"))
        # Close the test renderer's modal only; no completion flag/power/Cloud mutation.
        window.evaluate_js("document.querySelector('#windows-onboarding').close();")
        stage='default_key'
        progress(stage)
        checks['frontend_new_key_all_checked']=bool(window.evaluate_js('createKey(); document.querySelector("#key-form input[name=claude]").checked && document.querySelector("#key-form input[name=codex]").checked;'))
        window.evaluate_js('closeModal();')
        created=json.loads(request_owner(value,'/manage/keys/create',{'label':'WebView renderer acceptance'}))
        state=json.loads(request_owner(value,'/manage/state'))
        row=next(k for k in state['keys'] if k['id']==created['id'])
        checks['default_key_all_providers']=json.loads(row['providers'])==['claude','codex']
        stage='native_key_copy'
        progress(stage)
        # A fixed application test invokes the real frontend event and native clipboard API.
        window.evaluate_js('showToken('+json.dumps(created['token'])+'); document.getElementById("new-token").type="password";')
        progress('native_key_click')
        window.evaluate_js('document.getElementById("copy-token").click(); void(0);')
        progress('native_key_read')
        wait(lambda:read_clipboard()==created['token'])
        checks['actual_frontend_key_copy_exact']=True
        stage='same_key_http'
        progress(stage)
        port=state['local_port']
        request=urllib.request.Request(f'http://127.0.0.1:{port}/api/v1/models',
            headers={'Authorization':'Bearer '+created['token']})
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request,timeout=25) as response:models=json.load(response)
        # A disposable runner has no subscription CLIs. Empty availability is
        # valid; successful authentication and the stored scope are separate.
        checks['copied_key_authenticates']=models['object']=='list' and isinstance(models['data'],list)
        stage='native_csv_export'
        progress(stage)
        output=Path(directory)/'webview-acceptance-metadata.csv'
        output.unlink(missing_ok=True)
        # CLI acceptance supplies a Save-dialog result; no desktop input or dialog focus.
        # The remaining frontend, native bridge, authenticated GET and write are real.
        window.create_file_dialog=lambda *_args,**_kwargs:(str(output),)
        window.evaluate_js('closeModal(); navigate("logs"); document.getElementById("export").click();')
        wait(output.is_file)
        reader=csv.DictReader(io.StringIO(output.read_text(encoding='utf-8-sig')))
        rows=list(reader)
        checks['native_csv_exact_metadata_columns']=tuple(reader.fieldnames)==LOG_COLUMNS
        checks['native_csv_contains_synthetic_row']=any(r['model']=='synthetic' and r['prompt_tokens']=='17' for r in rows)
        checks['csv_does_not_contain_key']=created['token'] not in output.read_text(encoding='utf-8-sig')
        checks['csv_save_selection_supplied_by_test']=True
        stage='browser_adapter'
        progress(stage)
        # Exercise the same common frontend using the browser adapter, without opening a browser.
        window.evaluate_js('window.__nativeAdapter=window.BridgePlatform;')
        platform=(Path(__file__).parent/'web/platform.js').read_text(encoding='utf-8')
        window.evaluate_js(platform)
        checks['browser_frontend_remains_available']=window.evaluate_js('window.BridgePlatform.name')=='browser'
        window.evaluate_js('window.BridgePlatform=window.__nativeAdapter; delete window.__nativeAdapter;')
        stage='metadata_only_profile'
        progress(stage)
        checks['key_not_stored_plaintext']=all(created['token'].encode() not in p.read_bytes()
            for p in Path(directory).rglob('*') if p.is_file() and p.suffix not in {'.lock','.tmp'})
        assert all(checks.values())
        success=True
    except Exception as error:
        failure_type=type(error).__name__
    finally:
        if created:
            try:request_owner(value,'/manage/keys/revoke',{'id':created['id']})
            except Exception:success=False
        clipboard_text('LLM Bridge acceptance completed')
        atomic_json(Path(directory)/'windows-console-probe.json',{'success':success,'checks':checks,
            'stage':'complete' if success else stage,'desktop_input_used':False,'native_save_dialog_clicked':False,
            'failure_type':locals().get('failure_type')})
        window.destroy()
