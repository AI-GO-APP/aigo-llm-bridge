"""Publish Windows-only immutable assets and a signed channel pointer; no Cloud access."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from desktop_bridge.windows_updates import canonical, verify, fetch, version


def gh(*args,check=True):
    return subprocess.run(['gh',*map(str,args)],check=check,capture_output=True,text=True)


def same_release_action(old, new, now=None):
    if any(old[k] != new[k] for k in ('feed_sha256','package_sha256','commit')):
        raise ValueError('A published Windows version cannot be replaced.')
    if version(new['minimum_version']) < version(old['minimum_version']):
        raise ValueError('Cannot lower the minimum Windows version.')
    expires = datetime.fromisoformat(old['expires_at'].replace('Z','+00:00'))
    remaining = (expires - (now or datetime.now(timezone.utc))).total_seconds()
    return 'unchanged' if old['minimum_version'] == new['minimum_version'] and remaining > 7 * 86400 else 'refresh'


def publish(build, repository, minimum):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
    root=Path(build)
    report=json.loads((root/'artifacts.json').read_text());cfg=report['config']
    if not (cfg['platform']=='windows' and cfg['arch']=='x64' and cfg['channel']=='internal'
            and cfg['pack_id']=='AIGO.LLMBridge.Windows.Internal' and cfg['redistributable']
            and not cfg['local_probe'] and not cfg['dirty']):
        raise ValueError('Only clean redistributable Windows internal builds can be published.')
    if cfg['public_key']!=os.environ['BRIDGE_WINDOWS_UPDATE_PUBLIC_KEY']:
        raise ValueError('Unexpected Windows update identity.')
    tag='windows-installer-internal-v'+cfg['version']
    pointer_tag='windows-updates-internal';pointer_name='windows-x64-internal-policy.json'
    policy_url=f'https://github.com/{repository}/releases/download/{pointer_tag}/{pointer_name}'
    if cfg['policy_url']!=policy_url:
        raise ValueError('Installer policy URL is not this Windows channel.')
    key=Ed25519PrivateKey.from_private_bytes(base64.b64decode(os.environ['BRIDGE_WINDOWS_UPDATE_PRIVATE_KEY'],validate=True))
    Ed25519PublicKey.from_public_bytes(base64.b64decode(cfg['public_key'])).verify(key.sign(b'identity-probe'),b'identity-probe')
    head=gh('api',f'repos/{repository}/commits/'+cfg['commit']).stdout
    if json.loads(head)['sha']!=cfg['commit']:
        raise ValueError('Source commit is missing.')
    ancestry=json.loads(gh('api',f'repos/{repository}/compare/'+cfg['commit']+'...main').stdout)
    if ancestry['status'] not in ('ahead','identical'):
        raise ValueError('Installer source is not part of main.')
    sequence=1;previous=None
    with tempfile.TemporaryDirectory() as temp:
        temp=Path(temp)
        pointer_release=gh('release','view',pointer_tag,'--repo',repository,check=False)
        if pointer_release.returncode==0:
            prior=gh('release','download',pointer_tag,'--repo',repository,'--pattern',pointer_name,'--dir',temp,check=False)
            if prior.returncode!=0:
                raise ValueError('Existing Windows channel pointer is unreadable; refusing to reset its sequence.')
            previous=json.loads((temp/pointer_name).read_text())
            Ed25519PublicKey.from_public_bytes(base64.b64decode(cfg['public_key'])).verify(
                base64.b64decode(previous['signature']),canonical(previous['payload']))
            old=previous['payload']
            if any(old[k]!=cfg[k] for k in ('platform','arch','channel','pack_id')):
                raise ValueError('Existing pointer belongs to a different target.')
            if version(cfg['version'])<version(old['version']) or version(minimum)<version(old['minimum_version']):
                raise ValueError('A stale publication cannot downgrade this channel.')
            sequence=old['sequence']+1
        spec=importlib.util.spec_from_file_location('sign_update',ROOT/'packaging/windows/sign_update.py')
        signer=importlib.util.module_from_spec(spec);spec.loader.exec_module(signer)
        envelope=signer.sign(root,f'https://github.com/{repository}/releases/download/{tag}',sequence,minimum,key)
        if previous and previous['payload']['version']==cfg['version']:
            if same_release_action(previous['payload'], envelope['payload']) == 'unchanged':
                print('Windows channel already announced with identical content.');return
        release_exists=gh('release','view',tag,'--repo',repository,check=False).returncode==0
        assets=[root/'Releases'/item['name'] for item in report['artifacts']]+[root/'artifacts.json',root/'self-test.json']
        if not release_exists:
            gh('release','create',tag,'--repo',repository,'--target',cfg['commit'],'--prerelease',
                '--title',tag,'--notes','Unsigned Windows internal installer. Installer-owned BYO Cloudflare; no Cloud deployment.',*assets)
        readback=temp/'readback';readback.mkdir()
        gh('release','download',tag,'--repo',repository,'--dir',readback)
        for original in assets:
            downloaded=readback/original.name
            if not downloaded.is_file() or hashlib.sha256(downloaded.read_bytes()).digest()!=hashlib.sha256(original.read_bytes()).digest():
                raise ValueError('Published asset readback mismatch; channel was not announced.')
            anonymous=fetch(f'https://github.com/{repository}/releases/download/{tag}/{original.name}',cfg,original.stat().st_size)
            if hashlib.sha256(anonymous).digest()!=hashlib.sha256(original.read_bytes()).digest():
                raise ValueError('Anonymous public download differs; channel was not announced.')
        pointer=temp/pointer_name;pointer.write_text(json.dumps(envelope,indent=2),encoding='utf-8')
        if pointer_release.returncode!=0:
            gh('release','create',pointer_tag,'--repo',repository,'--target',cfg['commit'],'--prerelease',
                '--title','Windows internal update channel','--notes','Mutable signed Windows-only channel pointer.',pointer)
        else:
            gh('release','upload',pointer_tag,'--repo',repository,'--clobber',pointer)
        returned=json.loads(fetch(policy_url,cfg,65536));verify(returned,cfg)
        if returned!=envelope:raise ValueError('Announced Windows policy readback mismatch.')
        print(json.dumps({'announced':True,'version':cfg['version'],'sequence':sequence,
            'release_set_id':str(uuid.uuid5(uuid.NAMESPACE_URL,f'{repository}:windows:{cfg["version"]}:{cfg["commit"]}'))}))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    source=p.add_mutually_exclusive_group(required=True)
    source.add_argument('--build');source.add_argument('--published-version')
    p.add_argument('--repository',required=True);p.add_argument('--minimum-version',required=True)
    a=p.parse_args()
    if a.published_version:
        version(a.published_version)
        with tempfile.TemporaryDirectory() as selected:
            selected=Path(selected)
            gh('release','download','windows-installer-internal-v'+a.published_version,
               '--repo',a.repository,'--dir',selected)
            report=json.loads((selected/'artifacts.json').read_text())
            if report['config']['version']!=a.published_version:raise ValueError('Published version mismatch.')
            (selected/'Releases').mkdir()
            for item in report['artifacts']:
                if Path(item['name']).name!=item['name']:raise ValueError('Invalid artifact path.')
                (selected/item['name']).rename(selected/'Releases'/item['name'])
            publish(selected,a.repository,a.minimum_version)
    else:
        publish(a.build,a.repository,a.minimum_version)
