import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH).parents[1]
stage = Path(os.environ['BRIDGE_WINDOWS_STAGE'])
datas = [(str(stage/'web'), 'desktop_bridge/web'),
         (str(stage/'windows-release.json'), '.'),
         (str(root/'cloudflare/src/worker.js'), 'cloudflare/src'),
         (str(root/'cloudflare/wrangler.jsonc'), 'cloudflare'),
         (str(root/'AGENTS.md'), '.'), (str(root/'CLAUDE.md'), '.'),
         (str(root/'skills/byo-cloudflare/SKILL.md'), 'skills/byo-cloudflare')]
for name in ['BYO-QUICKSTART.md','DEVICE-IDENTITY.md','AI-AGENT-SETUP.md','P1-Windows-guide.md',
             'OPENROUTER-PRICING.md','THIRD-PARTY-INTEGRATION.md','AI-EA-CLOUD-BEST-PRACTICE.md',
             'CROSS-PLATFORM-INSTALL.md','WINDOWS-INSTALL-UPDATE.md']:
    datas.append((str(root/'docs'/name),'docs'))
# Only this committed anonymous acceptance report; never include a reports tree.
datas.append((str(root/'docs/qa/2026-10-22-windows-velopack-acceptance.md'),'docs/qa'))
datas += collect_data_files('jsonschema_specifications') + collect_data_files('velopack')
a = Analysis([str(root/'packaging/windows/entry.py')], pathex=[str(root)], datas=datas,
    hiddenimports=['desktop_bridge.__main__','desktop_bridge.windows_cli','desktop_bridge.windows_management',
                   'desktop_bridge.windows_updates','tkinter'], excludes=['pytest','IPython'], noarchive=False)
pyz = PYZ(a.pure)
gui = EXE(pyz,a.scripts,[],exclude_binaries=True,name='AIGO-LLM-Bridge',console=False)
cli = EXE(pyz,a.scripts,[],exclude_binaries=True,name='aigo-bridge',console=True)
bundle = COLLECT(gui,cli,a.binaries,a.datas,strip=False,upx=False,name='AIGO LLM Bridge')
