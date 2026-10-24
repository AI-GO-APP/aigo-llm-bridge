import pytest
from desktop_bridge.windows_console import local_page, NativeApi, clipboard_text


def test_other_profile_machine_rejection_does_not_spawn_retry_loop(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from desktop_bridge import windows_console as console
    from desktop_bridge.windows_instance import BUSY_EXIT, RuntimeBusyError
    launches = []
    monkeypatch.setattr(console, 'config', lambda: {})
    monkeypatch.setattr(console, 'owner', lambda *_: (_ for _ in ()).throw(FileNotFoundError()))
    monkeypatch.setattr(console, 'stable_entry', lambda: 'synthetic.exe')
    monkeypatch.setattr(console.subprocess, 'Popen', lambda *a, **k: (launches.append(a), SimpleNamespace(poll=lambda: BUSY_EXIT))[1])
    with pytest.raises(RuntimeBusyError): console.ensure_service(tmp_path)
    assert len(launches) == 1 and not list(tmp_path.iterdir())


@pytest.mark.parametrize('url',['https://127.0.0.1:8000/','http://localhost:8000/',
    'http://127.0.0.1:8001/','file:///local','http://127.0.0.1:8000/other',
    'http://127.0.0.1:8000/?next=external','http://evil.example/'])
def test_native_privileges_do_not_follow_external_navigation(url):
    from types import SimpleNamespace
    api=NativeApi({'origin':'http://127.0.0.1:8000'})
    api._window=SimpleNamespace(get_current_url=lambda:url)
    with pytest.raises(ValueError):api.copy_text('synthetic')
    with pytest.raises(ValueError):api.export_logs('status=completed')
    with pytest.raises(ValueError):api.open_browser()


def test_only_the_bound_local_console_has_native_access():
    assert local_page('http://127.0.0.1:8000/#keys','http://127.0.0.1:8000')
    assert not local_page(None,'http://127.0.0.1:8000')


@pytest.mark.parametrize('value',['',None,'secret\0tail','x'*65537],ids=['empty','null','embedded-null','oversize'])
def test_clipboard_rejects_invalid_inputs_before_touching_os(value):
    with pytest.raises(ValueError):clipboard_text(value)


@pytest.mark.parametrize('failure',[None,'allocate','write'])
def test_clipboard_uses_owned_window_and_releases_only_untransferred_memory(monkeypatch,failure):
    import ctypes
    from types import SimpleNamespace
    from desktop_bridge import windows_console as console
    calls=[];buffer=ctypes.create_string_buffer(1024)
    class Function:
        def __init__(self,name,fn):self.name,self.fn=name,fn
        def __call__(self,*args):calls.append((self.name,args));return self.fn(*args)
    def function(name,fn=lambda *_:1):return Function(name,fn)
    user=SimpleNamespace(CreateWindowExW=function('create',lambda *_:12345),
        DestroyWindow=function('destroy'),OpenClipboard=function('open'),
        EmptyClipboard=function('empty'),CloseClipboard=function('close'),
        SetClipboardData=function('write',lambda *_:0 if failure=='write' else 99))
    kernel=SimpleNamespace(GlobalAlloc=function('allocate',lambda *_:0 if failure=='allocate' else 99),
        GlobalLock=function('lock',lambda *_:ctypes.addressof(buffer)),GlobalUnlock=function('unlock'),
        GlobalFree=function('free'))
    monkeypatch.setattr(console.ctypes,'WinDLL',lambda name,**_:user if name=='user32' else kernel,raising=False)
    if failure:
        with pytest.raises(OSError):clipboard_text('synthetic 中文')
    else:
        clipboard_text('synthetic 中文')
        assert buffer.raw[:len('synthetic 中文\0'.encode('utf-16-le'))]=='synthetic 中文\0'.encode('utf-16-le')
    assert calls[-1]==('destroy',(12345,))
    if failure!='allocate':
        assert ('open',(12345,)) in calls and any(name=='close' for name,_ in calls)
    assert any(name=='free' for name,_ in calls)==(failure=='write')


def test_missing_runtime_uses_owner_browser_session_without_desktop_input(tmp_path,monkeypatch):
    import json
    from types import SimpleNamespace
    from desktop_bridge import windows_console as console
    opened=[]
    monkeypatch.setattr(console,'config',lambda:{'version':'test','local_probe':False})
    monkeypatch.setattr(console,'owner',lambda *_:{'origin':'http://127.0.0.1:8000','token':'synthetic'})
    monkeypatch.setattr(console,'Instance',lambda *_:SimpleNamespace(primary=True,close=lambda:None))
    monkeypatch.setattr(console,'runtime_available',lambda:False)
    monkeypatch.setattr(console,'_open_browser',lambda url:opened.append(url))
    assert console.run(tmp_path)==0
    assert opened==['http://127.0.0.1:8000/#session=synthetic']
    receipt=json.loads((tmp_path/'windows-console.json').read_text())
    assert receipt['mode']=='browser' and receipt['reason']=='webview2_unavailable'
    assert 'synthetic' not in json.dumps(receipt)


def test_native_export_cancel_does_not_fetch_or_write(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from desktop_bridge import windows_console as console
    monkeypatch.setattr(console,'request_owner',lambda *_:pytest.fail('Cancelled save must not fetch logs'))
    api=NativeApi({'origin':'http://127.0.0.1:8000'})
    api._window=SimpleNamespace(get_current_url=lambda:'http://127.0.0.1:8000/',create_file_dialog=lambda *_a,**_k:None)
    assert api.export_logs('provider=codex')=={'saved':False}
    with pytest.raises(ValueError):api.export_logs('destination=external')


def test_quick_restart_retries_clean_instance_handoff_without_terminating_old_service(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from desktop_bridge import windows_console as console
    launches=[]
    monkeypatch.setattr(console,'config',lambda:{'pack_id':'synthetic'})
    monkeypatch.setattr(console,'stable_entry',lambda:'synthetic.exe')
    monkeypatch.setattr(console.time,'sleep',lambda *_:None)
    availability=iter([False,False,True])
    monkeypatch.setattr(console,'Instance',lambda *_:SimpleNamespace(primary=next(availability),close=lambda:None))
    def owner(*_):
        if len(launches)<2:raise OSError('old owner removed while old instance still holds lock')
        return {'origin':'http://127.0.0.1:12345','token':'synthetic'}
    def launch(args,**_kwargs):
        launches.append(args)
        return SimpleNamespace(poll=lambda:0)
    monkeypatch.setattr(console,'owner',owner)
    monkeypatch.setattr(console,'request_owner',lambda *_:b'{}')
    monkeypatch.setattr(console.subprocess,'Popen',launch)
    assert console.ensure_service(tmp_path)['token']=='synthetic'
    assert len(launches)==2 and launches[0]==launches[1]
    assert launches[0][1:]==['--background','--data-dir',str(tmp_path)]


def test_failed_service_is_not_repeatedly_restarted(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from desktop_bridge import windows_console as console
    launches=[]
    monkeypatch.setattr(console,'config',lambda:{'pack_id':'synthetic'})
    monkeypatch.setattr(console,'stable_entry',lambda:'synthetic.exe')
    monkeypatch.setattr(console,'owner',lambda *_:(_ for _ in ()).throw(OSError('unavailable')))
    def launch(args,**_kwargs):
        launches.append(args)
        return SimpleNamespace(poll=lambda:2)
    monkeypatch.setattr(console.subprocess,'Popen',launch)
    with pytest.raises(ValueError):console.ensure_service(tmp_path)
    assert len(launches)==1
