[CmdletBinding()]
param([switch]$Run)
$ErrorActionPreference = 'Stop'
$taskName = 'QLDAPM-NaturalSchedule-Observation'
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if ($Run) {
    Push-Location $PSScriptRoot
    try { & $python -m automation.natural_schedule_observation --due; exit $LASTEXITCODE }
    finally { Pop-Location }
}
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) { throw 'OBSERVATION_TASK_EXISTS_INSPECT_FIRST' }
$planPath = Join-Path $env:LOCALAPPDATA 'QLDAPM\openproject-ai\operator\natural-schedule-observations\plan.json'
$planDoc = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
if (@($planDoc).Count -ne 2) { throw 'TWO_ONE_SHOT_OBSERVATIONS_REQUIRED' }
$triggers = foreach ($item in $planDoc) {
    if ($item.workflow -notin @('WF07','WF12')) { throw 'UNEXPECTED_OBSERVATION_TARGET' }
    $due = [DateTimeOffset]::Parse($item.scheduled_at).LocalDateTime.AddMinutes(5)
    if ($due -le (Get-Date)) { throw 'OBSERVATION_TIME_MUST_BE_FUTURE' }
    New-ScheduledTaskTrigger -Once -At $due
}
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$powershell = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$action = New-ScheduledTaskAction -Execute $powershell -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -File "' + $PSCommandPath + '" -Run') -WorkingDirectory $PSScriptRoot
$principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 3) -Hidden
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Principal $principal -Settings $settings -Description 'Two one-shot read-only checks of natural Main daily/weekly executions; no workflow invocation, mutation, restart or daemon.' | Select-Object TaskName,State
