[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^sha256:[a-f0-9]{64}$')][string]$Image,
    [Parameter(Mandatory)][ValidatePattern('^sha256:[a-f0-9]{64}$')][string]$GatewayImage,
    [Parameter(Mandatory)][string]$BackupPath,
    [switch]$OfficialOrigin
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot
$sourceRuntime=Join-Path $env:LOCALAPPDATA 'QLDAPM/openproject-ai'
$backupSource=(Resolve-Path -LiteralPath $BackupPath).Path
if(-not $backupSource.StartsWith([IO.Path]::GetFullPath($sourceRuntime+'/stage-backups')+[IO.Path]::DirectorySeparatorChar)){throw 'Synthetic staging backup required.'}
$evidence=Get-Content -LiteralPath (Join-Path $backupSource 'restore-result.json') -Raw | ConvertFrom-Json
if(-not $evidence.passed -or -not $evidence.syntheticOnly -or $evidence.image -ne $Image){throw 'Matching restored synthetic snapshot required.'}
foreach($entry in @(@('database.dump','databaseHash'),@('assets.tar.gz','assetsHash'))){
    if((Get-FileHash -LiteralPath (Join-Path $backupSource $entry[0])).Hash -ne $evidence.($entry[1])){throw 'Snapshot hash changed.'}
}
$pairProject='qldapm-pair-test-'+[guid]::NewGuid().ToString()
$dockerExecutable=(Get-Command docker.exe -CommandType Application | Select-Object -First 1).Source
function docker {
    if($args[0] -eq 'compose'){
        $index=[Array]::IndexOf([string[]]$args,'--project-name')
        if($index -lt 0 -or $args[$index+1] -notmatch ('^'+[regex]::Escape($pairProject)+'(?:-ai|-restore-[0-9]+)?$')){throw 'FIXTURE_PROJECT_DENIED: no Docker command executed.'}
        if('up' -in $args -and ('public' -in $args -or 'tunnel' -in $args)){throw 'FIXTURE_TUNNEL_START_DENIED'}
    }elseif($args[0] -eq 'stop'){
        foreach($id in $args | Select-Object -Skip 1){
            $label=& $dockerExecutable inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' $id
            if($LASTEXITCODE -ne 0 -or $label -notin @($pairProject,($pairProject+'-ai'))){throw 'FIXTURE_CONTAINER_DENIED: no stop executed.'}
        }
    }elseif($args[0] -notin @('image','inspect','ps','run')){throw 'FIXTURE_DOCKER_ACTION_DENIED'}
    & $dockerExecutable @args
}
$denied=$false
try{docker compose --project-name qldapm-openproject config}catch{if($_.Exception.Message -like 'FIXTURE_PROJECT_DENIED*'){$denied=$true}else{throw}}
if(-not $denied){throw 'Production project guard regression failed.'}
$fixture=Join-Path $sourceRuntime ('operator/rehearsals/'+$pairProject)
$runtime=Join-Path $fixture 'core';$aiRuntime=Join-Path $fixture 'ai'
New-Item -ItemType Directory -Path $runtime,(Join-Path $runtime 'gate'),(Join-Path $aiRuntime 'gateway'),(Join-Path $aiRuntime 'operator'),(Join-Path $aiRuntime 'workspaces') -Force | Out-Null
& icacls $fixture /inheritance:r /grant:r "$([Security.Principal.WindowsIdentity]::GetCurrent().Name):(OI)(CI)F" 'SYSTEM:(OI)(CI)F' | Out-Null
if($LASTEXITCODE -ne 0){throw 'Private fixture ACL required.'}
$envFile=Join-Path $runtime '.env';$aiEnv=Join-Path $aiRuntime '.env'
$composeFile=Join-Path $runtime 'compose.json';$aiComposeFile=Join-Path $aiRuntime 'compose.json'
$active=Join-Path $runtime 'active-volumes.yml';$bridge=Join-Path $runtime 'ui-bridge.yml'
$gate=Join-Path $runtime 'gate/maintenance';$gatewayConfig=Join-Path $aiRuntime 'gateway/config.json'
$imageLock=Join-Path $aiRuntime 'image-lock.json'
$tokens=$null;$errors=$null
$releaseAst=[Management.Automation.Language.Parser]::ParseFile((Join-Path $root 'Release-OpenProjectAI.ps1'),[ref]$tokens,[ref]$errors)
if($errors){throw 'Release parse failed.'}
$managerAst=[Management.Automation.Language.Parser]::ParseFile((Join-Path $root '../Manage-OpenProject.ps1'),[ref]$tokens,[ref]$errors)
if($errors){throw 'Manager parse failed.'}
function Fixture-Text([string]$Text){
    # Keep the implementation; only replace fixed production names/files in the test scope.
    $Text.Replace("'qldapm-openproject'",'$pairProject').Replace('--project-name qldapm-openproject','--project-name $pairProject').Replace("'qldapm-openproject-restore-'","(`$pairProject+'-restore-')").Replace('qldapm-ai --env-file',($pairProject+'-ai --env-file')).Replace("(Join-Path `$root 'compose.yml')",'$aiComposeFile')
}
function Load-Functions($Ast){
    foreach($definition in $Ast.EndBlock.Statements | Where-Object {$_ -is [Management.Automation.Language.FunctionDefinitionAst]}){
        . ([scriptblock]::Create((Fixture-Text $definition.Extent.Text)))
        Set-Item -Path ('Function:script:'+$definition.Name) -Value (Get-Item ('Function:'+$definition.Name)).ScriptBlock
    }
}
# Only cached images; the original live .env/credentials/volumes are never copied.
$images=Get-Content -LiteralPath (Join-Path $sourceRuntime 'image-lock.json') -Raw | ConvertFrom-Json
$oldGateway='sha256:7190fcc265f54880c06927b846982b2c2770109790df0a389d7932637b8641a3'
$officialCore='sha256:2beeecac788d4f423c46a95ffbd04e6479491938b9924b610e9f47d81a38303c'
& docker image inspect $oldGateway $Image $GatewayImage | Out-Null
if($LASTEXITCODE -ne 0){throw 'Cached pinned pair required; no pull.'}
if($OfficialOrigin){docker image inspect $officialCore | Out-Null;if($LASTEXITCODE -ne 0){throw 'Cached official core required; no pull.'}}
$variables=@{OP_IMAGE=$Image;AI_IMAGE=$oldGateway;POSTGRES_IMAGE=$images.POSTGRES_IMAGE;CLOUDFLARED_IMAGE=$images.CLOUDFLARED_IMAGE;
    POSTGRES_PASSWORD=('SyntheticOnly-'+[guid]::NewGuid());SECRET_KEY_BASE=([guid]::NewGuid().ToString('N')*4);
    COLLABORATIVE_SECRET=([guid]::NewGuid().ToString('N')*2);OP_HOST='localhost:8088';OP_HTTPS='false';PROXY_SCHEME='http';
    COLLABORATIVE_URL='ws://localhost:8088/hocuspocus';RUNTIME_DIR=$runtime.Replace('\','/');AI_RUNTIME=$aiRuntime.Replace('\','/');ALLOWED_MAIL='fixture@example.invalid'}
foreach($service in @('cache','hocuspocus','proxy')){
    $key=@{cache='CACHE_IMAGE';hocuspocus='HOCUSPOCUS_IMAGE';proxy='CADDY_IMAGE'}[$service]
    $variables[$key]=(& docker inspect --format '{{.Image}}' ('qldapm-openproject-'+$service+'-1'))
    if($LASTEXITCODE -ne 0 -or $variables[$key] -notmatch '^sha256:[a-f0-9]{64}$'){throw 'Cached infrastructure image required.'}
}
[IO.File]::WriteAllLines($envFile,[string[]]@($variables.GetEnumerator() | ForEach-Object {"$($_.Key)=$($_.Value)"}))
Copy-Item -LiteralPath $envFile -Destination $aiEnv
$saved=@{}
try{
    foreach($key in $variables.Keys){$saved[$key]=[Environment]::GetEnvironmentVariable($key,'Process');[Environment]::SetEnvironmentVariable($key,$variables[$key],'Process')}
    $coreJson=& docker compose --project-name $pairProject --profile public --env-file $envFile -f (Join-Path $root '../compose.yml') config --format json
    if($LASTEXITCODE -ne 0){throw 'Core fixture render failed.'}
    $aiJson=& docker compose --project-name ($pairProject+'-ai') --profile public --env-file $aiEnv -f (Join-Path $root 'compose.yml') config --format json
    if($LASTEXITCODE -ne 0){throw 'Gateway fixture render failed.'}
}finally{foreach($key in $saved.Keys){if($null -eq $saved[$key]){Remove-Item "Env:$key" -ErrorAction SilentlyContinue}else{[Environment]::SetEnvironmentVariable($key,$saved[$key],'Process')}}}
$core=$coreJson | ConvertFrom-Json -AsHashtable;$ai=$aiJson | ConvertFrom-Json -AsHashtable
foreach($doc in @($core,$ai)){
    $doc.Remove('name')
    foreach($service in $doc.services.Values){$service.Remove('ports');$service.pull_policy='never';$service.restart='no'}
    foreach($network in $doc.networks.Values){if(-not $network.external){$network.Remove('name');$network.internal=$true}}
    foreach($volume in $doc.volumes.Values){$volume.Remove('name')}
}
foreach($name in @('web','worker','cron','seeder')){$core.services[$name].image='${OP_IMAGE}'}
$ai.services.gateway.image='${AI_IMAGE}'
$ai.networks.openproject.name=$pairProject+'_frontend'
[IO.File]::WriteAllText($composeFile,($core | ConvertTo-Json -Depth 30))
[IO.File]::WriteAllText($aiComposeFile,($ai | ConvertTo-Json -Depth 30))
Copy-Item -LiteralPath (Join-Path $sourceRuntime 'stage/wbs-snapshot.csv') -Destination (Join-Path $runtime 'wbs-snapshot.csv')
Copy-Item -LiteralPath (Join-Path $sourceRuntime 'stage/test-credentials.json') -Destination (Join-Path $aiRuntime 'gateway/test-credentials.json')
$credentials=Get-Content -LiteralPath (Join-Path $aiRuntime 'gateway/test-credentials.json') -Raw | ConvertFrom-Json
$bootstrap=Get-Content -LiteralPath (Join-Path $sourceRuntime 'stage/bootstrap.json') -Raw | ConvertFrom-Json
$users=@{};foreach($role in $credentials.PSObject.Properties){$users[[string]$role.Value.id]=$role.Name}
@{users=$users;hosts=@('gateway:8090','127.0.0.1:8090');project_id=$bootstrap.project_id;openproject_url='http://web:8080';maintenance=$false} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $gatewayConfig
[IO.File]::WriteAllText((Join-Path $aiRuntime 'gateway/ui.key'),([guid]::NewGuid().ToString('N')*2))
[IO.File]::WriteAllText((Join-Path $aiRuntime 'operator/test-receipt.key'),([guid]::NewGuid().ToString('N')*2))
@{CORE_IMAGE=$Image;AI_IMAGE=$oldGateway} | ConvertTo-Json | Set-Content -LiteralPath $imageLock
[IO.File]::WriteAllText((Join-Path $aiRuntime 'gateway/gemini.json'),'{"enabled":false}')
& docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges:true --mount "type=bind,source=$aiRuntime/gateway,target=/state" --entrypoint python $GatewayImage -c 'import json; from pathlib import Path; from gateway.store import Store; s=Store(Path("/state")); c=json.loads(Path("/state/test-credentials.json").read_text()); [s.issue_token(v["id"],r,v["token"]) for r,v in c.items()]'
if($LASTEXITCODE -ne 0){throw 'Synthetic gateway state initialization failed.'}
Load-Functions $releaseAst
$bodyStart=($releaseAst.EndBlock.Statements | Where-Object {$_.Extent.Text.StartsWith('if(Test-Path -LiteralPath $folder)')}).Extent.StartLineNumber
$releaseBody=[scriptblock]::Create((@($releaseAst.EndBlock.Statements | Where-Object {$_.Extent.StartLineNumber -ge $bodyStart}).Extent.Text -join "`n"))
$managerSwitch=$managerAst.Find({param($node) $node -is [Management.Automation.Language.SwitchStatementAst] -and $node.Condition.Extent.Text -eq '$Action'},$true)
$manager={param($Action,$BackupPath,[switch]$KeepStopped,[switch]$ReplaceLocalData)
    $root=Split-Path $root;$project=$pairProject
    foreach($definition in $managerAst.EndBlock.Statements | Where-Object {$_ -is [Management.Automation.Language.FunctionDefinitionAst]}){. ([scriptblock]::Create((Fixture-Text $definition.Extent.Text)))}
    $clause=@($managerSwitch.Clauses | Where-Object {$_.Item1.Value -eq $Action})
    if($clause.Count -ne 1 -or $Action -notin @('Backup','Restore')){throw 'Only fixed backup/restore manager test actions allowed.'}
    . ([scriptblock]::Create((Fixture-Text ($clause[0].Item2.Statements.Extent.Text -join "`n"))))
    if($Action -eq 'Restore'){
        docker compose --project-name $restoredProject --env-file (Join-Path $BackupPath 'config/.env') -f $composeFile down
        if($LASTEXITCODE -ne 0){throw 'Restore fixture cleanup failed; volumes retained.'}
    }
}
$results=@();$originalVerify=(Get-Item Function:Verify-Pair).ScriptBlock
try{
    Compose up -d db cache
    for($i=0;$i -lt 40;$i++){if((& docker inspect --format '{{.State.Health.Status}}' (Compose ps -q db)) -eq 'healthy'){break};Start-Sleep -Seconds 2}
    Compose cp (Join-Path $backupSource 'database.dump') db:/tmp/pair-original.dump
    Compose exec -T db pg_restore -U postgres --exit-on-error --no-owner -d openproject /tmp/pair-original.dump
    Compose run --rm --no-deps -v "${backupSource}:/backup:ro" --entrypoint tar web -xzf /backup/assets.tar.gz -C /var/openproject/assets
    Compose run --rm --no-deps -e VERIFY_BACKUP=true -v "${backupSource}:/backup:ro" web bundle exec rails runner /qldapm/backup_state.rb
    if($OfficialOrigin){
        # Reconstruct a synthetic original schema only inside this UUID clone, then boot the actual official binary.
        Compose run --rm --no-deps -e "QLDAPM_PAIR_PROJECT=$pairProject" -v "${root}/core:/trusted:ro" web bundle exec rails runner /trusted/official_origin_fixture.rb
        foreach($version in @('20261010190000','20261010180000','20261009160000')){
            Compose run --rm --no-deps web bundle exec rails db:migrate:down "VERSION=$version"
        }
        Set-Image $envFile 'OP_IMAGE' $officialCore
        $originImages=Get-Content -LiteralPath $imageLock -Raw | ConvertFrom-Json
        $originImages.CORE_IMAGE=$officialCore
        $originImages | ConvertTo-Json | Set-Content -LiteralPath $imageLock
        Compose run --rm --no-deps -e "QLDAPM_PAIR_PROJECT=$pairProject" -v "${root}/core:/trusted:ro" -v "${runtime}/wbs-snapshot.csv:/private/wbs-snapshot.csv:ro" web bundle exec rails runner /trusted/official_origin_assert.rb
        $fixtureCredentials=Get-Content -LiteralPath (Join-Path $aiRuntime 'gateway/test-credentials.json') -Raw | ConvertFrom-Json -AsHashtable
        $fixtureCredentials['BA']=$fixtureCredentials['BA-PM'];$fixtureCredentials.Remove('BA-PM')
        $fixtureCredentials | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $aiRuntime 'gateway/test-credentials.json')
        $fixtureConfiguration=Get-Content -LiteralPath $gatewayConfig -Raw | ConvertFrom-Json -AsHashtable
        $fixtureConfiguration.users[[string]$fixtureCredentials.BA.id]='BA'
        $fixtureConfiguration | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $gatewayConfig
        docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges:true --mount "type=bind,source=$aiRuntime/gateway,target=/state" --entrypoint python $GatewayImage -c 'import json; from pathlib import Path; from gateway.store import Store; s=Store(Path("/state")); v=json.loads(Path("/state/test-credentials.json").read_text())["BA"]; s.issue_token(v["id"],"BA",v["token"])'
        if($LASTEXITCODE -ne 0){throw 'Synthetic BA state initialization failed.'}
    }
    $ActorId=[int]$credentials.PM.id
    $request=Join-Path $runtime 'inspect.json'
    @{action='inspect';actor=$ActorId;parameters=@{}} | ConvertTo-Json | Set-Content -LiteralPath $request
    $inspection=Compose run --rm --no-deps -e QLDAPM_REQUEST=/operator/inspect.json -v "${runtime}:/operator:ro" -v "${root}/core:/trusted:ro" web bundle exec rails runner /trusted/admin_operation.rb
    $BeforeHash=($inspection | Where-Object {$_ -like '{"configuration":*'} | ConvertFrom-Json).hash
    if($BeforeHash -notmatch '^[a-f0-9]{64}$'){throw 'Synthetic configuration fingerprint required.'}
    $cases=if($OfficialOrigin){@('gateway-failure','success')}else{@('success','gateway-failure')}
    foreach($caseName in $cases){
        $ReleaseId=[guid]::NewGuid().ToString();$folder=Join-Path $runtime ('releases/'+$ReleaseId);$backup=Join-Path $runtime ('backups/release-'+$ReleaseId)
        $beforeSelection=if(Test-Path -LiteralPath $active){[IO.File]::ReadAllText($active)}else{''}
        $script:injectFailure=$caseName -eq 'gateway-failure'
        function Verify-Pair {
            & $originalVerify
            if($script:injectFailure){[IO.File]::WriteAllText((Join-Path $aiRuntime 'gateway/failure.marker'),'synthetic failed candidate');throw 'Injected capability acceptance failure after real pair verification.'}
        }
        $caught=$false
        try{. $releaseBody}catch{$caught=$true;if($caseName -eq 'success'){throw}}
        $outcome=Get-Content -LiteralPath (Join-Path $folder 'result.json') -Raw | ConvertFrom-Json
        if($caseName -eq 'success'){
            if($caught -or -not $outcome.passed -or (Test-Path -LiteralPath $gate)){throw 'Actual pair release failed.'}
        }else{
            if(-not $caught -or -not $outcome.originalVolumesSelected -or -not (Test-Path -LiteralPath $gate)){throw 'Rollback selection/fencing failed.'}
            $afterSelection=if(Test-Path -LiteralPath $active){[IO.File]::ReadAllText($active)}else{''}
            if($afterSelection -ne $beforeSelection -or (Test-Path -LiteralPath (Join-Path $aiRuntime 'gateway/failure.marker')) -or -not (Test-Path -LiteralPath (Join-Path $folder 'failed-gateway/failure.marker'))){throw 'Old volumes/state not retained or failed state lost.'}
            $check=& docker inspect --format '{{.State.Status}}' (AICompose ps -aq gateway)
            if($check -ne 'exited'){throw 'Rolled-back gateway must remain stopped.'}
        }
        $sourceComparison=if($OfficialOrigin -and $caseName -eq 'success'){@('-e','QLDAPM_COMPARE_SOURCE=true')}else{@()}
        Compose run --rm --no-deps -e VERIFY_BACKUP=true @sourceComparison -v "${backup}:/backup:ro" web bundle exec rails runner /qldapm/backup_state.rb
        if($OfficialOrigin -and $caseName -eq 'gateway-failure'){
            if((Get-Content -LiteralPath $imageLock -Raw | ConvertFrom-Json).CORE_IMAGE -ne $officialCore){throw 'Official rollback image selection failed.'}
            Compose run --rm --no-deps -e "QLDAPM_PAIR_PROJECT=$pairProject" -v "${runtime}/wbs-snapshot.csv:/private/wbs-snapshot.csv:ro" -v "${root}/core:/trusted:ro" web bundle exec rails runner /trusted/official_origin_assert.rb
        }else{
            Compose run --rm --no-deps -v "${runtime}/wbs-snapshot.csv:/private/wbs-snapshot.csv:ro" -v "${root}/core:/trusted:ro" web bundle exec rails runner /trusted/release_verify.rb
        }
        $results+=@{case=$caseName;passed=$true;releaseId=$ReleaseId}
    }
    $limitations=@('Operator approval and real user TOTP/Codex acceptance are not simulated')
    if(-not $OfficialOrigin){$limitations+=@('Preexisting candidate core schema; official upgrade is not rehearsed')}
    if($OfficialOrigin){$limitations+=@('Original schema reconstructed from synthetic staging; not a production database clone')}
    @{passed=$true;syntheticOnly=$true;image=$Image;gatewayImage=$GatewayImage;cases=$results;productionChanged=$false;
        officialOrigin=[bool]$OfficialOrigin;originalImage=$(if($OfficialOrigin){$officialCore}else{$Image});limitations=$limitations} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $fixture 'result.json')
    Write-Output "Docker release pair/rollback PASS; evidence retained: $fixture/result.json"
}finally{
    # Keep volumes/backups; remove ephemeral containers/networks so repeated rehearsal cannot exhaust IP pools.
    $projects=@(& docker ps -a --format '{{.Label "com.docker.compose.project"}}' | Where-Object {
        $_ -match ('^'+[regex]::Escape($pairProject)+'(?:-ai|-restore-[0-9]+)?$')} | Sort-Object -Unique -Descending)
    foreach($testProject in $projects){
        $testCompose=if($testProject -eq $pairProject+'-ai'){$aiComposeFile}else{$composeFile}
        docker compose --project-name $testProject --env-file $envFile -f $testCompose down
        if($LASTEXITCODE -ne 0){Write-Warning 'Fixture cleanup incomplete; retain evidence and reconcile only UUID resources.'}
    }
}
