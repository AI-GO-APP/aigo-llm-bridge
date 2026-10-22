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
Copy-Item -LiteralPath AGENTS.md,CLAUDE.md -Destination $appRoot -Force
foreach ($folder in @('docs','skills/byo-cloudflare','cloudflare/src')) { New-Item -ItemType Directory -Path (Join-Path $appRoot $folder) -Force | Out-Null }
Copy-Item -LiteralPath docs/BYO-QUICKSTART.md,docs/DEVICE-IDENTITY.md,docs/AI-AGENT-SETUP.md,docs/P1-Windows-guide.md,docs/OPENROUTER-PRICING.md,docs/THIRD-PARTY-INTEGRATION.md,docs/CROSS-PLATFORM-INSTALL.md -Destination (Join-Path $appRoot 'docs') -Force
Copy-Item -LiteralPath skills/byo-cloudflare/SKILL.md -Destination (Join-Path $appRoot 'skills/byo-cloudflare') -Force
Copy-Item -LiteralPath cloudflare/src/worker.js -Destination (Join-Path $appRoot 'cloudflare/src') -Force
Copy-Item -LiteralPath cloudflare/wrangler.jsonc -Destination (Join-Path $appRoot 'cloudflare') -Force
Copy-Item -LiteralPath docs/AI-AGENT-SETUP.md -Destination (Join-Path $packageRoot 'AGENT-SETUP.md') -Force
$userGuide = Get-Content -LiteralPath docs/BYO-QUICKSTART.md -Raw
$userGuide.Replace('(DEVICE-IDENTITY.md)', '(app/docs/DEVICE-IDENTITY.md)').Replace('(P1-Windows-guide.md)', '(app/docs/P1-Windows-guide.md)').Replace('(CROSS-PLATFORM-INSTALL.md)', '(app/docs/CROSS-PLATFORM-INSTALL.md)').Replace('(THIRD-PARTY-INTEGRATION.md)', '(app/docs/THIRD-PARTY-INTEGRATION.md)') | Set-Content -LiteralPath (Join-Path $packageRoot 'USER-GUIDE.md') -Encoding utf8
'This package uses installer-owned BYO Cloudflare. Read app/AGENTS.md and app/skills/byo-cloudflare/SKILL.md. Work from app/; the native setup CLI is BYO-Setup/AIGO-Bridge-Setup.exe. There is no publisher-managed endpoint.' | Set-Content -LiteralPath (Join-Path $packageRoot 'AGENTS.md') -Encoding utf8
'Read AGENTS.md and app/AGENTS.md before setup. Use installer-owned BYO Cloudflare.' | Set-Content -LiteralPath (Join-Path $packageRoot 'CLAUDE.md') -Encoding utf8
Compress-Archive -LiteralPath $packageRoot -DestinationPath dist/AIGO-LLM-Bridge-BYO-Windows.zip -Force
python -c "import hashlib; from pathlib import Path; print(hashlib.sha256(Path('dist/AIGO-LLM-Bridge-BYO-Windows.zip').read_bytes()).hexdigest())"
if ($LASTEXITCODE -ne 0) { throw 'Cannot verify ZIP checksum.' }
