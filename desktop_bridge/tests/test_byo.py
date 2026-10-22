import json
from pathlib import Path

import pytest

from desktop_bridge import secret
from desktop_bridge.byo import Cloudflare,SetupError,configure,origin,publish,status,main
from desktop_bridge.store import Store

ACCOUNT='a'*32


class FakeCloud:
    def __init__(self,name,*,allowed=True,fail_secret=False):
        self.name=name;self.allowed=allowed;self.fail_secret=fail_secret;self.calls=[]
    def verify(self):
        if not self.allowed:raise SetupError('Wrong account')
    def run(self,args,input=None):
        self.calls.append((args,input))
        if args==['deploy']:return 'https://'+self.name+'.test-owner.workers.dev'
        if self.fail_secret:raise SetupError('Retryable cloud failure')
        return ''


@pytest.fixture
def crypto(monkeypatch):
    monkeypatch.setattr(secret,'uses_keychain',lambda:False)
    import base64
    def protect(value,decrypt=False):
        if decrypt:
            if not value.startswith(b'enc:'):raise ValueError('Wrong Windows user')
            return base64.b64decode(value[4:])
        return b'enc:'+base64.b64encode(value)
    monkeypatch.setattr(secret,'protect',protect)


def test_device_identity_survives_restart_and_differs_between_devices(tmp_path):
    first=Store(tmp_path/'one');did=first.get('device_id');_,key=first.create_key('device key')
    first.set('public_url','https://fixed.example.test');first.close()
    first=Store(tmp_path/'one');second=Store(tmp_path/'two')
    assert len(did)==32 and first.get('device_id')==did and second.get('device_id')!=did
    assert first.authenticate(key) and first.get('public_url')=='https://fixed.example.test'
    first.close();second.close()


def test_stable_worker_per_device_and_cloud_account_guard(tmp_path):
    first=Store(tmp_path/'one');second=Store(tmp_path/'two')
    config=configure(first,ACCOUNT);name=first.get('cloudflare_worker_name')
    assert configure(first)==config and first.get('cloudflare_worker_name')==name
    configure(second,ACCOUNT);assert second.get('cloudflare_worker_name')!=name
    with pytest.raises(SetupError):configure(first,'b'*32)
    with pytest.raises(SetupError):configure(first,worker_name='another-worker')
    assert json.loads(config.read_text())['account_id']==ACCOUNT
    first.close();second.close()


def test_existing_endpoint_is_adopted_instead_of_recreated(tmp_path):
    store=Store(tmp_path);store.set('public_url','https://my-old-device.owner.workers.dev')
    configure(store,ACCOUNT)
    assert store.get('cloudflare_worker_name')=='my-old-device'
    with pytest.raises(SetupError):configure(store,worker_name='new-worker')
    store.close()


def test_deploy_retry_keeps_pending_encrypted_and_preserves_api_keys(tmp_path,crypto):
    store=Store(tmp_path);_,key=store.create_key('keep');config=configure(store,ACCOUNT)
    did=store.get('device_id');cloud=FakeCloud(store.get('cloudflare_worker_name'),fail_secret=True)
    with pytest.raises(SetupError):publish(store,config,cloud)
    token=cloud.calls[-1][1].strip()
    pending=tmp_path/'relay-device.pending.dpapi'
    assert pending.exists() and token not in pending.read_bytes() and not store.get('public_url')
    cloud.fail_secret=False;url=publish(store,config,cloud)
    assert not pending.exists() and secret.load(tmp_path).encode()==token
    assert store.authenticate(key) and store.get('device_id')==did
    assert publish(store,config,cloud)==url and secret.load(tmp_path).encode()==token
    store.close()


def test_reauth_different_cloud_account_cannot_mutate_endpoint_or_keys(tmp_path,crypto):
    store=Store(tmp_path);_,key=store.create_key('keep');config=configure(store,ACCOUNT)
    good=FakeCloud(store.get('cloudflare_worker_name'));url=publish(store,config,good)
    old=secret.load(tmp_path);wrong=FakeCloud(good.name,allowed=False)
    with pytest.raises(SetupError):publish(store,config,wrong)
    assert not wrong.calls and store.get('public_url')==url and store.authenticate(key) and secret.load(tmp_path)==old
    store.close()


def test_existing_code_upgrade_does_not_rewrite_unchanged_secret(tmp_path,crypto):
    store=Store(tmp_path);config=configure(store,ACCOUNT)
    cloud=FakeCloud(store.get('cloudflare_worker_name'));url=publish(store,config,cloud)
    credential=secret.load(tmp_path);before=len(cloud.calls)
    assert publish(store,config,cloud)==url
    assert [c[0] for c in cloud.calls[before:]]==[['deploy']]
    assert secret.load(tmp_path)==credential
    before=len(cloud.calls)
    publish(store,config,cloud,repair=True)
    assert [c[0] for c in cloud.calls[before:]]==[['deploy'],['secret','put','DEVICE_KEY'],['deploy']]
    assert secret.load(tmp_path)!=credential
    store.close()


def test_cross_windows_user_repair_retains_device_url_and_client_keys(tmp_path,crypto):
    store=Store(tmp_path);_,key=store.create_key('keep');config=configure(store,ACCOUNT)
    cloud=FakeCloud(store.get('cloudflare_worker_name'));url=publish(store,config,cloud)
    did=store.get('device_id');(tmp_path/'relay-device.dpapi').write_bytes(b'wrong-user')
    assert status(store)['device_repair_required']
    count=len(cloud.calls)
    with pytest.raises(SetupError):publish(store,config,cloud)
    assert len(cloud.calls)==count
    publish(store,config,cloud,code=False,repair=True)
    assert secret.load(tmp_path) and store.get('public_url')==url and store.authenticate(key) and store.get('device_id')==did
    store.close()


def test_pair_rejects_endpoint_changes_before_cloud_secret_write(tmp_path,crypto):
    store=Store(tmp_path);config=configure(store,ACCOUNT);cloud=FakeCloud(store.get('cloudflare_worker_name'))
    url=publish(store,config,cloud);count=len(cloud.calls)
    with pytest.raises(SetupError):publish(store,config,cloud,code=False,url='https://new.example.test')
    assert len(cloud.calls)==count and store.get('public_url')==url
    store.close()


def test_first_pair_checks_actual_edge_credential_before_committing(tmp_path,crypto):
    store=Store(tmp_path);config=configure(store,ACCOUNT)
    class ReadyCloud(FakeCloud):
        probes=0
        def wait_pairing(self,url,token):
            self.probes+=1
            assert secret.load(tmp_path,pending=True)==token and not secret.load(tmp_path)
            assert self.calls[-1][0]==['secret','put','DEVICE_KEY']
    cloud=ReadyCloud(store.get('cloudflare_worker_name'))
    publish(store,config,cloud);assert cloud.probes==1
    publish(store,config,cloud);assert cloud.probes==1
    store.close()


@pytest.mark.parametrize('value',['http://x.test','https://user:pw@x.test','https://x.test/api/v1','https://x.test?q=1','https://x.test:8080'])
def test_invalid_origin_rejected(value):
    with pytest.raises(SetupError):origin(value)


def test_cli_key_lifecycle_is_local_and_preserves_live_work(tmp_path,capsys):
    store=Store(tmp_path)
    store.insert_request({'id':'live','status':'running'})
    store.close()
    def run(action,*args):
        assert main([action,'--data-dir',str(tmp_path),*args])==0
        return json.loads(capsys.readouterr().out)
    created=run('key-create','--label','CLI acceptance','--providers','codex')
    assert created['key'].startswith('sk-br-')
    listed=run('key-list')['keys']
    assert listed[0]['id']==created['id'] and 'digest' not in listed[0] and 'key' not in listed[0]
    rotated=run('key-rotate','--key-id',created['id'])
    store=Store(tmp_path,startup=False)
    assert not store.authenticate(created['key']) and store.authenticate(rotated['key'])['providers']==['codex']
    assert store.db.execute("select status from requests where id='live'").fetchone()[0]=='running'
    store.close()
    run('key-revoke','--key-id',rotated['id']);run('key-revoke','--key-id',rotated['id'])
    store=Store(tmp_path,startup=False);assert not store.authenticate(rotated['key']);store.close()
    assert created['key'].encode() not in (tmp_path/'bridge.sqlite').read_bytes()
    assert rotated['key'].encode() not in (tmp_path/'bridge.sqlite').read_bytes()
    assert main(['key-revoke','--data-dir',str(tmp_path),'--key-id','absent'])==1
    assert 'absent' not in capsys.readouterr().err
