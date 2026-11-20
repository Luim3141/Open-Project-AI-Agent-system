$ErrorActionPreference='Stop'
$fixtureRoot=Join-Path ([IO.Path]::GetTempPath()) ('qldapm-backup-lease-'+[guid]::NewGuid().ToString())
$runtime=$fixtureRoot
$BackupPath=Join-Path $fixtureRoot 'backup'
$previous=Join-Path $fixtureRoot 'previous'
$lease=$null
try {
    New-Item -ItemType Directory -Path (Join-Path $BackupPath 'config'),$previous -Force | Out-Null
    [IO.File]::WriteAllText((Join-Path $runtime 'fixture.json'),'synthetic-only')
    $lease=[IO.File]::Open((Join-Path $runtime 'release.lock'),'OpenOrCreate','ReadWrite','None')
    $tokens=$null; $errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot '../../Manage-OpenProject.ps1'),[ref]$tokens,[ref]$errors)
    if($errors){throw 'Manager parse failed.'}
    # Exercise the actual outgoing configuration-copy pipelines without running Docker/live operations.
    $copies=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.PipelineAst] -and $node.Extent.Text.StartsWith('Get-ChildItem -LiteralPath $runtime -File |')},$true))
    if($copies.Count -ne 2){throw 'Configuration-copy seam changed; update the regression.'}
    foreach($copy in $copies){ & ([scriptblock]::Create($copy.Extent.Text)) }
    foreach($destination in @((Join-Path $BackupPath 'config'),$previous)){
        if(-not (Test-Path -LiteralPath (Join-Path $destination 'fixture.json')) -or (Test-Path -LiteralPath (Join-Path $destination 'release.lock'))){throw 'Backup configuration/lease isolation failed.'}
    }
    Write-Output 'Backup configuration PASS: active exclusive release lease excluded; configuration retained.'
}finally {
    if($lease){$lease.Dispose()}
    $resolved=[IO.Path]::GetFullPath($fixtureRoot)
    if(-not $resolved.StartsWith([IO.Path]::GetTempPath()) -or [IO.Path]::GetFileName($resolved) -notmatch '^qldapm-backup-lease-[a-f0-9-]{36}$'){throw 'Unexpected fixture cleanup path.'}
    if(Test-Path -LiteralPath $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
