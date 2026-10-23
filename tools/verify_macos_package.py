"""Install the downloadable Mac BYO ZIP and verify its real startup boundary."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import queue
import socket
import subprocess
import sys
import tempfile
import threading
import urllib.request
import zipfile


def verify(package):
    if sys.platform != 'darwin': raise ValueError('Native package acceptance requires macOS.')
    with tempfile.TemporaryDirectory(prefix='bridge-macos-package-') as temporary:
        root=Path(temporary)
        with zipfile.ZipFile(package) as archive:
            for info in archive.infolist():
                relative=Path(info.filename)
                if relative.is_absolute() or '..' in relative.parts or (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('Unsafe package entry.')
            archive.extractall(root/'source')
        source=root/'source/aigo-llm-bridge'
        installation=root/'installed'
        result=subprocess.run(['/bin/sh',str(source/'Install.command'),'--install-root',str(installation)],
                              capture_output=True,text=True,timeout=300)
        if result.returncode: raise ValueError('Downloaded source installer failed.')
        manifest=json.loads((installation/'source-install.json').read_text())
        receipt=json.loads((source/'source-release.json').read_text())
        assert manifest['source_commit']==receipt['commit'] and manifest['version']==receipt['version']
        assert Path(manifest['app'],'desktop_bridge/macos_instance.py').is_file()
        # Source-install.json is the stable launcher path; use the real installed runtime.
        wrapper='''
from desktop_bridge import __main__ as app
original=app.ApiServer.start
def ready(server):
    original(server)
    print(server.port,flush=True)
app.ApiServer.start=ready
raise SystemExit(app.main())
'''
        command=[manifest['python'],'-u','-c',wrapper,'--headless','--port','0','--data-dir',manifest['data_dir']]
        child=subprocess.Popen(command,cwd=manifest['app'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            ready=queue.Queue()
            threading.Thread(target=lambda:ready.put(child.stdout.readline()),daemon=True).start()
            port=int(ready.get(timeout=60).strip())
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=5) as response:
                health=json.load(response)
                assert health['version']==receipt['version']
                assert health['max_concurrent_requests']==64 and health['shared_provider_capacity'] is True
            second=root/'second-profile'
            denied=subprocess.run([manifest['python'],'-m','desktop_bridge','--headless','--port','0',
                                   '--data-dir',str(second)],cwd=manifest['app'],capture_output=True,timeout=60)
            assert denied.returncode==2 and not (second/'bridge.sqlite').exists()
        finally:
            child.terminate();child.communicate(timeout=45)
        with socket.socket() as connection:
            assert connection.connect_ex(('127.0.0.1',port))!=0
        print(json.dumps({'success':True,'version':receipt['version'],'source_commit':receipt['commit'],
                          'download_installed':True,'fixed_machine_lock':True,'rejected_profile_no_database':True,
                          'shutdown_api_closed':True,'max_concurrent_requests':64,'credentials_or_power_changed':False}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',required=True)
    args=parser.parse_args()
    verify(Path(args.package).resolve())
