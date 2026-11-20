param([ValidateSet('success', 'recovery', 'exhaustion', 'missing')][string]$Case)
$ErrorActionPreference = 'Stop'
$global:monitorTestStarts = 0
$global:monitorTestSleeps = 0
function Test-Path {
    param($LiteralPath)
    if ($Case -eq 'missing') { return $false }
    Microsoft.PowerShell.Management\Test-Path -LiteralPath $LiteralPath
}
function Start-Process {
    param($FilePath, $ArgumentList, $WorkingDirectory, $WindowStyle,
        [switch]$Wait, [switch]$PassThru, $RedirectStandardOutput, $RedirectStandardError)
    $global:monitorTestStarts++
    if ($WindowStyle -ne 'Hidden' -or -not $Wait -or -not $PassThru -or
        $ArgumentList -notlike '*jira_monitor.py" --interval 3600' -or
        $global:monitorTestStarts -gt 4 -or
        $global:monitorTestSleeps -ne ($global:monitorTestStarts - 1)) { throw 'Invalid launch/retry' }
    $monitorTestCode = 7
    if ($Case -eq 'success' -or ($Case -eq 'recovery' -and $global:monitorTestStarts -eq 2)) {
        $monitorTestCode = 0
    }
    Write-Host ('SELF_CHECK: case={0} start={1} sleeps={2} exit={3}' -f
        $Case, $global:monitorTestStarts, $global:monitorTestSleeps, $monitorTestCode)
    [pscustomobject]@{ExitCode=$monitorTestCode}
}
function Start-Sleep {
    param($Seconds)
    if ($Seconds -ne 60) { throw 'Incorrect recovery delay' }
    $global:monitorTestSleeps++
}
& (Join-Path (Split-Path -Parent $PSScriptRoot) 'tools\Start-JiraMonitor.ps1')
exit $LASTEXITCODE
