<#
.SYNOPSIS
    Optional Local Backup Scheduler for QLDAPM Local Multi-Agent (User Consent Enforced).
.DESCRIPTION
    Configures or removes an optional scheduled backup task for QLDAPM Local Multi-Agent.
    Strictly zero-secret: never writes credentials, tokens, or passwords to task definitions.
    Relies on private runtime storage (%LOCALAPPDATA%\QLDAPM\openproject-ai).
.PARAMETER Action
    Action to perform: 'Status', 'Enable', 'Disable'. Default is 'Status'.
.PARAMETER Consent
    Switch indicating explicit user consent to register a scheduled task.
#>
[CmdletBinding()]
param(
    [ValidateSet('Status', 'Enable', 'Disable')]
    [string]$Action = 'Status',
    [switch]$Consent
)

$ErrorActionPreference = 'Stop'
$TaskName = 'QLDAPM-Local-Backup'
$PythonExe = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
$BackupScript = Join-Path $PSScriptRoot 'local_backup.py'
$RuntimeDir = Join-Path $env:LOCALAPPDATA 'QLDAPM/openproject-ai'

function Get-TaskStatus {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        return @{
            Registered = $true
            State = $existing.State.ToString()
            TaskName = $TaskName
            NextRunTime = (Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue).NextRunTime
        }
    } else {
        return @{
            Registered = $false
            State = 'NotRegistered'
            TaskName = $TaskName
            NextRunTime = $null
        }
    }
}

if ($Action -eq 'Status') {
    $status = Get-TaskStatus
    Write-Output ($status | ConvertTo-Json -Depth 2)
    exit 0
}

if ($Action -eq 'Disable') {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Scheduled task '$TaskName' successfully unregistered."
    } else {
        Write-Host "Scheduled task '$TaskName' was not registered."
    }
    exit 0
}

if ($Action -eq 'Enable') {
    if (-not $Consent) {
        Write-Error "Explicit user consent is REQUIRED to register a scheduled backup task. Pass -Consent to proceed."
        exit 1
    }

    if (-not (Test-Path -LiteralPath $PythonExe)) {
        Write-Error "Python venv executable not found at: $PythonExe"
        exit 1
    }

    # Action definition: zero credentials in command line or XML definition
    $ActionCmd = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$BackupScript`" snapshot" -WorkingDirectory $PSScriptRoot
    # Trigger: Daily at 02:00 AM (local time)
    $Trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
    # Settings: Do not wake computer, stop if running more than 2 hours
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries:$false -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2)

    Register-ScheduledTask -TaskName $TaskName -Action $ActionCmd -Trigger $Trigger -Settings $Settings -Description "QLDAPM Local Multi-Agent Automated Private Backup (Zero-Secret)" -Force | Out-Null

    Write-Host "Scheduled backup task '$TaskName' registered successfully."
    Write-Host "Emergency restore runbook: Execute 'Test-OpenProjectAIRestore.ps1' or consult docs/ai-multi-agent-upgrade/LOCAL_WINDOWS_RUNBOOK.md."
    exit 0
}
