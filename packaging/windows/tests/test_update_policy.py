import base64
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest
pytest.importorskip('cryptography')
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from desktop_bridge import windows_updates as updates


@pytest.fixture
def policy():
    key = Ed25519PrivateKey.generate()
    cfg = {'platform':'windows','arch':'x64','pack_id':'AIGO.LLMBridge.Probe.Test','channel':'internal',
           'local_probe':True,'version':'0.7.0','policy_url':'http://127.0.0.1:9876/policy.json',
           'public_key':base64.b64encode(key.public_key().public_bytes_raw()).decode()}
    payload = {k:cfg[k] for k in ('platform','arch','pack_id','channel')}
    payload.update(schema=1,version='0.7.1',minimum_version='0.7.0',sequence=1,
        expires_at=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat(),
        release_url='http://127.0.0.1:9876/b',feed_sha256='a'*64,package_sha256='b'*64,commit='c'*40)
    def signed(value):
        return {'payload':value,'signature':base64.b64encode(key.sign(updates.canonical(value))).decode()}
    return cfg,payload,signed


@pytest.mark.parametrize('change', [
    {'platform':'macos'}, {'arch':'arm64'}, {'channel':'stable'}, {'pack_id':'wrong'},
    {'sequence':True}, {'sequence':0}, {'sequence':9007199254740992},
    {'minimum_version':'0.9.0'}, {'version':'../0.7.1'}, {'feed_sha256':'bad'},
    {'expires_at':'2000-01-01T00:00:00+00:00'}, {'extra':'unsupported'},
    {'release_url':'http://example.com/update'}, {'release_url':'https://user:pass@example.com'}])
def test_wrong_signed_policy_cannot_enter_this_target(policy,change):
    cfg,payload,signed=policy
    with pytest.raises(updates.UpdateError):
        updates.verify(signed({**payload,**change}),cfg)


def test_tamper_and_wrong_signer_rejected(policy):
    cfg,payload,signed=policy
    envelope=signed(payload);envelope['payload']={**payload,'version':'0.7.2'}
    with pytest.raises(updates.UpdateError):updates.verify(envelope,cfg)
    cfg['public_key']=base64.b64encode(Ed25519PrivateKey.generate().public_key().public_bytes_raw()).decode()
    with pytest.raises(updates.UpdateError):updates.verify(signed(payload),cfg)


def test_replay_replacement_and_expired_source_do_not_reset_state(policy,monkeypatch,tmp_path):
    cfg,payload,signed=policy
    selected=[signed(payload)]
    monkeypatch.setattr(updates,'fetch',lambda *_:json.dumps(selected[0]).encode())
    assert updates.check(cfg,tmp_path)['available']
    for override in ({'sequence':0},{'sequence':1,'version':'0.7.2'},
                     {'sequence':2,'feed_sha256':'d'*64}):
        selected[0]=signed({**payload,**override})
        with pytest.raises(updates.UpdateError):updates.check(cfg,tmp_path)
    selected[0]=signed({**payload,'version':'0.7.2','sequence':2})
    assert updates.check(cfg,tmp_path)['latest']=='0.7.2'


def test_valid_new_sequence_cannot_lower_known_minimum(policy,monkeypatch,tmp_path):
    cfg,payload,signed=policy
    selected=[signed({**payload,'minimum_version':'0.7.1'})]
    monkeypatch.setattr(updates,'fetch',lambda *_:json.dumps(selected[0]).encode())
    assert updates.check(cfg,tmp_path)['required']
    selected[0]=signed({**payload,'sequence':2})
    with pytest.raises(updates.UpdateError):updates.check(cfg,tmp_path)


def test_management_cannot_resume_below_verified_minimum(tmp_path,monkeypatch):
    from desktop_bridge.windows_management import WindowsManagementServer
    from desktop_bridge.windows_release import atomic_json
    server=object.__new__(WindowsManagementServer)
    server.release={'pack_id':'fixture'}
    from types import SimpleNamespace
    server.store=SimpleNamespace(directory=tmp_path)
    atomic_json(tmp_path/'updates/minimum-block.json',{'pack_id':'fixture','previous_accepting':True})
    with pytest.raises(ValueError):server.action('/manage/accepting',{'accepting':True})


def test_unsigned_build_cannot_enable_loopback_transport(policy):
    cfg,payload,signed=policy
    with pytest.raises(updates.UpdateError):updates.transport(cfg['policy_url'],{**cfg,'local_probe':False})


def test_backup_preserves_metadata_and_encrypted_credentials(tmp_path):
    from desktop_bridge.store import Store
    store=Store(tmp_path);key_id,key=store.create_key('synthetic',providers=['codex'])
    device=store.get('device_id');store.set('public_url','https://fixture.invalid');store.close()
    (tmp_path/'relay-device.dpapi').write_bytes(b'encrypted-fixture')
    root=updates.backup(tmp_path,'0.7.1')
    restored=Store(root,startup=False)
    assert restored.get('device_id')==device and restored.authenticate(key)['id']==key_id
    assert (root/'relay-device.dpapi').read_bytes()==b'encrypted-fixture'
    assert key.encode() not in (root/'bridge.sqlite').read_bytes()
    restored.close()


@pytest.mark.skipif(__import__('os').name!='nt',reason='Windows instance and update locks')
def test_recovery_refuses_changed_schema_then_restores_only_compatible_old_binary(tmp_path):
    from desktop_bridge.store import Store
    from desktop_bridge.windows_release import atomic_json
    cfg={'pack_id':'AIGO.LLMBridge.Probe.Recovery','version':'0.7.0'}
    store=Store(tmp_path);store.set('accepting',False)
    original=updates.schema_digest(tmp_path)
    pending={'pack_id':cfg['pack_id'],'from_version':'0.7.0','target':'0.7.1','previous_accepting':True,'schema_sha256':original}
    atomic_json(tmp_path/'updates/pending.json',pending)
    store.db.execute('create table fixture_change(id integer)');store.db.commit()
    with pytest.raises(updates.UpdateError):updates.recover(cfg,tmp_path)
    assert (tmp_path/'updates/pending.json').is_file()
    store.db.execute('drop table fixture_change');store.db.commit();store.close()
    assert updates.recover(cfg,tmp_path)['recovered']
    store=Store(tmp_path,startup=False);assert store.get('accepting');store.close()
def test_immutable_github_release_uses_explicit_http_source(tmp_path,monkeypatch):
    """A string chooses GithubSource and 404s; the loopback A/B test cannot catch that."""
    import hashlib
    import json
    import velopack
    from desktop_bridge import windows_updates as updates
    raw=json.dumps({'Assets':[{'Type':'Full','Version':'0.7.2','PackageId':'fixture','FileName':'fixture-full.nupkg'}]}).encode()
    policy={'release_url':'https://github.com/example/project/releases/download/fixed-tag',
            'feed_sha256':hashlib.sha256(raw).hexdigest(),'version':'0.7.2'}
    monkeypatch.setattr(updates,'check',lambda *_:{'available':True,'policy':policy})
    monkeypatch.setattr(updates,'fetch',lambda *_:raw)
    class ReachedNativeSource(Exception):pass
    def manager(source,options):
        assert isinstance(source,velopack.HttpSource)
        assert options.ExplicitChannel=='windows-x64-internal'
        raise ReachedNativeSource()
    monkeypatch.setattr(velopack,'UpdateManager',manager)
    with pytest.raises(ReachedNativeSource):
        updates.apply({'pack_id':'fixture','framework_channel':'windows-x64-internal'},tmp_path)
