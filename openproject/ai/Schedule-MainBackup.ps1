[CmdletBinding()]
param([switch]$Run)
$ErrorActionPreference = 'Stop'
$taskName = 'QLDAPM-Main-Daily-Backup'
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'MAIN_BACKUP_PYTHON_REQUIRED' }
if ($Run) {
    Push-Location $PSScriptRoot
    try { & $python -m automation.main_backup_schedule; exit $LASTEXITCODE }
    finally { Pop-Location }
}
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) { throw 'MAIN_BACKUP_TASK_EXISTS_INSPECT_BEFORE_REPLACING' }
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$powershell = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$action = New-ScheduledTaskAction -Execute $powershell -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -File "' + $PSCommandPath + '" -Run') -WorkingDirectory $PSScriptRoot
$triggers = @(
    (New-ScheduledTaskTrigger -AtLogOn -User $identity),
    (New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 1))
)
$principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 20) -Hidden
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Principal $principal -Settings $settings -Description 'Main-only consistent daily snapshots; hourly due check, preserve existing backups, no automatic restore or replay.' | Select-Object TaskName,State
