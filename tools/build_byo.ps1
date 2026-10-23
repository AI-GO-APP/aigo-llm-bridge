param([string]$BuildDependencies = '.desktop-build/tools')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$env:PYTHONPATH = (Join-Path $projectRoot $BuildDependencies)
python -m PyInstaller --noconfirm --windowed --name AIGO-LLM-Bridge --onedir --distpath dist/byo --workpath .desktop-build/pyinstaller-byo --specpath .desktop-build/spec-byo --paths . --add-data "$(Join-Path $projectRoot 'desktop_bridge/web');desktop_bridge/web" --exclude-module pytest --exclude-module jsonschema.tests --exclude-module referencing.tests desktop_bridge/launcher.py
if ($LASTEXITCODE -ne 0) { throw 'Bridge build failed.' }
python -m PyInstaller --noconfirm --console --name AIGO-Bridge-Setup --onedir --distpath dist/byo-setup --workpath .desktop-build/pyinstaller-byo-setup --specpath .desktop-build/spec-byo-setup --paths . --exclude-module pytest desktop_bridge/setup_launcher.py
if ($LASTEXITCODE -ne 0) { throw 'BYO setup build failed.' }
$packageRoot = Join-Path $projectRoot 'dist/AIGO-LLM-Bridge-BYO'
$appRoot = Join-Path $packageRoot 'app'
New-Item -ItemType Directory -Path $appRoot -Force | Out-Null
Copy-Item -LiteralPath installer/windows/Install.cmd -Destination $packageRoot -Force
$installer = Get-Content -LiteralPath installer/windows/Install.ps1 -Raw
$installer | Set-Content -LiteralPath (Join-Path $packageRoot 'Install.ps1') -Encoding utf8
$version = python -c "from desktop_bridge import __version__; print(__version__)"
if ($LASTEXITCODE -ne 0) { throw 'Cannot read package version.' }
@{version=$version.Trim()} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $appRoot 'version.json') -Encoding utf8
Get-ChildItem -LiteralPath dist/byo/AIGO-LLM-Bridge -Force | Copy-Item -Destination $appRoot -Recurse -Force
$setupRoot = Join-Path $appRoot 'BYO-Setup'
New-Item -ItemType Directory -Path $setupRoot -Force | Out-Null
Get-ChildItem -LiteralPath dist/byo-setup/AIGO-Bridge-Setup -Force | Copy-Item -Destination $setupRoot -Recurse -Force
# Reuse the native installer's curated, tracked and commit-pinned documentation.
$documentStage = Join-Path $projectRoot '.desktop-build/byo-document-stage'
python packaging/windows/build_resources.py --stage $documentStage
if ($LASTEXITCODE -ne 0) { throw 'Cannot stage tracked package documentation.' }
Get-ChildItem -LiteralPath (Join-Path $documentStage 'documents') -Force | Copy-Item -Destination $appRoot -Recurse -Force
New-Item -ItemType Directory -Path (Join-Path $appRoot 'cloudflare/src') -Force | Out-Null
Copy-Item -LiteralPath cloudflare/src/worker.js -Destination (Join-Path $appRoot 'cloudflare/src') -Force
Copy-Item -LiteralPath cloudflare/wrangler.jsonc -Destination (Join-Path $appRoot 'cloudflare') -Force
# Root entrypoints link to the maintained guides instead of copying their relative links.
'# Agent setup (legacy ZIP)

Read [the agent prompt](app/docs/AI-AGENT-SETUP.md) and [app/AGENTS.md](app/AGENTS.md). This archive uses Install.ps1 and BYO-Setup, not the newer Velopack layout.' | Set-Content -LiteralPath (Join-Path $packageRoot 'AGENT-SETUP.md') -Encoding utf8
'# User guide (legacy ZIP)

Read [BYO setup](app/docs/BYO-QUICKSTART.md) and [the product index](app/docs/README.md). Use the legacy ZIP section for this archive; the newer Setup installer is a separate product path.' | Set-Content -LiteralPath (Join-Path $packageRoot 'USER-GUIDE.md') -Encoding utf8
'This package uses installer-owned BYO Cloudflare. Read app/AGENTS.md and app/skills/byo-cloudflare/SKILL.md. Work from app/; the native setup CLI is BYO-Setup/AIGO-Bridge-Setup.exe. There is no publisher-managed endpoint.' | Set-Content -LiteralPath (Join-Path $packageRoot 'AGENTS.md') -Encoding utf8
'Read AGENTS.md and app/AGENTS.md before setup. Use installer-owned BYO Cloudflare.' | Set-Content -LiteralPath (Join-Path $packageRoot 'CLAUDE.md') -Encoding utf8
Compress-Archive -LiteralPath $packageRoot -DestinationPath dist/AIGO-LLM-Bridge-BYO-Windows.zip -Force
python -c "import hashlib; from pathlib import Path; print(hashlib.sha256(Path('dist/AIGO-LLM-Bridge-BYO-Windows.zip').read_bytes()).hexdigest())"
if ($LASTEXITCODE -ne 0) { throw 'Cannot verify ZIP checksum.' }
