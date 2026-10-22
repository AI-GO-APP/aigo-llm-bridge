import os
import json
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH).parents[1]
stage = Path(os.environ['BRIDGE_WINDOWS_STAGE'])
datas = [(str(stage/'web'), 'desktop_bridge/web'),
         (str(stage/'windows-release.json'), '.'),
         (str(root/'cloudflare/src/worker.js'), 'cloudflare/src'),
         (str(root/'cloudflare/wrangler.jsonc'), 'cloudflare')]
for name in json.loads((stage/'documents.json').read_text(encoding='utf-8')):
    datas.append((str(stage/'documents'/name), str(Path(name).parent)))
datas += collect_data_files('jsonschema_specifications') + collect_data_files('velopack') + collect_data_files('webview')
a = Analysis([str(root/'packaging/windows/entry.py')], pathex=[str(root)], datas=datas,
    hiddenimports=['desktop_bridge.__main__','desktop_bridge.windows_cli','desktop_bridge.windows_management',
                   'desktop_bridge.windows_updates','desktop_bridge.windows_console','desktop_bridge.windows_console_probe','webview.platforms.winforms',
                   'webview.platforms.edgechromium','clr_loader','pythonnet','tkinter'],
    excludes=['pytest','IPython','PyQt5','PyQt6','PySide2','PySide6','cefpython3'], noarchive=False)
pyz = PYZ(a.pure)
gui = EXE(pyz,a.scripts,[],exclude_binaries=True,name='AIGO-LLM-Bridge',console=False)
cli = EXE(pyz,a.scripts,[],exclude_binaries=True,name='aigo-bridge',console=True)
bundle = COLLECT(gui,cli,a.binaries,a.datas,strip=False,upx=False,name='AIGO LLM Bridge')
