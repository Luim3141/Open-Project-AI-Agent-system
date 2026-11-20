$ErrorActionPreference = 'Stop'
$engineeringRoot = 'D:\AI project\QLDAPM chat'
$engineeringLog = Join-Path $env:LOCALAPPDATA 'QLDAPM\openproject-ai\operator\engineering-delivery.log'
Set-Location -LiteralPath $engineeringRoot
# Boot this one distro so its enabled local demo service is available after logon.
# OpenClaw cron/heartbeat and the provider gate remain OFF; this performs no inference.
& wsl.exe -d OpenClawGateway -u openclaw --cd /home/openclaw --exec /usr/bin/true *>> $engineeringLog
& (Join-Path $engineeringRoot 'openproject\ai\.venv\Scripts\python.exe') -B -u (Join-Path $engineeringRoot 'openproject\ai\automation\engineering_worker.py') --watch *>> $engineeringLog
exit $LASTEXITCODE
