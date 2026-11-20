$ErrorActionPreference='Stop'
$fixtureRoot=Join-Path ([IO.Path]::GetTempPath()) ('qldapm-release-pair-'+[guid]::NewGuid())
$root=Split-Path $PSScriptRoot
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $root 'Release-OpenProjectAI.ps1'),[ref]$tokens,[ref]$errors)
if($errors){throw 'Release script parse failed.'}
try {
    foreach($caseName in @('none','migration','gateway','shared-key','reopen')){
        $runtime=Join-Path $fixtureRoot "$caseName/core"
        $aiRuntime=Join-Path $fixtureRoot "$caseName/ai"
        $ReleaseId=[guid]::NewGuid().ToString()
        $Image='sha256:'+('a'*64);$GatewayImage='sha256:'+('b'*64)
        $BeforeHash='c'*64;$ActorId=19
        $envFile=Join-Path $runtime '.env';$aiEnv=Join-Path $aiRuntime '.env'
        $composeFile='fixture-core.yml';$imageLock=Join-Path $aiRuntime 'image-lock.json'
        $folder=Join-Path $runtime ('releases/'+$ReleaseId);$backup=Join-Path $runtime ('backups/'+$ReleaseId)
        $active=Join-Path $runtime 'active-volumes.yml';$bridge=Join-Path $runtime 'ui-bridge.yml'
        $gate=Join-Path $runtime 'gate/maintenance';$gatewayConfig=Join-Path $aiRuntime 'gateway/config.json'
        New-Item -ItemType Directory -Path (Join-Path $runtime 'gate'),(Join-Path $runtime 'releases'),(Join-Path $aiRuntime 'gateway'),(Join-Path $aiRuntime 'operator') -Force | Out-Null
        [IO.File]::WriteAllText($envFile,"OP_IMAGE=old-core`n")
        [IO.File]::WriteAllText($aiEnv,"AI_IMAGE=old-gateway`n")
        [IO.File]::WriteAllText($imageLock,'{"CORE_IMAGE":"old-core","AI_IMAGE":"old-gateway"}')
        [IO.File]::WriteAllText($gatewayConfig,'{"maintenance":false}')
        [IO.File]::WriteAllText((Join-Path $aiRuntime 'gateway/gateway.sqlite'),'original-synthetic-state')
        [IO.File]::WriteAllText((Join-Path $aiRuntime 'gateway/ui.key'),('synthetic-ui-'+'0'*40))
        [IO.File]::WriteAllText((Join-Path $aiRuntime 'operator/test-receipt.key'),('synthetic-receipt-'+'1'*40))
        if($caseName -eq 'shared-key'){
            [IO.File]::WriteAllText((Join-Path $aiRuntime 'operator/test-receipt.key'),[IO.File]::ReadAllText((Join-Path $aiRuntime 'gateway/ui.key')))
        }
        [IO.File]::WriteAllText($active,'old-volume')
        $script:events=[Collections.Generic.List[string]]::new()
        $script:failedOnce=$false
        function docker {
            $command=$args -join ' '
            $script:events.Add($command)
            $global:LASTEXITCODE=0
            if($caseName -eq 'migration' -and $command -like '*rails db:migrate*' -and -not $script:failedOnce){
                $script:failedOnce=$true;$global:LASTEXITCODE=1;return
            }
            if($command -like 'inspect*Health.Status*'){return 'healthy'}
            if($command -like 'inspect*{{.Image}}*'){
                if($command -like '*fixture-gateway*'){return $GatewayImage}else{return $Image}
            }
            if($command -like '*ps -q gateway*'){return 'fixture-gateway'}
            if($command -like '*ps -q web*'){return 'fixture-web'}
            if($command -like '*ps -q db*'){return 'fixture-db'}
            if($caseName -eq 'gateway' -and $command -like '*exec -T gateway python*' -and -not $script:failedOnce){
                $script:failedOnce=$true
                [IO.File]::WriteAllText((Join-Path $aiRuntime 'gateway/gateway.sqlite'),'new-failed-synthetic-state')
                $global:LASTEXITCODE=1
            }
        }
        $manager={param($Action,$BackupPath,[switch]$KeepStopped,[switch]$ReplaceLocalData)
            $script:events.Add('manager '+$Action)
            if($Action -eq 'Restore'){[IO.File]::WriteAllText($active,'new-volume')}
        }
        foreach($definition in $ast.EndBlock.Statements | Where-Object {$_ -is [Management.Automation.Language.FunctionDefinitionAst]}){
            . ([scriptblock]::Create($definition.Extent.Text))
        }
        if($caseName -eq 'reopen'){
            $script:originalMaintenance=(Get-Item Function:Gateway-Maintenance).ScriptBlock
            function Gateway-Maintenance([bool]$Enabled){
                if(-not $Enabled){
                    [IO.File]::WriteAllText((Join-Path $aiRuntime 'gateway/gateway.sqlite'),'new-committed-state')
                    throw 'Synthetic error while reopening writes.'
                }
                & $script:originalMaintenance $Enabled
            }
        }
        $body=@($ast.EndBlock.Statements | Where-Object {$_.Extent.StartLineNumber -ge ($ast.EndBlock.Statements | Where-Object {$_.Extent.Text.StartsWith('if(Test-Path -LiteralPath $folder)')}).Extent.StartLineNumber})
        $caught=$false
        try{. ([scriptblock]::Create(($body.Extent.Text -join "`n")))}catch{$caught=$true}
        if($caseName -eq 'none'){
            if($caught){throw 'Successful release fixture failed.'}
            $result=Get-Content -LiteralPath (Join-Path $folder 'result.json') -Raw | ConvertFrom-Json
            if(-not $result.passed -or $result.gatewayImage -ne $GatewayImage -or (Test-Path -LiteralPath $gate)){throw 'Pair success/maintenance result failed.'}
            $mounts=(Get-Content -LiteralPath $bridge -Raw | ConvertFrom-Json).services.web.volumes
            if($mounts.Count -ne 2 -or @($mounts | Where-Object {-not $_.read_only -or $_.bind.create_host_path}).Count){throw 'Exactly two read-only existing-file mounts required.'}
            if(($mounts.target -join ',') -ne '/qldapm-ui/ui.key,/qldapm-ui/test-receipt.key'){throw 'Unexpected secret mount.'}
            $images=Get-Content -LiteralPath $imageLock -Raw | ConvertFrom-Json
            if($images.CORE_IMAGE -ne $Image -or $images.AI_IMAGE -ne $GatewayImage){throw 'Pair pin mismatch.'}
        }elseif($caseName -eq 'reopen'){
            if(-not $caught -or -not (Test-Path -LiteralPath $gate)){throw 'Post-cutover failure must close access.'}
            if([IO.File]::ReadAllText($envFile).Trim() -ne "OP_IMAGE=$Image" -or [IO.File]::ReadAllText($aiEnv).Trim() -ne "AI_IMAGE=$GatewayImage"){throw 'Never rollback after writes may have opened.'}
            if([IO.File]::ReadAllText((Join-Path $aiRuntime 'gateway/gateway.sqlite')) -ne 'new-committed-state' -or [IO.File]::ReadAllText($active) -ne 'new-volume'){throw 'Post-cutover writes lost.'}
        }else{
            if(-not $caught -or -not (Test-Path -LiteralPath $gate)){throw 'Failure must retain maintenance.'}
            if([IO.File]::ReadAllText($envFile) -ne "OP_IMAGE=old-core`n" -or [IO.File]::ReadAllText($aiEnv) -ne "AI_IMAGE=old-gateway`n"){throw 'Both previous images must be restored.'}
            if([IO.File]::ReadAllText($active) -ne 'old-volume' -or (Test-Path -LiteralPath $bridge)){throw 'Previous volumes/bridge selection not restored.'}
            if([IO.File]::ReadAllText((Join-Path $aiRuntime 'gateway/gateway.sqlite')) -ne 'original-synthetic-state'){throw 'Gateway state not restored.'}
            if(-not (Get-Content -LiteralPath $gatewayConfig -Raw | ConvertFrom-Json).maintenance){throw 'Gateway maintenance must remain on.'}
        }
        $stopIndex=$script:events.IndexOf(($script:events | Where-Object {$_ -like '*stop gateway tunnel*'} | Select-Object -First 1))
        $backupIndex=$script:events.IndexOf('manager Backup')
        if($stopIndex -lt 0 -or $stopIndex -ge $backupIndex -or @($script:events | Where-Object {$_ -like '*up*tunnel*'}).Count){throw 'Freeze order or remote fail-closed violated.'}
        Write-Output "Release pair fixture PASS: $caseName (no Docker/live calls)."
    }
    $runtime=Join-Path $fixtureRoot 'compose-core'
    New-Item -ItemType Directory -Path $runtime | Out-Null
    $bridge=Join-Path $runtime 'ui-bridge.yml'
    [IO.File]::WriteAllText($bridge,'synthetic-compose')
    $managerAst=[Management.Automation.Language.Parser]::ParseFile((Join-Path $root '../Manage-OpenProject.ps1'),[ref]$tokens,[ref]$errors)
    if($errors){throw 'Manager parse failed.'}
    foreach($sourceAst in @($ast,$managerAst)){
        $definition=$sourceAst.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Compose'},$true)
        . ([scriptblock]::Create($definition.Extent.Text))
        $project='qldapm-openproject';$script:events.Clear()
        Compose ps -q web | Out-Null
        if(-not $script:events[0].Contains('-f '+$bridge)){throw 'Persistent UI bridge missing from Compose.'}
        if($sourceAst -eq $managerAst){
            $project='synthetic-restore';$script:events.Clear()
            Compose ps -q web | Out-Null
            if($script:events[0].Contains($bridge)){throw 'Live UI key mounted into temporary restore stack.'}
        }
    }
    Write-Output 'Persistent Compose bridge PASS: manager/release retain mount; restore stack excluded.'
}finally{
    Remove-Item Function:docker -ErrorAction SilentlyContinue
    $resolved=[IO.Path]::GetFullPath($fixtureRoot)
    if(-not $resolved.StartsWith([IO.Path]::GetTempPath()) -or [IO.Path]::GetFileName($resolved) -notmatch '^qldapm-release-pair-[a-f0-9-]{36}$'){throw 'Unexpected fixture cleanup path.'}
    if(Test-Path -LiteralPath $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
