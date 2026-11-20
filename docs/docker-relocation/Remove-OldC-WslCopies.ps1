param([switch]$SelfTest)
$ErrorActionPreference='Stop'
$cacheRoot='C:\Users\LUIM\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local'
$oldRoots=@("$cacheRoot\Docker\wsl", "$cacheRoot\Docker.redirect-retained-20261016-014024\wsl")
$files=@("$($oldRoots[0])\main\ext4.vhdx", "$($oldRoots[1])\disk\docker_data.vhdx", "$($oldRoots[1])\main\ext4.vhdx")
function Assert-PhysicalOldCPath([string]$Path) {
    $full=[IO.Path]::GetFullPath($Path)
    if ($full -notin $files -or -not $full.StartsWith($cacheRoot+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'PATH_OUTSIDE_EXACT_OLD_C_ALLOWLIST' }
    $current=$full
    while ($current) {
        if ((Get-Item -LiteralPath $current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw ('REPARSE_POINT_REFUSED:'+ $current) }
        $parent=Split-Path $current -Parent
        if (-not $parent -or $parent -eq $current) { break }
        $current=$parent
    }
    return $full
}
if ($SelfTest) {
    foreach($file in $files) { Assert-PhysicalOldCPath $file | Out-Null }
    foreach($denied in 'D:\Docker\wsl\disk\docker_data.vhdx','C:\Users\LUIM\AppData\Local\Docker\wsl\main\ext4.vhdx',"$cacheRoot\Docker\wsl\..\other.vhdx") {
        $rejected=$false
        try { Assert-PhysicalOldCPath $denied | Out-Null } catch { $rejected=$true }
        if (-not $rejected) { throw 'PATH_GUARD_SELF_TEST_FAILED' }
    }
    Write-Output 'PASS: only three exact physical C files accepted; active C junction/D/traversal refused'
    exit 0
}
$hostStatePath='D:\Docker\relocation-host-state.json'
if (((Get-Date)-(Get-Item -LiteralPath $hostStatePath).LastWriteTime).TotalMinutes -gt 5) { throw 'FRESH_UNPACKAGED_HOST_INSPECTION_REQUIRED' }
$hostState=Get-Content -LiteralPath $hostStatePath -Raw | ConvertFrom-Json
if ($hostState.custom_wsl -ne 'D:\Docker\wsl' -or -not $hostState.containerd_store) { throw 'ACTIVE_DATA_SETTING_NOT_D' }
$registrations=@($hostState.registry | Where-Object DistributionName -eq 'docker-desktop')
if ($registrations.Count -ne 1 -or $registrations[0].BasePath -ne '\\?\D:\Docker\wsl\main') { throw 'REAL_WSL_REGISTRATION_NOT_D' }
foreach($part in 'wsl','log','tasks') {
    $entry=@($hostState.entries | Where-Object Name -eq $part)
    if ($entry.Count -ne 1 -or @($entry[0].Target).Count -ne 1 -or $entry[0].Target[0] -ne ('D:\Docker\'+$part)) { throw 'REAL_HOST_JUNCTION_CHANGED' }
}
foreach($path in 'D:\Docker\wsl\main\ext4.vhdx','D:\Docker\wsl\disk\docker_data.vhdx') {
    $inUse=$false
    try { $gate=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::None); $gate.Dispose() }
    catch [IO.IOException] { if (($_.Exception.HResult -band 65535) -in 32,33) {$inUse=$true} else {throw} }
    if (-not $inUse) { throw 'ACTIVE_D_VHDX_NOT_HELD_BY_RUNTIME' }
}
$archive='D:\Docker\retained-c-wsl-20261016-1012'
if (Test-Path -LiteralPath $archive) { throw 'ARCHIVE_ALREADY_EXISTS' }
if ((Get-Item -LiteralPath 'D:\Docker').Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'D_ARCHIVE_ROOT_IS_REPARSE' }
New-Item -ItemType Directory -Path $archive | Out-Null
Set-Acl -LiteralPath $archive -AclObject (Get-Acl -LiteralPath 'D:\Docker')
$held=@(); $manifest=@()
try {
    foreach($path in $files) {
        $full=Assert-PhysicalOldCPath $path
        $held += [IO.File]::Open($full,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
        $item=Get-Item -LiteralPath $full -Force
        $relative=$full.Substring($cacheRoot.Length+1)
        $target=Join-Path $archive $relative
        New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force | Out-Null
        Copy-Item -LiteralPath $full -Destination $target
        $hash=(Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash
        if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $hash) { throw 'ARCHIVE_HASH_MISMATCH' }
        $manifest += [pscustomobject]@{source=$full;archived_to=$target;bytes=$item.Length;sha256=$hash}
    }
} finally { foreach($handle in $held) { $handle.Dispose() } }
$manifest | ConvertTo-Json | Set-Content -LiteralPath "$archive\manifest.json" -Encoding UTF8
foreach($row in $manifest) {
    $full=Assert-PhysicalOldCPath $row.source
    $gate=[IO.File]::Open($full,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::None)
    $gate.Dispose()
    if ((Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash -ne $row.sha256) { throw 'SOURCE_CHANGED_BEFORE_DELETE' }
    Remove-Item -LiteralPath $full -Force
}
foreach($root in $oldRoots) {
    foreach($directory in @("$root\main","$root\disk",$root)) {
        if (-not (Test-Path -LiteralPath $directory)) { continue }
        if ((Get-Item -LiteralPath $directory).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'EMPTY_DIRECTORY_CLEANUP_REFUSES_REPARSE' }
        if (@(Get-ChildItem -LiteralPath $directory -Force).Count -eq 0) {
            [IO.Directory]::Delete($directory,$false)
        }
    }
}
$receipt=[ordered]@{at=(Get-Date -Format o);removed_only_physical_C_files=$manifest;logical_bytes_removed=($manifest | Measure-Object bytes -Sum).Sum;archive=$archive;archive_sha256_all_match=$true;active_D_data_deleted=$false;active_C_junction_deleted=$false;wsl_unregistered=$false;formatted_disks=0}
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath 'D:\AI project\QLDAPM chat\docs\docker-relocation\c-old-wsl-cleanup.json' -Encoding UTF8
Write-Output 'Three unused C VHDX copies removed after verified D archive; active D disks and C junction unchanged'
