param(
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$InstallDir,
    [switch]$Uninstall
)
$ErrorActionPreference = 'Stop'
$taskName = 'aigo-llm-bridge-desktop'
if ($Uninstall) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        Stop-ScheduledTask -TaskName $taskName
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
    return
}
# 以 PowerShell 啟動檔保留含空白與 Unicode 的完整路徑,金鑰不寫進排程。
$launcher = Join-Path $InstallDir 'serve.ps1'
$escapedHome = $InstallDir.Replace("'", "''")
$escapedPython = $Python.Replace("'", "''")
@"
`$env:AIGO_DESKTOP_HOME = '$escapedHome'
`$env:PYTHONUNBUFFERED = '1'
& '$escapedPython' '$escapedHome\aigo_desktop.py' serve >> '$escapedHome\service.log' 2>&1
exit `$LASTEXITCODE
"@ | Set-Content -LiteralPath $launcher -Encoding UTF8
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$launcher`"" -WorkingDirectory $InstallDir
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -User $user -RunLevel Limited -Force | Out-Null
Start-ScheduledTask -TaskName $taskName
Write-Output '已啟動。登入後會自動執行。'
