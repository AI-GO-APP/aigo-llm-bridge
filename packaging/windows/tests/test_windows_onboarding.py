import copy
import json
from types import SimpleNamespace

import pytest

from desktop_bridge import windows_onboarding as onboarding
from desktop_bridge.store import Store
from desktop_bridge.windows_power import PowerPolicy, SETTINGS, USER_VALUES


class FakePower:
    def __init__(self):
        self.active = 'original'
        self.values = {('original', setting, dc): 120 if not dc else 30 for _, _, setting in SETTINGS for dc in (False, True)}
        self.registry_values = {(path, name, False): {'exists': True, 'value': '1' if isinstance(value, str) else 1,
                                                     'type': 1 if isinstance(value, str) else 4} for path, name, value in USER_VALUES}
        self.connected = True
        self.writes = []
        self.denied = False

    def scheme(self, duplicate=None):
        if duplicate:
            for key, value in list(self.values.items()):
                if key[0] == duplicate:
                    self.values[('bridge', *key[1:])] = value
            return 'bridge'
        return self.active

    def read(self, scheme, sub, setting, dc=False):
        return self.values[scheme, setting, dc]

    def write(self, scheme, sub, setting, value):
        if self.denied:
            raise OSError(5, 'synthetic denied')
        self.writes.append((scheme, sub, setting, value))
        self.values[scheme, setting, False] = value

    def activate(self, scheme):
        self.active = scheme

    def registry(self, path, name, machine=False):
        return copy.deepcopy(self.registry_values.get((path, name, machine), {'exists': False}))

    def set_registry(self, path, name, value):
        self.registry_values[path, name, False] = copy.deepcopy(value)

    def ac(self):
        return self.connected


def test_power_requires_explicit_consent_and_never_touches_dc(tmp_path):
    native = FakePower()
    before = copy.deepcopy(native.values)
    policy = PowerPolicy(tmp_path, native)
    with pytest.raises(ValueError):
        policy.apply()
    assert not native.writes and not policy.path.exists()
    assert policy.apply(consent=True)['verified']
    assert native.active == 'bridge'
    for _, _, setting in SETTINGS:
        assert native.values['original', setting, False] == before['original', setting, False]
        assert native.values['bridge', setting, False] == 0
        assert native.values['bridge', setting, True] == before['original', setting, True]
    policy.restore()
    assert native.active == 'original'
    assert not policy.inspect()['enabled']


def test_ac_guard_restores_locks_on_battery_and_does_not_rewrite_them(tmp_path):
    native = FakePower()
    old = copy.deepcopy(native.registry_values)
    policy = PowerPolicy(tmp_path, native)
    policy.apply(consent=True)
    assert native.registry_values != old
    native.connected = False
    policy.tick()
    assert native.registry_values == old
    path, name, _ = USER_VALUES[0]
    native.registry_values[path, name, False]['value'] = 'owner-change'
    policy.tick()
    assert native.registry_values[path, name, False]['value'] == 'owner-change'
    native.connected = True
    policy.tick()
    policy.stop()
    assert native.registry_values[path, name, False]['value'] == '1'


def test_power_failure_rolls_back_and_cannot_claim_success(tmp_path):
    native = FakePower()
    native.denied = True
    policy = PowerPolicy(tmp_path, native)
    with pytest.raises(OSError):
        policy.apply(consent=True)
    assert native.active == 'original' and not policy.inspect()['verified']


def test_managed_lock_policy_is_not_overridden(tmp_path):
    native = FakePower()
    native.registry_values[r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System', 'InactivityTimeoutSecs', True] = {
        'exists': True, 'value': 600, 'type': 4}
    policy = PowerPolicy(tmp_path, native)
    with pytest.raises(ValueError):
        policy.apply(consent=True)
    assert policy.inspect()['blockers'] == ['InactivityTimeoutSecs']
    assert not native.writes


def test_changed_plan_is_reported_and_owner_plan_survives_restore(tmp_path):
    native = FakePower()
    policy = PowerPolicy(tmp_path, native)
    policy.apply(consent=True)
    native.active = 'owner-other-plan'
    assert not policy.inspect()['verified']
    policy.restore()
    assert native.active == 'owner-other-plan'


@pytest.fixture
def wizard(tmp_path, monkeypatch):
    store = Store(tmp_path, startup=False)
    owner = SimpleNamespace(store=store, release={'version': '0.8.0', 'pack_id': 'fixture'},
                            auth_checking=False, relay=None)
    monkeypatch.setattr(onboarding, 'installation_id', lambda *_: 'install-a')
    value = onboarding.Onboarding(owner, PowerPolicy(tmp_path, FakePower()))
    yield value
    store.close()


def wait_job(wizard):
    assert wizard.busy.acquire(timeout=5), 'background job did not finish'
    wizard.busy.release()


def test_first_install_daily_start_update_and_reinstall_are_distinct(wizard, monkeypatch):
    assert wizard.state()['required']
    saved = wizard.load()
    saved['completed_at'] = 123
    wizard.save(saved)
    assert not onboarding.Onboarding(wizard.owner, wizard.power).state()['required']
    wizard.owner.release['version'] = '0.8.1'
    assert not onboarding.Onboarding(wizard.owner, wizard.power).state()['required']
    key_id, key = wizard.store.create_key('retained')
    device = wizard.store.get('device_id')
    wizard.store.set('public_url', 'https://retained.example.invalid')
    monkeypatch.setattr(onboarding, 'installation_id', lambda *_: 'install-b')
    assert onboarding.Onboarding(wizard.owner, wizard.power).state()['required']
    assert wizard.store.authenticate(key)['id'] == key_id
    assert wizard.store.get('device_id') == device
    assert wizard.store.get('public_url') == 'https://retained.example.invalid'


def test_ready_subscription_is_never_logged_in_or_logged_out(wizard, monkeypatch):
    monkeypatch.setattr(onboarding.providers, 'status', lambda *_: {'ready': True})
    monkeypatch.setattr(onboarding.subprocess, 'Popen', lambda *_a, **_k: pytest.fail('must not change a ready login'))
    wizard.login('codex')
    wizard.login('claude')


def test_unready_subscription_with_active_requests_cannot_start_login(wizard, monkeypatch):
    monkeypatch.setattr(onboarding.providers, 'status', lambda *_: {'ready': False})
    wizard.store.insert_request({'id': 'active', 'status': 'running'})
    with pytest.raises(ValueError):
        wizard.login('codex')


def test_ai_ide_prompt_uses_same_profile_and_contains_no_credential(wizard):
    _, key = wizard.store.create_key('secret')
    prompt = wizard.prompt()['prompt']
    assert str(wizard.store.directory) in prompt and 'byo plan' in prompt and 'byo deploy' in prompt
    assert key not in prompt and '不要呼叫 Claude/Codex' in prompt
    assert 'auth.json' in prompt  # warning against requesting it, not credential content


def test_wrong_cloud_account_fails_before_project_or_cloud_mutation(wizard, monkeypatch):
    monkeypatch.setattr(onboarding, 'cloud_accounts', lambda *_: [{'id': 'a' * 32}])
    monkeypatch.setattr(onboarding.byo, 'configure', lambda *_: pytest.fail('not authorized'))
    with pytest.raises(ValueError):
        wizard.deploy('b' * 32, True)
    with pytest.raises(ValueError):
        wizard.deploy('a' * 32, False)


def test_unverified_http_and_forged_handoff_cannot_complete(wizard):
    with pytest.raises(ValueError):
        wizard.action('finish', {'key_saved': True, 'handoff_copied': True})
    assert wizard.state()['required']
    with pytest.raises(ValueError):
        wizard.action('power', {'consent': True})


def test_full_workflow_persists_metadata_only_and_bypasses_daily_wizard(wizard, monkeypatch):
    monkeypatch.setattr(onboarding.secret, 'load', lambda *_: 'synthetic-device-secret')
    monkeypatch.setattr(onboarding.providers, 'status', lambda *_: {'ready': True})
    monkeypatch.setattr(onboarding, 'verify', lambda *_: {'success': True, 'http_status': 200, 'cost_usd': .012345, 'code': 'ok'})
    wizard.store.set('public_url', 'https://synthetic.example.invalid')
    wizard.power.apply(consent=True)
    saved = wizard.load()
    saved['lock_checks_acknowledged'] = True
    wizard.save(saved)
    created = wizard.action('create-key', {})
    assert wizard.store.authenticate(created['token'])['providers'] == ['claude', 'codex']
    wizard.action('verify', {'key': created['token'], 'model': wizard.store.get('models')[1]['id']})
    wait_job(wizard)
    assert wizard.load()['verification']['success']
    wizard.action('finish', {'key_saved': True, 'handoff_copied': True})
    assert not wizard.state()['required']
    assert not onboarding.Onboarding(wizard.owner, wizard.power).state()['required']
    for path in wizard.store.directory.glob('*.json'):
        assert created['token'] not in path.read_text()
        assert 'Reply exactly' not in path.read_text()


def test_async_error_state_does_not_expose_exception_or_cli_output(wizard):
    def fail():
        raise RuntimeError('sensitive CLI result must never be returned')
    wizard.task('synthetic', fail)
    wait_job(wizard)
    assert wizard.job == {'status': 'failed', 'action': 'synthetic', 'code': 'operation_failed'}


@pytest.mark.parametrize('cost', [None, True, '0.1', -1, float('nan'), float('inf')])
def test_https_verifier_rejects_missing_or_non_numeric_cost(wizard, monkeypatch, cost):
    from contextlib import contextmanager
    _, key = wizard.store.create_key('test')
    wizard.store.set('public_url', 'https://fixture.example.invalid')
    calls = []
    @contextmanager
    def response(request, **_kwargs):
        calls.append(request)
        body = {'data': [{'id': 'test-model'}]} if len(calls) == 1 else {
            'choices': [{'message': {'content': 'PONG'}}], 'usage': {'cost': cost}}
        yield SimpleNamespace(status=200, read=lambda *_: json.dumps(body).encode())
    monkeypatch.setattr(onboarding.urllib.request, 'build_opener', lambda *_: SimpleNamespace(open=response))
    result = onboarding.verify(wizard.store, key, 'test-model')
    assert not result['success'] and result['cost_usd'] is None
    assert [r.get_method() for r in calls] == ['GET', 'POST']


def test_install_hook_creates_new_install_id_only_on_install(tmp_path, monkeypatch):
    monkeypatch.setattr(onboarding, 'installation_marker', lambda: tmp_path / 'install.json')
    onboarding.record_install('0.8.0')
    first = json.loads((tmp_path / 'install.json').read_text())
    onboarding.record_install('0.8.0')
    assert json.loads((tmp_path / 'install.json').read_text()) != first


def test_reinstall_can_deliver_same_existing_key_after_real_verification(wizard, monkeypatch):
    monkeypatch.setattr(onboarding.providers, 'status', lambda *_: {'ready': True})
    monkeypatch.setattr(onboarding, 'verify', lambda *_: {'success': True, 'cost_usd': 0, 'code': 'ok'})
    wizard.store.set('public_url', 'https://same.example.invalid')
    kid, key = wizard.store.create_key('original-saved-key')
    wizard.power.apply(consent=True)
    value = wizard.load(); value['lock_checks_acknowledged'] = True; wizard.save(value)
    wizard.action('verify', {'key': key, 'model': wizard.store.get('models')[1]['id']})
    wait_job(wizard)
    wizard.action('finish', {'key_saved': True, 'handoff_copied': True})
    assert not wizard.state()['required']
    assert wizard.load()['key_id'] == kid and len(wizard.store.keys()) == 1


def test_admin_helper_does_not_change_administrator_hkcu(tmp_path, monkeypatch):
    import time
    from desktop_bridge import windows_power_admin as admin
    from desktop_bridge.windows_release import atomic_json
    monkeypatch.setattr(admin.ctypes, 'windll', SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda: True)), raising=False)
    calls = []
    class Policy:
        def __init__(self, _directory): pass
        def apply(self, **kwargs):
            calls.append(kwargs)
            return {'verified': True}
    monkeypatch.setattr(admin, 'PowerPolicy', Policy)
    values = [{'exists': False}] * 3
    path = tmp_path / 'windows-power-elevation.json'
    atomic_json(path, {'nonce': 'synthetic-request', 'created_at': time.time(), 'operation': 'apply', 'user_values': values})
    assert admin.elevated(tmp_path, 'wrong', 'apply') == 1
    assert not calls
    assert admin.elevated(tmp_path, 'synthetic-request', 'apply') == 0
    assert calls == [{'consent': True, 'user_values': values, 'manage_user': False}]
    assert not path.exists()


def test_admin_actions_require_explicit_consent(wizard):
    for action in ('power-admin', 'restore-power-admin'):
        with pytest.raises(ValueError):
            wizard.action(action, {})


def test_externally_deployed_same_profile_restarts_relay_once(wizard, monkeypatch):
    calls = []
    wizard.owner.relay = SimpleNamespace(stop=lambda: calls.append('stop'), start=lambda: calls.append('start'))
    monkeypatch.setattr(onboarding.providers, 'status', lambda *_: {'ready': True})
    monkeypatch.setattr(onboarding, 'cloud_accounts', lambda *_: [])
    wizard.store.set('public_url', 'https://external-ide.example.invalid')
    wizard.store.set('relay_enabled', True)
    wizard.refresh()
    assert calls == ['stop', 'start']
    wizard.refresh()
    assert calls == ['stop', 'start']
