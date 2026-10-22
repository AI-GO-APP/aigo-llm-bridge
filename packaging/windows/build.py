"""Build the Windows BYO native installer without altering macOS packaging."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from desktop_bridge import __version__


def build():
    version=(ROOT/'VERSION').read_text(encoding='utf-8-sig').strip()
    if __version__!=version:raise ValueError('Windows runtime version differs from VERSION')
    subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'tools/build_byo.ps1')],cwd=ROOT,check=True)
    output=ROOT/'dist/windows';output.mkdir(parents=True,exist_ok=True)
    package=output/f'aigo-llm-bridge-windows-{version}.zip'
    shutil.copyfile(ROOT/'dist/AIGO-LLM-Bridge-BYO-Windows.zip',package)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    sha=hashlib.sha256(package.read_bytes()).hexdigest()
    manifest={'target':'windows','version':version,'commit':commit,'dirty':dirty,
              'package':package.name,'size':package.stat().st_size,'sha256':sha,
              'format':'windows-native-byo','requires_python':False,'requires_node_for_deploy':'>=22',
              'signed':False}
    (output/'windows-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (output/(package.name+'.sha256')).write_text(sha+'  '+package.name+'\n',encoding='ascii')
    return package


if __name__=='__main__':print(build())
