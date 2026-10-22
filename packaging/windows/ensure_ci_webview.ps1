$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true') { throw 'This prerequisite installer is for disposable GitHub runners only.' }
$bridgePython = Join-Path $PSScriptRoot '../../.desktop-build/venv/Scripts/python.exe'
$bridgeHasRuntime = & $bridgePython -c 'from desktop_bridge.windows_console import runtime_available; print(int(runtime_available()))'
if ($LASTEXITCODE) { throw 'Runtime detection failed.' }
if ($bridgeHasRuntime.Trim() -eq '1') { Write-Output 'Evergreen WebView2 runtime is already installed.'; exit 0 }
$bridgeBootstrap = Join-Path $env:RUNNER_TEMP 'MicrosoftEdgeWebview2Setup.exe'
Invoke-WebRequest 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' -OutFile $bridgeBootstrap
$bridgeSignature = Get-AuthenticodeSignature -LiteralPath $bridgeBootstrap
if ($bridgeSignature.Status -ne 'Valid' -or $bridgeSignature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation') { throw 'Untrusted runtime bootstrapper.' }
$bridgeRuntimeSetup = Start-Process -FilePath $bridgeBootstrap -ArgumentList '/silent','/install' -Wait -PassThru -WindowStyle Hidden
if ($bridgeRuntimeSetup.ExitCode -ne 0) { throw 'WebView2 runtime setup failed.' }
& $bridgePython -c 'from desktop_bridge.windows_console import runtime_available; assert runtime_available()'
if ($LASTEXITCODE) { throw 'WebView2 runtime is unavailable after setup.' }
