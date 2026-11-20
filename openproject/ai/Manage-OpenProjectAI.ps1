[CmdletBinding()]
param(
    [ValidateSet('Setup','Start','StartStage','Stop','Status','Register','Revoke','Preview','Approve','Process','Stage','Verify','Qualify','Resolve')]
    [string]$Action = 'Status',
    [switch]$LocalOnly,
    [int]$UserId,
    [string]$Job,
    [string]$Hash
)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$runtime = Join-Path $env:LOCALAPPDATA 'QLDAPM/openproject-ai'
$projectRuntime = Join-Path $env:LOCALAPPDATA 'QLDAPM/openproject'
$python = Join-Path $root '.venv/Scripts/python.exe'
$envFile = Join-Path $runtime '.env'
function Local { & $python (Join-Path $root 'manage_local.py') @args --runtime $runtime; if ($LASTEXITCODE -ne 0) { throw 'Local operation failed.' } }
function Broker { & $python (Join-Path $root 'broker.py') @args --runtime $runtime; if ($LASTEXITCODE -ne 0) { throw 'Broker operation failed; reconcile the actual state before retry.' } }
function Compose {
    $files = @('-f', (Join-Path $root 'compose.yml'))
    if (Test-Path -LiteralPath (Join-Path $runtime 'operator/gemini-main/free-tier-proof.json')) {
        $files += @('-f', (Join-Path $root 'gemini-free.main.yml'))
    }
    & docker compose --project-name qldapm-ai --env-file $envFile @files @args
    if ($LASTEXITCODE -ne 0) { throw 'AI Compose failed.' }
}
function Stage { & docker compose --project-name qldapm-ai-stage --env-file $envFile -f (Join-Path $root 'stage.yml') @args; if ($LASTEXITCODE -ne 0) { throw 'Stage Compose failed.' } }
if ($Action -in @('Setup','Start','StartStage','Stage','Verify','Qualify')) {
    & docker info --format '{{.ServerVersion}}' 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $desktop='C:/Program Files/Docker/Docker/Docker Desktop.exe'
        if (-not (Test-Path -LiteralPath $desktop)) { throw 'Docker Desktop is not installed.' }
        Start-Process -FilePath $desktop -WindowStyle Hidden
        for ($attempt=0;$attempt -lt 60;$attempt++) {
            Start-Sleep -Seconds 3
            & docker info --format '{{.ServerVersion}}' 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { break }
        }
        if ($LASTEXITCODE -ne 0) { throw 'Docker engine not ready; no stack was modified.' }
    }
}
function Wait-Gateway {
    for ($attempt=0; $attempt -lt 40; $attempt++) {
        try { $health=Invoke-RestMethod http://127.0.0.1:18089/health -TimeoutSec 3; if ($health.status -eq 'ok') { return } } catch {}
        Start-Sleep -Seconds 2
    }
    throw 'Gateway did not become healthy.'
}
function Broker-Process {
    $record = Join-Path $runtime 'operator/broker-process.json'
    if (-not (Test-Path -LiteralPath $record)) { return $null }
    $saved = Get-Content -LiteralPath $record -Raw | ConvertFrom-Json
    $process = Get-Process -Id $saved.id -ErrorAction SilentlyContinue
    if ($process -and $process.Path -eq $python -and $process.StartTime.ToUniversalTime().Ticks -eq $saved.started) { return $process }
    return $null
}
function Start-Broker {
    if (Broker-Process) { return }
    Remove-Item -LiteralPath (Join-Path $runtime 'operator/broker.stop') -ErrorAction SilentlyContinue
    $arguments = '"' + (Join-Path $root 'broker.py') + '" watch --runtime "' + $runtime + '"'
    $process = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $root -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtime 'operator/broker-output.log') -RedirectStandardError (Join-Path $runtime 'operator/broker-error.log')
    Start-Sleep -Seconds 1
    if ($process.HasExited) { throw 'Broker could not start; inspect its private operator logs.' }
    @{id=$process.Id;started=$process.StartTime.ToUniversalTime().Ticks} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtime 'operator/broker-process.json')
}
if ($Action -eq 'Setup') {
    New-Item -ItemType Directory -Force -Path $runtime | Out-Null
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    & icacls $runtime /inheritance:r /grant:r "${identity}:(OI)(CI)F" 'SYSTEM:(OI)(CI)F' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Cannot protect AI runtime.' }
    if (-not (Test-Path -LiteralPath $python)) {
        & python -m venv (Join-Path $root '.venv')
        if ($LASTEXITCODE -ne 0) { throw 'Venv creation failed.' }
    }
    & $python -m pip install -r (Join-Path $root 'requirements.lock.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Locked dependency installation failed.' }
    Local initialize --project-runtime $projectRuntime
    & docker build -t qldapm-ai:gateway -f (Join-Path $root 'Dockerfile') $root
    if ($LASTEXITCODE -ne 0) { throw 'Gateway build failed.' }
    & docker build -t qldapm-openproject:17.9.1-gates -f (Join-Path $root 'core/Dockerfile') $root
    if ($LASTEXITCODE -ne 0) { throw 'Core build failed.' }
    Local environment --project-runtime $projectRuntime
    Local workspaces --source (Join-Path (Split-Path $root) 'development/core')
    Compose config --quiet
    Write-Host 'AI setup ready. Core rollout requires the approved release job.'
    return
}
if (-not (Test-Path -LiteralPath $envFile)) { throw 'Run Setup first.' }
switch ($Action) {
    'Register' { Local register --user-id $UserId }
    'Revoke' { Local revoke }
    'Preview' { Broker preview --job $Job }
    'Approve' { Broker approve --job $Job --hash $Hash }
    'Process' {
        if (Broker-Process) { throw 'Broker watcher is running; it processes approved jobs automatically.' }
        Broker process --job $Job
    }
    'Resolve' {
        if (Broker-Process) { throw 'Stop AI broker before local reconciliation.' }
        Broker resolve --job $Job --hash $Hash --offline-state
    }
    'Status' {
        Compose --profile public ps
        $url = Join-Path $runtime 'current-url.txt'
        if (Test-Path -LiteralPath $url) { Get-Content -LiteralPath $url }
    }
    'Stop' {
        Local hosts
        $broker = Broker-Process
        if ($broker) {
            [IO.File]::WriteAllText((Join-Path $runtime 'operator/broker.stop'), 'stop after current job')
            if (-not $broker.WaitForExit(10000)) { throw 'Broker is finishing an active job; retry Stop after completion. No job was killed.' }
        }
        Compose --profile public stop
        Remove-Item -LiteralPath (Join-Path $runtime 'current-url.txt') -ErrorAction SilentlyContinue
        Write-Host 'AI gateway/tunnel stopped; data and workspaces retained.'
    }
    'Start' {
        $listener = Get-NetTCPConnection -LocalPort 18089 -State Listen -ErrorAction SilentlyContinue
        $own = & docker ps --filter 'label=com.docker.compose.project=qldapm-ai' --filter 'label=com.docker.compose.service=gateway' --format '{{.ID}}'
        if ($listener -and -not $own) { throw 'Port 18089 is occupied by another service.' }
        Local hosts
        Compose --profile public stop tunnel
        Compose up -d gateway telegram-ai
        Wait-Gateway
        Start-Broker
        $url = 'http://127.0.0.1:18089'
        if (-not $LocalOnly) {
            try {
                Compose --profile public up -d --force-recreate tunnel
                $hostname=$null
                for ($attempt=0; $attempt -lt 40; $attempt++) {
                    $logs = (Compose --profile public logs --no-color tunnel 2>&1 | Out-String)
                    $match = [regex]::Match($logs,'https://([a-z0-9-]+\.trycloudflare\.com)')
                    if ($match.Success) { $hostname=$match.Groups[1].Value; break }
                    Start-Sleep -Seconds 2
                }
                if (-not $hostname) { throw 'Quick Tunnel did not return a hostname.' }
                Local hosts --host $hostname
                $url = 'https://' + $hostname
                try { Invoke-WebRequest "$url/api/v1/openapi.json" -TimeoutSec 30 | Out-Null; throw 'Anonymous data endpoint unexpectedly returned success.' }
                catch { if ([int]$_.Exception.Response.StatusCode -ne 401) { throw } }
            } catch {
                Local hosts
                Compose --profile public stop tunnel
                throw
            }
        }
        [IO.File]::WriteAllText((Join-Path $runtime 'current-url.txt'), $url)
        Write-Host "AI REST: $url/api/v1 ; MCP: $url/mcp ; Bearer required."
    }
    'StartStage' {
        $stageLock = Get-Content -Raw -LiteralPath (Join-Path $runtime 'stage-image-lock.json') | ConvertFrom-Json
        foreach ($service in @('db','staging-web','staging-gateway')) {
            $name = "qldapm-ai-stage-$service-1"
            $container = ((& docker inspect $name) | ConvertFrom-Json)[0]
            if ($LASTEXITCODE -ne 0 -or $container.Config.Labels.'com.docker.compose.project' -ne 'qldapm-ai-stage' -or
                $container.Image -ne $stageLock.$service) { throw "Staging image/ownership mismatch: $name; no recreate or seeder." }
        }
        & docker start qldapm-ai-stage-db-1 qldapm-ai-stage-staging-web-1 qldapm-ai-stage-staging-gateway-1
        if ($LASTEXITCODE -ne 0) { throw 'Staging start failed; no live changes.' }
        Write-Host 'AI staging: http://localhost:18091/projects/qldapm-local/qldapm-ai'
        Write-Host 'Existing key/provider state retained. Expired Free proof, quota or circuit still blocks Google; no automatic renewal.'
    }
    'Stage' {
        $listener = Get-NetTCPConnection -LocalPort 18091 -State Listen -ErrorAction SilentlyContinue
        $own = & docker ps --filter 'label=com.docker.compose.project=qldapm-ai-stage' --filter 'label=com.docker.compose.service=staging-web' --format '{{.ID}}'
        if ($listener -and -not $own) { throw 'Port 18091 is occupied by another service.' }
        Stage up -d db
        Stage run --rm seeder
        Stage up -d staging-web
        Write-Host 'Stage is isolated at http://127.0.0.1:18091. Use the synthetic bootstrap/import runbook.'
    }
    'Verify' {
        Push-Location $root
        try {
            & $python -m unittest discover -s tests -v
            if ($LASTEXITCODE -ne 0) { throw 'Gateway tests failed.' }
        } finally { Pop-Location }
        Stage exec -T -e QLDAPM_TEST_ONLY=true staging-web bundle exec rails runner /qldapm-core/integration.rb
    }
    'Qualify' {
        if (Broker-Process) { throw 'Stop AI broker first with -Action Stop. Staging must remain running.' }
        & $python (Join-Path $root 'release.py') --runtime $runtime
    }
}
if ($LASTEXITCODE -ne 0) { throw 'AI local operation failed.' }
