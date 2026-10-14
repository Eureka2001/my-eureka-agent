# eureka 网关开机自启：登录触发 + 看门狗重复触发 + 失败自动重启。
#
# 用法（管理员不需要，用户级任务）：
#   powershell -ExecutionPolicy Bypass -File install-task.ps1            # 安装（幂等）
#   powershell -ExecutionPolicy Bypass -File install-task.ps1 -Status    # 查看状态
#   powershell -ExecutionPolicy Bypass -File install-task.ps1 -Uninstall # 卸载
#
# 关键设置的理由：
#   -ExecutionTimeLimit Zero     默认 72h 后强杀常驻任务，必须禁用
#   -MultipleInstances IgnoreNew 看门狗每 10 分钟重复触发，已运行则跳过；
#                                进程死掉/被误杀时下一次触发自动复活
#   -RestartCount 3              崩溃后 1 分钟间隔自动重启
#   -StartWhenAvailable          错过的触发补跑

param(
    [switch]$Uninstall,
    [switch]$Status
)

$ErrorActionPreference = 'Stop'
$TaskName = 'eureka-gateway'
$GatewayDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Pythonw = Join-Path $GatewayDir '.venv\Scripts\pythonw.exe'

if ($Status) {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $task) { Write-Host "[$TaskName] 未安装"; exit 0 }
    $info = $task | Get-ScheduledTaskInfo
    Write-Host "[$TaskName] State=$($task.State) LastResult=$($info.LastTaskResult) LastRun=$($info.LastRunTime)"
    exit 0
}

if ($Uninstall) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "[$TaskName] 已卸载"
    exit 0
}

if (-not (Test-Path $Pythonw)) {
    throw "未找到 $Pythonw；请先在 $GatewayDir 下执行 uv sync"
}

# 幂等：先移除旧任务再注册
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction -Execute $Pythonw `
    -Argument 'server.py --http' -WorkingDirectory $GatewayDir

$logonTrigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$watchdog = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 10) `
    -RepetitionDuration (New-TimeSpan -Days 3650)  # MaxValue 会超出 XML 范围，10 年近似无限

$settings = New-ScheduledTaskSettingsSet `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

Register-ScheduledTask -TaskName $TaskName `
    -Action $action -Trigger $logonTrigger, $watchdog `
    -Settings $settings -Principal $principal `
    -Description 'eureka MCP 网关（127.0.0.1:1820）：聚合本地 MCP server，后台常驻；日志见 mcp/gateway/logs/gateway.log' | Out-Null

Write-Host "[$TaskName] 已安装：登录即启动；每 10 分钟看门狗；崩溃 1 分钟后自动重启"
Write-Host "立即启动：Start-ScheduledTask $TaskName；状态：-Status；卸载：-Uninstall"
