import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.mark.skipif(os.name!='nt',reason='Windows installer')
def test_installer_update_preserves_profile_and_refuses_accidental_change(tmp_path):
    root=Path(__file__).resolve().parents[2]
    package=tmp_path/'package';(package/'app').mkdir(parents=True)
    shutil.copyfile(root/'installer/windows/Install.ps1',package/'Install.ps1')
    (package/'app/AIGO-LLM-Bridge.exe').write_bytes(b'installer fixture only')
    install=tmp_path/'isolated install';data=tmp_path/'separate data'
    def run(version,*extra):
        (package/'app/version.json').write_text(json.dumps({'version':version}))
        return subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(package/'Install.ps1'),
            '-InstallRoot',str(install),'-NoShortcuts',*extra],capture_output=True,timeout=30)
    assert run('0.3.0-byo','-DataDir',str(data)).returncode==0
    first=json.loads((install/'install.json').read_text(encoding='utf-8-sig'))
    sentinel=data/'preserved.txt';sentinel.write_text('existing device profile')
    assert run('0.3.1-byo').returncode==0
    second=json.loads((install/'install.json').read_text(encoding='utf-8-sig'))
    assert second['version']=='0.3.1-byo' and first['exe']!=second['exe']
    assert second['data_dir']==first['data_dir']==str(data) and sentinel.read_text()=='existing device profile'
    assert Path(first['exe']).is_file() and Path(second['exe']).is_file()
    before=(install/'install.json').read_bytes()
    assert run('0.3.1-byo','-DataDir',str(tmp_path/'wrong profile')).returncode!=0
    assert (install/'install.json').read_bytes()==before
    assert not (tmp_path/'wrong profile').exists()
