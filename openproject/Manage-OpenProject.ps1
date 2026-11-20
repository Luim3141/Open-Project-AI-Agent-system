[CmdletBinding()]
param(
    [ValidateSet('Setup','Start','Stop','Status','Backup','Restore','Verify')][string]$Action = 'Status',
    [switch]$LocalOnly,
    [string]$BackupPath,
    [switch]$ReplaceLocalData,
    [switch]$KeepStopped
)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$runtime = Join-Path $env:LOCALAPPDATA 'QLDAPM/openproject'
$envFile = Join-Path $runtime '.env'
$composeFile = Join-Path $root 'compose.yml'
$project = 'qldapm-openproject'
$gate = Join-Path $runtime 'gate/maintenance'
function Compose {
    $files = @('-f', $composeFile)
    $active = Join-Path $runtime 'active-volumes.yml'
    if ($project -eq 'qldapm-openproject' -and (Test-Path -LiteralPath $active)) { $files += @('-f', $active) }
    $bridge = Join-Path $runtime 'ui-bridge.yml'
    if ($project -eq 'qldapm-openproject' -and (Test-Path -LiteralPath $bridge)) { $files += @('-f', $bridge) }
    & docker compose --project-name $project --env-file $envFile @files @args
    if ($LASTEXITCODE -ne 0) { throw 'Docker Compose operation failed.' }
}
function Set-Runtime([hashtable]$Values) {
    $lines = [IO.File]::ReadAllLines($envFile)
    $lines = foreach ($line in $lines) {
        $key = $line.Split('=',2)[0]
        if ($Values.ContainsKey($key)) { "$key=$($Values[$key])" } else { $line }
    }
    [IO.File]::WriteAllLines($envFile, [string[]]$lines, [Text.UTF8Encoding]::new($false))
}
function Wait-Web {
    for ($i=0; $i -lt 120; $i++) {
        $id = @(Compose ps -q web)[0]
        if ($id) {
            $health = & docker inspect --format '{{.State.Health.Status}}' $id
            if ($health -eq 'healthy') { return }
        }
        Start-Sleep -Seconds 3
    }
    throw 'OpenProject web did not become healthy; maintenance remains enabled.'
}
function Maintenance { [IO.File]::WriteAllText($gate, 'maintenance') }
function Protect-Directory([string]$Path) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    & icacls $Path /inheritance:r /grant:r "${identity}:(OI)(CI)F" 'SYSTEM:(OI)(CI)F' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Cannot protect runtime directory.' }
}
function Check-Python { & python --version; if ($LASTEXITCODE -ne 0) { throw 'Python 3 required.' } }

& docker info --format '{{.ServerVersion}}' 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    $desktop = 'C:/Program Files/Docker/Docker/Docker Desktop.exe'
    if (-not (Test-Path -LiteralPath $desktop)) { throw 'Docker Desktop is not installed.' }
    Start-Process -FilePath $desktop -WindowStyle Hidden
    for ($i=0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 3
        & docker info --format '{{.ServerVersion}}' 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
    }
    if ($LASTEXITCODE -ne 0) { throw 'Docker engine not ready.' }
}
Protect-Directory $runtime
if (-not $env:QLDAPM_RELEASE_OPERATION) {
    $releaseLease = Join-Path $runtime 'release.lock'
    if (Test-Path -LiteralPath $releaseLease) {
        try { $leaseCheck=[IO.File]::Open($releaseLease,'Open','ReadWrite','None'); $leaseCheck.Dispose() }
        catch { throw 'An approved release is in progress; retry after it completes.' }
    }
}
$lock = $null
try {
    $lock = [IO.File]::Open((Join-Path $runtime 'operator.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
    if ($Action -eq 'Setup') {
        Check-Python
        $upstreamLock = Get-Content (Join-Path $root 'upstream-lock.json') -Raw | ConvertFrom-Json
        foreach ($name in @('openproject','compose')) {
            $path = Join-Path $root "upstream/$name"
            $record = $upstreamLock.$name
            if (-not (Test-Path -LiteralPath $path)) {
                $ref = if ($name -eq 'openproject') { $record.tag } else { $record.branch }
                & git clone --depth 1 --branch $ref $record.repository $path
                if ($LASTEXITCODE -ne 0) { throw "Clone failed: $name" }
            }
            $commit = & git -C $path rev-parse HEAD
            if ($commit -ne $record.commit) { throw "Upstream commit mismatch: $name. Review lock before proceeding." }
        }
        $listener = Get-NetTCPConnection -LocalPort 18088 -State Listen -ErrorAction SilentlyContinue
        $ownProxy = & docker ps --filter 'label=com.docker.compose.project=qldapm-openproject' --filter 'label=com.docker.compose.service=proxy' --format '{{.ID}}'
        if ($listener -and -not $ownProxy) { throw 'Port 18088 is occupied by another service.' }
        $images = @('openproject/openproject:17.9.1-slim','postgres:17','memcached:1.6-alpine',
                    'caddy:2-alpine','openproject/hocuspocus:17.9.1','cloudflare/cloudflared:2026.10.0')
        foreach ($image in $images) {
            & docker image inspect $image --format '{{.Id}}' 2>$null | Out-Null
            if ($LASTEXITCODE -ne 0) { & docker pull $image; if ($LASTEXITCODE -ne 0) { throw "Pull failed: $image" } }
        }
        & python (Join-Path $root 'scripts/initialize.py') $runtime (Join-Path (Split-Path $root) 'Jira_WBS_QAG3_v7_DRAFT.csv')
        if ($LASTEXITCODE -ne 0) { throw 'Runtime initialization failed.' }
        Compose config --quiet
        Maintenance
        Compose up -d db cache seeder proxy
        Compose up -d web worker cron hocuspocus
        Wait-Web
        if (-not (Test-Path (Join-Path $runtime 'bootstrap.json'))) {
            Compose run --rm --no-deps -v "${runtime}:/private" web bundle exec rails runner /qldapm/bootstrap.rb
        }
        Remove-Item -LiteralPath $gate -ErrorAction SilentlyContinue
        & python (Join-Path $root 'scripts/import_wbs.py') $runtime
        if ($LASTEXITCODE -ne 0) { Maintenance; throw 'Import failed; retained mapping permits reconciliation.' }
        if (-not (Test-Path (Join-Path $runtime 'board-initialized.json'))) {
            Compose run --rm --no-deps -v "${runtime}:/private" web bundle exec rails runner /qldapm/finish_import.rb
        }
        Write-Host 'Setup complete. Run Start to obtain a protected public URL.'
        return
    }
    if (-not (Test-Path -LiteralPath $envFile)) { throw 'Run -Action Setup first.' }
    switch ($Action) {
        'Status' { Compose --profile public ps; if (Test-Path (Join-Path $runtime 'current-url.txt')) { Get-Content (Join-Path $runtime 'current-url.txt') } }
        'Stop' { Compose --profile public stop; Write-Host 'Only qldapm-openproject stopped. Volumes preserved.' }
        'Verify' {
            Check-Python
            & python (Join-Path $root 'scripts/import_wbs.py') $runtime --verify-only
            if ($LASTEXITCODE -ne 0) { throw 'Verification failed.' }
        }
        'Start' {
            Maintenance
            Compose --profile public stop tunnel
            Set-Runtime @{OP_HOST='127.0.0.1:18088';OP_HTTPS='false';PROXY_SCHEME='http';COLLABORATIVE_URL='ws://127.0.0.1:18088/hocuspocus'}
            Compose up -d db cache web worker cron hocuspocus proxy
            Wait-Web
            $url = 'http://127.0.0.1:18088'
            if (-not $LocalOnly) {
                try {
                    Compose --profile public up -d --force-recreate tunnel
                    $hostname = $null
                    for ($i=0; $i -lt 40; $i++) {
                        $logs = (Compose --profile public logs --no-color tunnel 2>&1 | Out-String)
                        $match = [regex]::Match($logs, 'https://([a-z0-9-]+\.trycloudflare\.com)')
                        if ($match.Success) { $hostname = $match.Groups[1].Value; break }
                        Start-Sleep -Seconds 2
                    }
                    if (-not $hostname) { throw 'Protected Quick Tunnel did not return a hostname.' }
                    $url = "https://$hostname"
                    Set-Runtime @{OP_HOST=$hostname;OP_HTTPS='true';PROXY_SCHEME='https';COLLABORATIVE_URL="wss://$hostname/hocuspocus"}
                    Compose up -d web worker cron hocuspocus proxy
                    Wait-Web
                    # Unauthenticated requests must terminate at Cloudflare, not at OpenProject.
                    $handler = [Net.Http.HttpClientHandler]::new()
                    $handler.AllowAutoRedirect = $false
                    $client = [Net.Http.HttpClient]::new($handler)
                    try {
                        $edge = $client.GetAsync("$url/api/v3/projects").GetAwaiter().GetResult()
                        $location = $edge.Headers.Location
                        if ([int]$edge.StatusCode -ne 302 -or -not $location -or $location.Host -ne 'login.trycloudflare.com' -or $location.AbsolutePath -ne '/authorize') {
                            throw 'Protected Quick Tunnel email challenge not verified.'
                        }
                    } finally { $client.Dispose(); $handler.Dispose() }
                } catch {
                    Compose --profile public stop tunnel
                    Maintenance
                    throw
                }
            }
            Remove-Item -LiteralPath $gate -ErrorAction SilentlyContinue
            [IO.File]::WriteAllText((Join-Path $runtime 'current-url.txt'), $url)
            Write-Host "OpenProject ready: $url"
        }
        'Backup' {
            if (-not $BackupPath) { $BackupPath = Join-Path $runtime ('backups/' + (Get-Date -Format 'yyyyMMdd-HHmmss')) }
            if (Test-Path -LiteralPath $BackupPath) { throw 'Backup destination must not exist.' }
            Protect-Directory $BackupPath
            Maintenance
            Compose stop web worker cron hocuspocus
            try {
                Compose run --rm --no-deps -v "${BackupPath}:/backup" web bundle exec rails runner /qldapm/backup_state.rb
                Compose exec -T db pg_dump -U postgres -Fc -f /tmp/qldapm-backup.dump openproject
                Compose cp db:/tmp/qldapm-backup.dump (Join-Path $BackupPath 'database.dump')
                Compose run --rm --no-deps -v "${BackupPath}:/backup" --entrypoint tar web -czf /backup/assets.tar.gz -C /var/openproject/assets .
                $assets = Compose run --rm --no-deps --entrypoint sh web -c 'cd /var/openproject/assets && find . -type f -exec sha256sum {} +'
                [IO.File]::WriteAllText((Join-Path $BackupPath 'assets-sha256.txt'), (($assets | Sort-Object) -join "`n"))
                New-Item -ItemType Directory (Join-Path $BackupPath 'config') | Out-Null
                Get-ChildItem -LiteralPath $runtime -File | Where-Object Name -notin @('operator.lock','release.lock') | Copy-Item -Destination (Join-Path $BackupPath 'config')
                Copy-Item -LiteralPath $composeFile,(Join-Path $root 'Caddyfile') -Destination $BackupPath
                $hashes = Get-ChildItem -LiteralPath $BackupPath -Recurse -File | ForEach-Object {
                    $rel = $_.FullName.Substring($BackupPath.Length).TrimStart('\','/')
                    [pscustomobject]@{Path=$rel;Hash=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
                }
                [IO.File]::WriteAllText((Join-Path $BackupPath 'sha256.json'), ($hashes | ConvertTo-Json))
                Write-Host "Backup complete: $BackupPath"
            } finally {
                if (-not $KeepStopped) {
                    Compose up -d --no-deps web worker cron hocuspocus
                    Wait-Web
                    Remove-Item -LiteralPath $gate -ErrorAction SilentlyContinue
                }
            }
        }
        'Restore' {
            if (-not $BackupPath) { throw 'Specify -BackupPath.' }
            $BackupPath = (Resolve-Path -LiteralPath $BackupPath).Path
            foreach ($hash in (Get-Content (Join-Path $BackupPath 'sha256.json') -Raw | ConvertFrom-Json)) {
                $relative = $hash.Path
                if ($relative.StartsWith('..') -or [IO.Path]::IsPathRooted($relative)) { throw 'Backup manifest escapes destination.' }
                if ((Get-FileHash -LiteralPath (Join-Path $BackupPath $relative)).Hash -ne $hash.Hash) { throw "Backup hash mismatch: $relative" }
            }
            $project = 'qldapm-openproject-restore-' + (Get-Date -Format 'yyyyMMddHHmmss')
            $envFile = Join-Path $BackupPath 'config/.env'
            Compose up -d db cache
            try {
                for ($i=0; $i -lt 40; $i++) {
                    $id = @(Compose ps -q db)[0]
                    $health = & docker inspect --format '{{.State.Health.Status}}' $id
                    if ($health -eq 'healthy') { break }
                    Start-Sleep -Seconds 2
                }
                if ($health -ne 'healthy') { throw 'Restore database not healthy.' }
                Compose cp (Join-Path $BackupPath 'database.dump') db:/tmp/qldapm-restore.dump
                Compose exec -T db pg_restore -U postgres --exit-on-error --no-owner -d openproject /tmp/qldapm-restore.dump
                Compose run --rm --no-deps -v "${BackupPath}:/backup:ro" --entrypoint tar web -xzf /backup/assets.tar.gz -C /var/openproject/assets
                $assets = Compose run --rm --no-deps --entrypoint sh web -c 'cd /var/openproject/assets && find . -type f -exec sha256sum {} +'
                if ((($assets | Sort-Object) -join "`n") -ne [IO.File]::ReadAllText((Join-Path $BackupPath 'assets-sha256.txt'))) { throw 'Restored assets hash mismatch.' }
                Compose run --rm --no-deps -e VERIFY_BACKUP=true -v "${BackupPath}:/backup:ro" web bundle exec rails runner /qldapm/backup_state.rb
                Write-Host "Restore verified in isolated stack: $project. No public ports or tunnel; volumes retained."
            } finally { Compose stop }
            if ($ReplaceLocalData) {
                $restoredProject = $project
                $project = 'qldapm-openproject'
                $envFile = Join-Path $runtime '.env'
                Maintenance
                Compose --profile public stop
                $previous = Join-Path $runtime ('pre-restore-config/' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
                Protect-Directory $previous
                Get-ChildItem -LiteralPath $runtime -File | Where-Object Name -notin @('operator.lock','release.lock') | Copy-Item -Destination $previous
                Get-ChildItem -LiteralPath (Join-Path $BackupPath 'config') -File |
                    Where-Object Name -notin @('operator.lock','release.lock','active-volumes.yml','current-url.txt') | Copy-Item -Destination $runtime
                $override = "volumes:`n  pgdata:`n    external: true`n    name: ${restoredProject}_pgdata`n  opdata:`n    external: true`n    name: ${restoredProject}_opdata`n"
                [IO.File]::WriteAllText((Join-Path $runtime 'active-volumes.yml'), $override)
                Remove-Item -LiteralPath (Join-Path $runtime 'current-url.txt') -ErrorAction SilentlyContinue
                Set-Runtime @{OP_HOST='127.0.0.1:18088';OP_HTTPS='false';PROXY_SCHEME='http';COLLABORATIVE_URL='ws://127.0.0.1:18088/hocuspocus';RUNTIME_DIR=$runtime.Replace('\','/')}
                Write-Host "Restored volumes selected. Old volumes and configuration remain recoverable at $previous. Run Start to resume."
            }
        }
    }
} finally { if ($lock) { $lock.Dispose() } }
