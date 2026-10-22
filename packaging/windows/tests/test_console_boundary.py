import pytest
from desktop_bridge.windows_console import local_page, NativeApi, clipboard_text


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
