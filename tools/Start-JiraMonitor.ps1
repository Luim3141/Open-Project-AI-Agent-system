$ErrorActionPreference = 'Stop'
$monitorRoot = Split-Path -Parent $PSScriptRoot
$monitorPython = 'C:\Users\LUIM\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$monitorScript = Join-Path $PSScriptRoot 'jira_monitor.py'
$monitorRuntime = Join-Path $monitorRoot 'jira-bot\runtime'
try {
    foreach ($monitorPath in @($monitorPython, $monitorScript, $monitorRuntime)) {
        if (-not (Test-Path -LiteralPath $monitorPath)) { throw 'Required monitor path missing' }
    }
    # Native RestartOnFailure did not relaunch in the live test; bound retries here.
    for ($monitorAttempt = 0; $monitorAttempt -le 3; $monitorAttempt++) {
        $monitorChild = Start-Process -FilePath $monitorPython `
            -ArgumentList ('"{0}" --interval 3600' -f $monitorScript) `
            -WorkingDirectory $monitorRoot -WindowStyle Hidden -Wait -PassThru `
            -RedirectStandardOutput (Join-Path $monitorRuntime 'supervisor.stdout.log') `
            -RedirectStandardError (Join-Path $monitorRuntime 'supervisor.stderr.log')
        if ($monitorChild.ExitCode -eq 0 -or $monitorAttempt -eq 3) { exit $monitorChild.ExitCode }
        Start-Sleep -Seconds 60
    }
} catch {
    Write-Output 'MONITOR_LAUNCH_FAILED: check local paths/storage; no Jira writes occurred.'
    exit 1
}
