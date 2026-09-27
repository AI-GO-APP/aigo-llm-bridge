<#
Windows:用「工作排程器」讓 worker 在你登入後自動啟動、異常結束自動重啟。

  安裝:powershell -ExecutionPolicy Bypass -File install-windows-task.ps1
  移除:powershell -ExecutionPolicy Bypass -File install-windows-task.ps1 -Uninstall
  查看:Get-Content "$env:USERPROFILE\.aigo-llm-bridge\worker.log" -Wait -Tail 20

只為目前的使用者建立工作(不需要系統管理員)。先完成 `python aigo_bridge_worker.py enroll ...` 再裝。
結束碼 0 = 正常結束或這台電腦已被撤銷 → 不重啟;其他 → 1 分鐘後重啟。
#>
param(
    [string]$Worker = (Join-Path $PSScriptRoot "..\aigo_bridge_worker.py"),
    [string]$Python = "",
    [string]$Claude = "",
    [string]$TaskName = "aigo-llm-bridge-worker",
    [switch]$Uninstall
)
$ErrorActionPreference = "Stop"

if ($Uninstall) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Output "已移除工作 $TaskName"
    return
}

$Worker = (Resolve-Path $Worker).Path
if (-not $Python) { $Python = (Get-Command python -ErrorAction Stop).Source }
if (-not $Claude) {
    # 直接找 claude.exe:npm 安裝的 claude.cmd 殼會重新解析引號,worker 也是這樣處理
    $cmd = Get-Command claude -ErrorAction Stop
    $Claude = $cmd.Source
    if ($Claude -like "*.cmd") {
        $exe = Get-ChildItem -Path (Split-Path $Claude) -Recurse -Filter claude.exe -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($exe) { $Claude = $exe.FullName }
    }
}

$home_dir = if ($env:AIGO_BRIDGE_WORKER_HOME) { $env:AIGO_BRIDGE_WORKER_HOME } else { Join-Path $env:USERPROFILE ".aigo-llm-bridge" }
New-Item -ItemType Directory -Force -Path $home_dir | Out-Null
$log = Join-Path $home_dir "worker.log"

# 工作排程器不能直接設環境變數,所以產生一個小的啟動檔
$launcher = Join-Path $home_dir "run-worker.cmd"
@(
    "@echo off",
    "set AIGO_BRIDGE_CLAUDE=$Claude",
    "set PYTHONUNBUFFERED=1",
    "set PYTHONIOENCODING=utf-8",
    "`"$Python`" `"$Worker`" run >> `"$log`" 2>&1",
    "exit /b %ERRORLEVEL%"
) | Set-Content -Path $launcher -Encoding ASCII

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$launcher`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
    -Description "aigo-llm-bridge worker: runs your own Claude Code for your own jobs" -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
Write-Output "已建立並啟動工作 $TaskName"
Write-Output "  worker : $Worker"
Write-Output "  claude : $Claude"
Write-Output "  紀錄檔 : $log"
