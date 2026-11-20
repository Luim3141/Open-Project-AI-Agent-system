[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^sha256:[a-f0-9]{64}$')][string]$Image,
    [Parameter(Mandatory)][ValidatePattern('^sha256:[a-f0-9]{64}$')][string]$GatewayImage,
    [Parameter(Mandatory)][ValidatePattern('^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$')][string]$ReleaseId,
    [Parameter(Mandatory)][ValidatePattern('^[a-f0-9]{64}$')][string]$BeforeHash,
    [Parameter(Mandatory)][ValidatePattern('^[a-f0-9]{64}$')][string]$DeploymentHash,
    [Parameter(Mandatory)][ValidateRange(1,2147483647)][int]$ActorId
)
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$runtime=Join-Path $env:LOCALAPPDATA 'QLDAPM/openproject'
$aiRuntime=Join-Path $env:LOCALAPPDATA 'QLDAPM/openproject-ai'
$envFile=Join-Path $runtime '.env'
$composeFile=Join-Path (Split-Path $root) 'compose.yml'
$manager=Join-Path (Split-Path $root) 'Manage-OpenProject.ps1'
$folder=Join-Path $runtime ('releases/'+$ReleaseId)
$backup=Join-Path $runtime ('backups/release-'+$ReleaseId)
$active=Join-Path $runtime 'active-volumes.yml'
$gate=Join-Path $runtime 'gate/maintenance'
$gatewayConfig=Join-Path $aiRuntime 'gateway/config.json'
$aiEnv=Join-Path $aiRuntime '.env'
$imageLock=Join-Path $aiRuntime 'image-lock.json'
$bridge=Join-Path $runtime 'ui-bridge.yml'
& (Join-Path $root '.venv/Scripts/python.exe') (Join-Path $root 'release.py') --runtime $aiRuntime --check-deployment-hash $DeploymentHash
if($LASTEXITCODE -ne 0){throw 'Approved deployment changed; no live mutation attempted.'}
function Compose {
    $files=@('-f',$composeFile)
    if(Test-Path -LiteralPath $active){$files+=@('-f',$active)}
    if(Test-Path -LiteralPath $bridge){$files+=@('-f',$bridge)}
    & docker compose --project-name qldapm-openproject --env-file $envFile @files @args
    if($LASTEXITCODE -ne 0){throw 'Approved release Compose operation failed.'}
}
function AICompose {
    & docker compose --project-name qldapm-ai --env-file $aiEnv -f (Join-Path $root 'compose.yml') @args
    if($LASTEXITCODE -ne 0){throw 'Approved gateway Compose operation failed.'}
}
function Set-Image([string]$Path,[string]$Key,[string]$Value){
    $lines=[IO.File]::ReadAllLines($Path)
    if(@($lines | Where-Object {$_ -like "$Key=*"}).Count -ne 1){throw 'Exactly one image setting required.'}
    $lines=@($lines | ForEach-Object {if($_.StartsWith($Key+'=')){"$Key=$Value"}else{$_}})
    [IO.File]::WriteAllLines($Path,[string[]]$lines,[Text.UTF8Encoding]::new($false))
}
function Wait-Gateway {
    for($attempt=0;$attempt -lt 40;$attempt++){
        $id=AICompose ps -q gateway
        if($id -and ((& docker inspect --format '{{.State.Health.Status}}' $id) -eq 'healthy')){return}
        Start-Sleep -Seconds 3
    }
    throw 'Gateway unhealthy; maintenance retained.'
}
function Install-UIBridge {
    $mounts=@()
    $keyHashes=@()
    foreach($relative in @('gateway/ui.key','operator/test-receipt.key')){
        $path=Join-Path $aiRuntime $relative
        $file=Get-Item -LiteralPath $path
        if($file.PSIsContainer -or $file.LinkType -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $file.Length -lt 32){throw 'Separate local UI/test receipt keys required.'}
        $keyHashes+=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
        $target=if($relative -eq 'gateway/ui.key'){'ui.key'}else{'test-receipt.key'}
        $mounts+=@{type='bind';source=$file.FullName;target="/qldapm-ui/$target";read_only=$true;bind=@{create_host_path=$false}}
    }
    if($keyHashes[0] -eq $keyHashes[1]){throw 'UI and test receipt signing keys must be independent.'}
    # JSON is valid Compose YAML; literal file paths avoid ambient environment substitutions.
    [IO.File]::WriteAllText($bridge,(@{services=@{web=@{volumes=$mounts}}} | ConvertTo-Json -Depth 10))
}
function Verify-Pair {
    $id=AICompose ps -q gateway
    if((& docker inspect --format '{{.Image}}' $id) -ne $GatewayImage){throw 'Gateway image changed.'}
    Compose exec -T web test -r /qldapm-ui/ui.key
    Compose exec -T web test -r /qldapm-ui/test-receipt.key
    AICompose exec -T gateway python -c @'
import json
from pathlib import Path
from gateway.native import Native
c=json.loads(Path('/state/config.json').read_text()); tokens=json.loads(Path('/state/credentials.json').read_text())
actor=next(int(a) for a in c['users'] if a in tokens)
n=Native(c['openproject_url'],tokens[str(actor)],c['project_id'])
assert n.identity(actor)['role']==c['users'][str(actor)]
p=n.call('/api/v3/qldapm/capabilities')
assert p['project_id']==c['project_id'] and p['gate_schema']==2 and p['enforced'] is True
print('Core/gateway capability PASS')
'@
}
function Gateway-Maintenance([bool]$Enabled){
    $config=Get-Content -LiteralPath $gatewayConfig -Raw | ConvertFrom-Json
    $config.maintenance=$Enabled
    [IO.File]::WriteAllText($gatewayConfig+'.release-tmp',($config | ConvertTo-Json -Depth 10))
    Move-Item -LiteralPath ($gatewayConfig+'.release-tmp') -Destination $gatewayConfig -Force
}
function Wait-Web {
    for($attempt=0;$attempt -lt 120;$attempt++){
        $web=Compose ps -q web
        if($web -and ((& docker inspect --format '{{.State.Health.Status}}' $web) -eq 'healthy')){return}
        Start-Sleep -Seconds 3
    }
    throw 'Candidate unhealthy; maintenance retained.'
}
if(Test-Path -LiteralPath $folder){throw 'Release ID already used; reconcile before another attempt.'}
$lease=[IO.File]::Open((Join-Path $runtime 'release.lock'),'OpenOrCreate','ReadWrite','None')
$operatorLock=$null
$changed=$false
$maintenanceStarted=$false
$gatewayStopped=$false
$gatewaySnapshot=$false
$committed=$false
$previousOperation=$env:QLDAPM_RELEASE_OPERATION
try{
    $env:QLDAPM_RELEASE_OPERATION=$ReleaseId
    New-Item -ItemType Directory -Path $folder | Out-Null
    Copy-Item -LiteralPath $envFile -Destination (Join-Path $folder 'previous.env')
    if(Test-Path -LiteralPath $active){Copy-Item -LiteralPath $active -Destination (Join-Path $folder 'previous-volumes.yml')}
    if(Test-Path -LiteralPath $bridge){Copy-Item -LiteralPath $bridge -Destination (Join-Path $folder 'previous-ui-bridge.yml')}
    Copy-Item -LiteralPath $aiEnv -Destination (Join-Path $folder 'previous-ai.env')
    Copy-Item -LiteralPath $imageLock -Destination (Join-Path $folder 'previous-image-lock.json')
    Gateway-Maintenance $true
    $maintenanceStarted=$true
    [IO.File]::WriteAllText($gate,'approved release maintenance')
    foreach($item in @(Get-Item -LiteralPath (Join-Path $aiRuntime 'gateway'))+@(Get-ChildItem -LiteralPath (Join-Path $aiRuntime 'gateway') -Recurse -Force)){
        if($item.LinkType -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Linked gateway state denied.'}
    }
    AICompose --profile public stop gateway tunnel
    $gatewayStopped=$true
    # Freeze SQLite, credentials and config together; never copy a running WAL database.
    Copy-Item -LiteralPath (Join-Path $aiRuntime 'gateway') -Destination (Join-Path $folder 'previous-gateway') -Recurse
    $gatewaySnapshot=$true
    Compose --profile public stop tunnel
    & $manager -Action Backup -BackupPath $backup -KeepStopped
    $changed=$true
    & $manager -Action Restore -BackupPath $backup -ReplaceLocalData
    $operatorLock=[IO.File]::Open((Join-Path $runtime 'operator.lock'),'OpenOrCreate','ReadWrite','None')
    Compose up -d db cache
    $healthy=$false
    for($attempt=0;$attempt -lt 40;$attempt++){
        $database=Compose ps -q db
        if($database -and ((& docker inspect --format '{{.State.Health.Status}}' $database) -eq 'healthy')){$healthy=$true;break}
        Start-Sleep -Seconds 2
    }
    if(-not $healthy){throw 'Restored database not healthy; no migration attempted.'}
    @{action='inspect';parameters=@{};actor=$ActorId} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $folder 'configuration-request.json')
    Compose run --rm --no-deps -v "${root}/core:/trusted:ro" -v "${folder}:/operator:ro" -e QLDAPM_REQUEST=/operator/configuration-request.json -e "QLDAPM_EXPECTED_CONFIGURATION=$BeforeHash" web bundle exec rails runner /trusted/admin_operation.rb
    # Inspect the frozen original schema with its original image before loading candidate models.
    Install-UIBridge
    Set-Image $envFile 'OP_IMAGE' $Image
    Set-Image $aiEnv 'AI_IMAGE' $GatewayImage
    $images=Get-Content -LiteralPath $imageLock -Raw | ConvertFrom-Json
    $images.CORE_IMAGE=$Image
    $images.AI_IMAGE=$GatewayImage
    [IO.File]::WriteAllText($imageLock,($images | ConvertTo-Json -Depth 10))
    [IO.File]::WriteAllText((Join-Path $aiRuntime 'gateway/gemini.json'),'{"enabled":false}')
    Compose run --rm --no-deps -v "${root}/core:/trusted:ro" web bundle exec rails db:migrate
    Compose run --rm --no-deps -v "${root}/core:/trusted:ro" -v "${runtime}/wbs-snapshot.csv:/private/wbs-snapshot.csv:ro" web bundle exec rails runner /trusted/migrate_snapshot.rb
    Compose run --rm --no-deps -e VERIFY_BACKUP=true -e QLDAPM_COMPARE_SOURCE=true -v "${backup}:/backup:ro" web bundle exec rails runner /qldapm/backup_state.rb
    Compose run --rm --no-deps -v "${root}/core:/trusted:ro" -v "${runtime}/wbs-snapshot.csv:/private/wbs-snapshot.csv:ro" web bundle exec rails runner /trusted/release_verify.rb
    Compose up -d --no-deps web worker cron hocuspocus proxy
    Wait-Web
    $running=Compose ps -q web
    if((& docker inspect --format '{{.Image}}' $running) -ne $Image){throw 'Candidate image changed.'}
    AICompose up -d --no-deps gateway
    Wait-Gateway
    Verify-Pair
    @{image=$Image;gatewayImage=$GatewayImage;releaseId=$ReleaseId;backup=$backup;passed=$true;localOnly=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $folder 'result.json')
    # Once access may open, rollback could discard new writes; fence and reconcile instead.
    $committed=$true
    Remove-Item -LiteralPath $gate
    Gateway-Maintenance $false
    [IO.File]::WriteAllText((Join-Path $runtime 'current-url.txt'),'http://localhost:8088')
    Write-Host "Approved release PASS; old volumes retained. Rollback backup: $backup. UI remains local-only until protected Start."
}catch{
    $failure=$_
    if(-not $maintenanceStarted){throw $failure}
    if($committed){
        [IO.File]::WriteAllText($gate,'candidate selected; reopening failed; operator reconciliation required')
        try{AICompose --profile public stop gateway tunnel; Compose --profile public stop tunnel proxy}catch{Write-Warning 'Access fencing incomplete; operator intervention required.'}
        Gateway-Maintenance $true
        @{releaseId=$ReleaseId;passed=$false;candidateSelected=$true;maintenance=$true;automaticRollbackDenied=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $folder 'result.json')
        throw $failure
    }
    if($operatorLock){$operatorLock.Dispose();$operatorLock=$null}
    try{
        Compose --profile public stop
        if($gatewayStopped){AICompose --profile public stop gateway tunnel}
        Copy-Item -LiteralPath (Join-Path $folder 'previous.env') -Destination $envFile -Force
        Copy-Item -LiteralPath (Join-Path $folder 'previous-ai.env') -Destination $aiEnv -Force
        Copy-Item -LiteralPath (Join-Path $folder 'previous-image-lock.json') -Destination $imageLock -Force
        if($gatewaySnapshot){
            $failedState=Join-Path $folder 'failed-gateway'
            $statePath=[IO.Path]::GetFullPath((Join-Path $aiRuntime 'gateway'))
            $failedState=[IO.Path]::GetFullPath($failedState)
            if($statePath -ne [IO.Path]::GetFullPath($aiRuntime+'/gateway') -or -not $failedState.StartsWith([IO.Path]::GetFullPath($folder)+[IO.Path]::DirectorySeparatorChar)){throw 'Rollback target denied.'}
            Move-Item -LiteralPath $statePath -Destination $failedState
            Copy-Item -LiteralPath (Join-Path $folder 'previous-gateway') -Destination (Join-Path $aiRuntime 'gateway') -Recurse
        }
        if(Test-Path -LiteralPath (Join-Path $folder 'previous-ui-bridge.yml')){
            Copy-Item -LiteralPath (Join-Path $folder 'previous-ui-bridge.yml') -Destination $bridge -Force
        }elseif(Test-Path -LiteralPath $bridge){Remove-Item -LiteralPath $bridge}
        if(Test-Path -LiteralPath (Join-Path $folder 'previous-volumes.yml')){
            Copy-Item -LiteralPath (Join-Path $folder 'previous-volumes.yml') -Destination $active -Force
        }elseif($changed -and (Test-Path -LiteralPath $active)){
            Remove-Item -LiteralPath $active
        }
        Compose up -d db cache
        Compose up -d --no-deps web worker cron hocuspocus proxy
        Wait-Web
        [IO.File]::WriteAllText($gate,'release failed; original image/volumes selected; operator review required')
        Gateway-Maintenance $true
        # Keep the rolled-back gateway stopped: operator reconciles before reopening either tunnel.
        @{releaseId=$ReleaseId;passed=$false;originalVolumesSelected=$true;maintenance=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $folder 'result.json')
    }catch{
        [IO.File]::WriteAllText($gate,'rollback requires local operator intervention')
        Write-Warning 'Rollback incomplete; gateway/UI remain in maintenance. Original volumes and backup retained.'
    }
    throw $failure
}finally{
    if($operatorLock){$operatorLock.Dispose()}
    $lease.Dispose()
    $env:QLDAPM_RELEASE_OPERATION=$previousOperation
}
