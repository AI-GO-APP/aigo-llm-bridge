"""The Mac release must contain the current BYO installer and no local profiles."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import zipfile

import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('macos_builder',ROOT/'packaging/macos/build.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)


def source_repo(tmp_path,monkeypatch):
    root=tmp_path/'source';root.mkdir()
    for name in builder.REQUIRED | {'VERSION','README.md'}:
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('0.9.1-mac.1\n' if name=='VERSION' else 'public fixture\n')
    subprocess.run(['git','init','-q',str(root)],check=True)
    subprocess.run(['git','add','.'],cwd=root,check=True)
    subprocess.run(['git','-c','user.name=Fixture','-c','user.email=fixture@example.test',
                    'commit','-qm','public source'],cwd=root,check=True)
    monkeypatch.setattr(builder,'ROOT',root)
    return root


def test_release_contains_current_byo_sources_and_executable_installer(tmp_path,monkeypatch):
    source_repo(tmp_path,monkeypatch)
    package=builder.build(tmp_path/'output')
    manifest=json.loads((package.parent/'macos-source-manifest.json').read_text())
    assert manifest['format']=='macos-byo-source' and manifest['requires_python']=='>=3.12'
    assert manifest['redistributable'] and not manifest['dirty']
    assert manifest['sha256']==hashlib.sha256(package.read_bytes()).hexdigest()
    with zipfile.ZipFile(package) as archive:
        names=set(archive.namelist())
        assert all(builder.PREFIX+p in names for p in builder.REQUIRED)
        assert archive.getinfo(builder.PREFIX+'Install.command').external_attr >> 16 & 0o111
        assert json.loads(archive.read(builder.PREFIX+'source-release.json'))['commit']==manifest['commit']
        assert not any('/desktop/' in name or 'bridge.sqlite' in name for name in names)


def test_dirty_or_private_files_cannot_be_published(tmp_path,monkeypatch):
    root=source_repo(tmp_path,monkeypatch)
    private=root/'.desktop-data';private.mkdir();(private/'bridge.sqlite').write_bytes(b'synthetic private fixture')
    with pytest.raises(ValueError): builder.build(tmp_path/'release')
    package=builder.build(tmp_path/'local-only',allow_dirty=True)
    manifest=json.loads((package.parent/'macos-source-manifest.json').read_text())
    assert not manifest['redistributable']
    with zipfile.ZipFile(package) as archive: assert not any('.desktop-data' in n for n in archive.namelist())
