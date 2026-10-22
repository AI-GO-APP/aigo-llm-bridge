param(
    [switch]$AutoStart, [switch]$Launch,
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'AIGO LLM Bridge'),
    [string]$DataDir = '', [switch]$NoShortcuts, [string]$ShortcutDirectory = ''
)
$ErrorActionPreference = 'Stop'
$appRoot = [IO.Path]::GetFullPath($InstallRoot)
$manifestPath = Join-Path $appRoot 'install.json'
$previous = $null
if (Test-Path -LiteralPath $manifestPath) { $previous = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json }
if (-not $DataDir) {
    if ($previous) { $DataDir = $previous.data_dir }
    else { $DataDir = Join-Path $appRoot 'data' }
}
$DataDir = [IO.Path]::GetFullPath($DataDir)
if ($appRoot.Contains('"') -or $DataDir.Contains('"')) { throw 'Paths must not contain double quotes.' }
if ($previous -and -not $DataDir.Equals($previous.data_dir, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Update must preserve the original DataDir. Use another InstallRoot for a new device profile.'
}
$sourceRoot = Join-Path $PSScriptRoot 'app'
if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot 'AIGO-LLM-Bridge.exe'))) { throw 'Installer package is incomplete.' }
$version = '0.2.0-p1'
$versionFile = Join-Path $sourceRoot 'version.json'
if (Test-Path -LiteralPath $versionFile) { $version = (Get-Content -LiteralPath $versionFile -Raw | ConvertFrom-Json).version }
if ($version -notmatch '^[a-zA-Z0-9.-]+$') { throw 'Invalid package version.' }
$releaseRoot = Join-Path $appRoot ('versions\' + $version + '-' + [guid]::NewGuid().ToString('N').Substring(0,12))
New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null
Get-ChildItem -LiteralPath $sourceRoot -Force | Copy-Item -Destination $releaseRoot -Recurse -Force
New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
$exePath = Join-Path $releaseRoot 'AIGO-LLM-Bridge.exe'
$arguments = '--data-dir "' + $DataDir + '"'
if (-not $NoShortcuts) {
    if ($ShortcutDirectory) {
        $ShortcutDirectory = [IO.Path]::GetFullPath($ShortcutDirectory)
        New-Item -ItemType Directory -Path $ShortcutDirectory -Force | Out-Null
        $shortcutPaths = @((Join-Path $ShortcutDirectory 'LLM Bridge.lnk'))
    } else {
        $shortcutPaths = @((Join-Path ([Environment]::GetFolderPath('Desktop')) 'LLM Bridge.lnk'),
                          (Join-Path ([Environment]::GetFolderPath('Programs')) 'LLM Bridge.lnk'))
    }
    $shell = New-Object -ComObject WScript.Shell
    foreach ($path in $shortcutPaths) {
        $shortcut = $shell.CreateShortcut($path)
        $shortcut.TargetPath = $exePath
        $shortcut.Arguments = $arguments
        $shortcut.WorkingDirectory = $releaseRoot
        $shortcut.Save()
    }
}
$runPath = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$registered = (Get-ItemProperty -LiteralPath $runPath -Name 'AigoLlmBridge' -ErrorAction SilentlyContinue).AigoLlmBridge
$ownedStartup = $registered -and $registered.StartsWith('"' + $appRoot + '\', [StringComparison]::OrdinalIgnoreCase)
if ($AutoStart -or $ownedStartup) {
    $defaultRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'AIGO LLM Bridge'))
    if ($registered -and -not $ownedStartup -and -not $appRoot.Equals($defaultRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Another installation owns startup. It was not replaced.' }
    New-ItemProperty -Path $runPath -Name 'AigoLlmBridge' -Value ('"' + $exePath + '" ' + $arguments + ' --background') -PropertyType String -Force | Out-Null
}
@{version=$version; exe=$exePath; data_dir=$DataDir; install_root=$appRoot} | ConvertTo-Json | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Output ('Installed: ' + $exePath)
Write-Output ('Data: ' + $DataDir)
if ($Launch) { Start-Process -FilePath $exePath -ArgumentList $arguments -WindowStyle Hidden }
