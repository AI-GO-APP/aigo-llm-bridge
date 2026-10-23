"""Mac adapters exercise isolation, consent, recovery and the shared setup proof."""
import copy
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from desktop_bridge.macos_power import PowerPolicy, parse_settings
from desktop_bridge.macos_onboarding import Onboarding
from desktop_bridge.store import Store


class FakePower:
    def __init__(self, sleep=20):
        self.values = {'AC Power': {'sleep': sleep, 'displaysleep': 10, 'hibernatemode': 3},
                       'Battery Power': {'sleep': 5, 'displaysleep': 2, 'hibernatemode': 3}}
        self.writes = []
        self.denied = False

    def read(self):
        return copy.deepcopy(self.values)

    def write(self, minutes, admin=False):
        if self.denied:
            raise PermissionError(13, 'synthetic cancelled authorization')
        self.writes.append((minutes, admin))
        self.values['AC Power']['sleep'] = minutes


def test_ac_only_consent_backup_restore_and_owner_changes(tmp_path):
    native = FakePower()
    before = native.read()
    policy = PowerPolicy(tmp_path, native)
    with pytest.raises(ValueError): policy.apply()
    assert not native.writes and not policy.path.exists()
    assert policy.apply(consent=True, admin=True)['verified']
    assert policy.load()['original_sleep'] == 20
    expected = copy.deepcopy(before); expected['AC Power']['sleep'] = 0
    assert native.read() == expected and native.writes == [(0, True)]
    assert PowerPolicy(tmp_path, native).inspect()['verified']
    assert policy.apply(consent=True)['verified'] and len(native.writes) == 1
    policy.restore(admin=True)
    assert native.read() == before and not policy.inspect()['enabled']
    policy.apply(consent=True)
    native.values['AC Power']['sleep'] = 37
    with pytest.raises(ValueError): policy.restore(admin=True)
    assert native.values['AC Power']['sleep'] == 37


def test_denied_admin_and_pending_recovery_never_lose_original(tmp_path):
    native = FakePower(); native.denied = True
    policy = PowerPolicy(tmp_path, native)
    with pytest.raises(PermissionError): policy.apply(consent=True, admin=True)
    assert not policy.inspect()['verified'] and policy.load()['original_sleep'] == 20
    native.denied = False
    native.values['AC Power']['sleep'] = 0  # A crash just after the OS write.
    policy.apply(consent=True)
    policy.restore()
    assert native.values['AC Power']['sleep'] == 20


def test_preconfigured_ac_sleep_needs_no_privilege_or_setting_change(tmp_path):
    native = FakePower(sleep=0); before = native.read()
    policy = PowerPolicy(tmp_path, native)
    assert policy.inspect()['verified'] and not policy.path.exists()
    policy.apply(consent=True); policy.restore()
    assert native.read() == before and not native.writes


def test_pmset_parser_does_not_confuse_battery_and_ac():
    settings = parse_settings('Battery Power:\n sleep 5\n displaysleep 2\nAC Power:\n sleep 0\n displaysleep 10\n')
    assert settings['AC Power']['sleep'] == 0 and settings['Battery Power']['sleep'] == 5
    with pytest.raises(ValueError): parse_settings('Battery Power:\n sleep 0\n')


@pytest.fixture
def wizard(tmp_path):
    store = Store(tmp_path, startup=False)
    owner = SimpleNamespace(store=store, release={'version': '0.8.0-mac.1', 'pack_id': 'macos-source'},
                            auth_checking=False, relay=None)
    yield Onboarding(owner, PowerPolicy(tmp_path, FakePower()))
    store.close()


def wait_job(wizard):
    assert wizard.busy.acquire(timeout=5)
    wizard.busy.release()


def test_mac_setup_retains_key_proof_consent_and_completion_across_update(wizard, monkeypatch):
    from desktop_bridge import windows_onboarding as shared
    monkeypatch.setattr(shared.providers, 'status', lambda *_: {'ready': True})
    monkeypatch.setattr(shared, 'verify', lambda *_: {'success': True, 'http_status': 200, 'cost_usd': .01, 'code': 'ok'})
    wizard.store.set('public_url', 'https://synthetic.workers.dev')
    kid, key = wizard.store.create_key('existing owner key')
    device = wizard.store.get('device_id')
    model = wizard.store.get('models')[1]['id']
    wizard.action('verify', {'key': key, 'model': model}); wait_job(wizard)
    finish = {'key_saved': True, 'handoff_copied': True, 'model': model}
    with pytest.raises(ValueError): wizard.action('finish', finish)
    wizard.action('power', {'consent': True}); wait_job(wizard)
    wizard.action('finish', finish)
    assert not wizard.state()['required']
    wizard.owner.release['version'] = '0.8.0-mac.2'
    second = Onboarding(wizard.owner, wizard.power)
    assert not second.state()['required']
    assert wizard.store.get('device_id') == device and wizard.store.authenticate(key)['id'] == kid
    assert len(wizard.store.keys()) == 1
    assert key not in wizard.path.read_text() and 'PONG' not in wizard.path.read_text()
    wizard.store.revoke(kid)
    with pytest.raises(ValueError): wizard.action('finish', finish)


def test_mac_setup_open_and_prompt_do_not_deploy_or_change_login(wizard, monkeypatch):
    from desktop_bridge import macos_onboarding as mac
    monkeypatch.setattr(mac.providers, 'status', lambda *_: {'ready': True})
    monkeypatch.setattr(mac.subprocess, 'run', lambda *_a, **_k: pytest.fail('ready login must not open Terminal'))
    wizard.login('codex'); wizard.login('claude')
    prompt = wizard.prompt()['prompt']
    assert 'macOS' in prompt and 'byo_setup.py' in prompt
    assert str(wizard.store.directory) in prompt and 'aigo-bridge.exe' not in prompt
    assert 'Keychain' in prompt
    wizard.action('open', {})
    assert wizard.state()['open_requested'] and wizard.state()['required']


@pytest.mark.parametrize('url', ['https://127.0.0.1:8000/', 'http://localhost:8000/',
    'http://127.0.0.1:8001/', 'http://127.0.0.1:8000/other', 'http://127.0.0.1:8000/?evil', 'file:///local'])
def test_mac_native_privileges_never_follow_other_pages(url):
    from desktop_bridge.macos_console import NativeApi
    api = NativeApi({'origin': 'http://127.0.0.1:8000'})
    api._window = SimpleNamespace(get_current_url=lambda: url)
    with pytest.raises(ValueError): api.copy_text('synthetic')
    with pytest.raises(ValueError): api.export_logs('status=completed')
    with pytest.raises(ValueError): api.open_browser()


def test_native_clipboard_stdin_and_cancelled_export(wizard, monkeypatch):
    from desktop_bridge import macos_console as console
    calls = []
    monkeypatch.setattr(console.subprocess, 'run', lambda command, **kw: calls.append((command, kw)) or SimpleNamespace(returncode=0))
    api = console.NativeApi({'origin': 'http://127.0.0.1:8000'})
    api._window = SimpleNamespace(get_current_url=lambda: 'http://127.0.0.1:8000/#keys', create_file_dialog=lambda *_a, **_kw: None)
    assert api.copy_text('synthetic 中文')['ok']
    assert calls[0][0] == ['/usr/bin/pbcopy'] and calls[0][1]['input'] == 'synthetic 中文'.encode()
    for invalid in ('', None, 'x\0y', 'x' * 65537):
        with pytest.raises(ValueError): api.copy_text(invalid)
    # No optional GUI import is required to validate a cancelled/invalid path.
    monkeypatch.setitem(__import__('sys').modules, 'webview', SimpleNamespace(FileDialog=SimpleNamespace(SAVE=1)))
    monkeypatch.setattr(console, 'request_owner', lambda *_: pytest.fail('cancel must not fetch metadata'))
    assert api.export_logs('provider=codex') == {'saved': False}
    with pytest.raises(ValueError): api.export_logs('destination=external')


def test_cocoa_save_panel_string_is_a_complete_path_not_first_character(tmp_path, monkeypatch):
    from desktop_bridge import macos_console as console
    monkeypatch.setitem(__import__('sys').modules, 'webview', SimpleNamespace(FileDialog=SimpleNamespace(SAVE=1)))
    output = tmp_path / 'metadata 中文.csv'
    api = console.NativeApi({'origin': 'http://127.0.0.1:8000'})
    api._window = SimpleNamespace(get_current_url=lambda: 'http://127.0.0.1:8000/', create_file_dialog=lambda *_a, **_kw: str(output))
    monkeypatch.setattr(console, 'request_owner', lambda *_: b'metadata only')
    assert api.export_logs('')['saved'] and output.read_bytes() == b'metadata only'


@pytest.mark.skipif(os.name == 'nt', reason='Mac source updates use the POSIX profile lock.')
def test_mac_update_failure_restores_manifest_and_restarts_original(tmp_path, monkeypatch):
    from tools import mac_service
    root = tmp_path / 'installed'; root.mkdir()
    source = tmp_path / 'source'; (source / 'tools').mkdir(parents=True)
    (source / 'desktop_bridge').mkdir(); (source / 'tools/install.py').touch(); (source / 'desktop_bridge/__init__.py').touch()
    original = {'install_root': str(root), 'data_dir': str(root / 'data'), 'app': 'old', 'python': 'python', 'version': 'old'}
    (root / 'source-install.json').write_text(json.dumps(original))
    actions = []
    monkeypatch.setattr(mac_service, 'control', lambda action, *_a, **_kw: actions.append(action))
    def failed(*_args, **_kw):
        (root / 'source-install.json').write_text(json.dumps({**original, 'app': 'broken'}))
        return SimpleNamespace(returncode=1)
    monkeypatch.setattr(mac_service.subprocess, 'run', failed)
    with pytest.raises(ValueError): mac_service.update(root, source)
    assert json.loads((root / 'source-install.json').read_text()) == original
    assert actions == ['stop', 'stop', 'start']
    receipt = json.loads((root / 'macos-update.json').read_text())
    assert receipt['status'] == 'failed' and receipt['recovered']
