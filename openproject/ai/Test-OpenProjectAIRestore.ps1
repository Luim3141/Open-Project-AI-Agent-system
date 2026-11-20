[CmdletBinding()]
param([ValidatePattern('^sha256:[a-f0-9]{64}$')][string]$Image)
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$runtime=Join-Path $env:LOCALAPPDATA 'QLDAPM/openproject-ai'
$envFile=Join-Path $runtime '.env'
$composeFile=Join-Path $root 'stage.yml'
$identifier=[guid]::NewGuid().ToString()
$restoreProject='qldapm-ai-restore-'+$identifier
$backup=Join-Path $runtime ('stage-backups/'+$identifier)
$fixture='qldapm-ai-restore-fixture-'+$identifier+'.txt'
$previousCoreImage=$env:CORE_IMAGE
if(-not $Image){$Image=(Get-Content -LiteralPath (Join-Path $runtime 'image-lock.json') -Raw | ConvertFrom-Json).CORE_IMAGE}
$env:CORE_IMAGE=$Image
$runningImage=& docker inspect --format '{{.Image}}' qldapm-ai-stage-staging-web-1
if($LASTEXITCODE -ne 0 -or $runningImage -ne $Image){$env:CORE_IMAGE=$previousCoreImage;throw 'Restore rehearsal must match the running synthetic staging image.'}
function Compose([string]$ProjectName) {
    if($ProjectName -notin @('qldapm-ai-stage',$restoreProject)){throw 'Synthetic restore project denied.'}
    $files=@('-f',$composeFile)
    if($ProjectName -eq 'qldapm-ai-stage' -and (Test-Path -LiteralPath (Join-Path $runtime 'stage-ai/ui.key'))){$files+=@('-f',(Join-Path $root 'deep-ai.stage.yml'))}
    & docker compose --project-name $ProjectName --env-file $envFile @files @args
    if($LASTEXITCODE -ne 0){throw 'Staging restore Compose operation failed.'}
}
function Wait-Database([string]$ProjectName){
    for($attempt=0;$attempt -lt 40;$attempt++){
        $container=Compose $ProjectName ps -q db
        if($container -and ((& docker inspect --format '{{.State.Health.Status}}' $container) -eq 'healthy')){return}
        Start-Sleep -Seconds 2
    }
    throw 'Restore database did not become healthy.'
}
function Wait-StagingWeb {
    for($attempt=0;$attempt -lt 120;$attempt++){
        $container=Compose qldapm-ai-stage ps -q staging-web
        if($container -and ((& docker inspect --format '{{.State.Health.Status}}' $container) -eq 'healthy')){return}
        Start-Sleep -Seconds 2
    }
    throw 'Staging web not healthy after restore; transport acceptance must not start.'
}
$label=& docker inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' qldapm-ai-stage-db-1
if($LASTEXITCODE -ne 0 -or $label -ne 'qldapm-ai-stage'){throw 'Synthetic staging database required.'}
$lock=[IO.File]::Open((Join-Path $runtime 'operator/stage-restore.lock'),'OpenOrCreate','ReadWrite','None')
$fixtureCreated=$false
try{
    New-Item -ItemType Directory -Path $backup | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $backup 'config') | Out-Null
    Compose qldapm-ai-stage stop staging-web
    & docker run --rm --network none --user 1000:1000 --read-only --cap-drop ALL --security-opt no-new-privileges:true --mount 'type=volume,source=qldapm-ai-stage_stage-assets,target=/assets' --mount "type=bind,source=$root/core,target=/trusted,readonly" --entrypoint cp $image /trusted/restore_fixture.txt "/assets/$fixture"
    if($LASTEXITCODE -ne 0){throw 'Cannot create synthetic attachment fixture.'}
    $fixtureCreated=$true
    Compose qldapm-ai-stage run --rm --no-deps -v "${backup}:/backup" staging-web bundle exec rails runner /qldapm/backup_state.rb
    Compose qldapm-ai-stage exec -T db pg_dump -U postgres -Fc -f /tmp/qldapm-ai-stage-backup.dump openproject
    Compose qldapm-ai-stage cp db:/tmp/qldapm-ai-stage-backup.dump (Join-Path $backup 'database.dump')
    Compose qldapm-ai-stage run --rm --no-deps -v "${backup}:/backup" --entrypoint tar staging-web -czf /backup/assets.tar.gz -C /var/openproject/assets .
    $expectedAssets=Compose qldapm-ai-stage run --rm --no-deps --entrypoint sh staging-web -c 'cd /var/openproject/assets && find . -type f -exec sha256sum {} +'
    Copy-Item -LiteralPath $envFile,$composeFile -Destination (Join-Path $backup 'config')
    Compose $restoreProject up -d db
    Wait-Database $restoreProject
    Compose $restoreProject cp (Join-Path $backup 'database.dump') db:/tmp/qldapm-ai-stage-restore.dump
    Compose $restoreProject exec -T db pg_restore -U postgres --exit-on-error --no-owner -d openproject /tmp/qldapm-ai-stage-restore.dump
    Compose $restoreProject run --rm --no-deps -v "${backup}:/backup:ro" --entrypoint tar staging-web -xzf /backup/assets.tar.gz -C /var/openproject/assets
    $actualAssets=Compose $restoreProject run --rm --no-deps --entrypoint sh staging-web -c 'cd /var/openproject/assets && find . -type f -exec sha256sum {} +'
    if((($expectedAssets | Sort-Object) -join "`n") -ne (($actualAssets | Sort-Object) -join "`n")){throw 'Synthetic attachment restore differs.'}
    Compose $restoreProject run --rm --no-deps -e VERIFY_BACKUP=true -v "${backup}:/backup:ro" staging-web bundle exec rails runner /qldapm/backup_state.rb
    if((Get-FileHash -LiteralPath $envFile).Hash -ne (Get-FileHash -LiteralPath (Join-Path $backup 'config/.env')).Hash){throw 'Configuration restore copy differs.'}
    $tables=@((Get-Content -LiteralPath (Join-Path $backup 'database-state.json') -Raw | ConvertFrom-Json).PSObject.Properties).Count
    $record=@{passed=$true;syntheticOnly=$true;image=$image;restoreProject=$restoreProject;backup=$backup;tables=$tables;databaseHash=(Get-FileHash -LiteralPath (Join-Path $backup 'database.dump')).Hash;assetsHash=(Get-FileHash -LiteralPath (Join-Path $backup 'assets.tar.gz')).Hash;configurationHash=(Get-FileHash -LiteralPath $envFile).Hash}
    $record | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backup 'restore-result.json')
    Write-Host "Staging database/assets/config restore PASS; retained isolated volumes: $restoreProject. Evidence: $backup/restore-result.json"
}finally{
    # Retain snapshot volumes, not idle networks that exhaust Docker's subnet pool on repeated tests.
    Compose $restoreProject down
    if($fixtureCreated){
        & docker run --rm --network none --user 1000:1000 --read-only --cap-drop ALL --security-opt no-new-privileges:true --mount 'type=volume,source=qldapm-ai-stage_stage-assets,target=/assets' --entrypoint rm $image -f "/assets/$fixture"
        if($LASTEXITCODE -ne 0){Write-Warning 'Synthetic fixture cleanup failed; live data unaffected.'}
    }
    try{
        Compose qldapm-ai-stage up -d staging-web
        Wait-StagingWeb
    }finally{$lock.Dispose();$env:CORE_IMAGE=$previousCoreImage}
}
