# HISTORICAL one-time migration record. Do not rerun; see CHECKPOINT.md and MSIX path caveat.
$ErrorActionPreference = 'Stop'
$sourceRoot = 'C:\Users\LUIM\AppData\Local\Docker'
$sourceWsl = 'D:\AI project\CSDLDPT\.docker-runtime\wsl'
$destinationRoot = 'D:\Docker'
$recordRoot = Join-Path $env:LOCALAPPDATA 'QLDAPM\openproject-ai\operator\docker-relocation-20261016'
if ([IO.Path]::GetFullPath($sourceRoot) -ne 'C:\Users\LUIM\AppData\Local\Docker' -or
    [IO.Path]::GetFullPath($destinationRoot) -ne 'D:\Docker' -or
    (Get-Item -LiteralPath $sourceRoot -Force).LinkType -or
    (Get-Item -LiteralPath $destinationRoot -Force).LinkType -or
    (Get-Item -LiteralPath "$sourceRoot\wsl" -Force).Target -ne $sourceWsl) { throw 'SOURCE_OR_TARGET_CHANGED' }
if (@(Get-ChildItem -LiteralPath $destinationRoot -Force).Count -ne 0) { throw 'DESTINATION_NOT_EMPTY_RECONCILE' }
if (-not (Test-Path -LiteralPath "$recordRoot\before.json")) { throw 'BEFORE_INVENTORY_REQUIRED' }
if ((Get-Volume -DriveLetter D).SizeRemaining -lt 60GB) { throw 'INSUFFICIENT_DESTINATION_SPACE' }

if (Get-Process -Name 'com.docker.backend' -ErrorAction SilentlyContinue) {
    & docker desktop stop *> "$recordRoot\desktop-stop.log"
    if ($LASTEXITCODE -ne 0) { throw 'DESKTOP_STOP_FAILED' }
}
$distroNames = @(& wsl --list --quiet | ForEach-Object { ($_ -replace "`0", '').Trim() } | Where-Object { $_ })
if ($distroNames.Count -ne 1 -or $distroNames[0] -ne 'docker-desktop') { throw 'NON_DOCKER_WSL_DISTRO_PRESENT' }
& wsl --shutdown *> "$recordRoot\wsl-shutdown.log"
if ($LASTEXITCODE -ne 0) { throw 'WSL_SHUTDOWN_FAILED' }
# Terminating only the distro can leave its utility VM holding the engine VHDX.
$diskFiles = @(Get-ChildItem -LiteralPath $sourceWsl -Recurse -Force -File -Filter '*.vhdx')
if ($diskFiles.Count -ne 2) { throw 'WSL_DISK_SET_CHANGED' }
$held = @()
try {
    foreach ($disk in $diskFiles) {
        $held += [IO.File]::Open($disk.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    }
    Write-Output 'PHASE: Docker stopped, both VHDX read-locked; originals retained'
    Get-Acl -LiteralPath $sourceRoot | Set-Acl -LiteralPath $destinationRoot
    $ipc = @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -Force -File -Attributes ReparsePoint)
    $copyOptions = @('/E','/COPY:DATS','/DCOPY:DAT','/XJ','/R:1','/W:1','/NP')
    $rootArguments = @($sourceRoot,$destinationRoot) + $copyOptions + @("/LOG:$recordRoot\copy-local.log")
    if ($ipc.Count) { $rootArguments += @('/XF') + @($ipc.FullName) }
    & robocopy @rootArguments | Out-Null
    if ($LASTEXITCODE -ge 8) { throw 'LOCAL_COPY_FAILED_SEE_PRIVATE_LOG' }
    Write-Output 'PHASE: regular LocalDocker files copied; copying physical WSL disks'
    & robocopy $sourceWsl "$destinationRoot\wsl" @copyOptions "/LOG:$recordRoot\copy-wsl.log" | Out-Null
    if ($LASTEXITCODE -ge 8) { throw 'WSL_COPY_FAILED_SEE_PRIVATE_LOG' }

    $manifest = @()
    $regular = @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -Force -File | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) })
    $wslFiles = @(Get-ChildItem -LiteralPath $sourceWsl -Recurse -Force -File)
    Write-Output "PHASE: hashing $($regular.Count + $wslFiles.Count) persistent files, including both full VHDX"
    foreach ($pair in @(@{Root=$sourceRoot;Prefix='';Files=$regular}, @{Root=$sourceWsl;Prefix='wsl\';Files=$wslFiles})) {
        foreach ($file in $pair.Files) {
            $relative = $pair.Prefix + [IO.Path]::GetRelativePath($pair.Root, $file.FullName)
            $target = Join-Path $destinationRoot $relative
            if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "COPY_FILE_MISSING:$relative" }
            if ((Get-Item -LiteralPath $target).Length -ne $file.Length) { throw "COPY_SIZE_MISMATCH:$relative" }
            $oldHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
            $newHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
            if ($oldHash -ne $newHash) { throw "COPY_HASH_MISMATCH:$relative" }
            $manifest += [pscustomobject]@{Relative=$relative;Bytes=$file.Length;SHA256=$oldHash}
        }
    }
    $manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$recordRoot\copy-manifest.json" -Encoding utf8
    [pscustomobject]@{phase='COPY_VERIFIED';files=$manifest.Count;bytes=($manifest | Measure-Object Bytes -Sum).Sum;sha256_all_match=$true;source_root_retained=$true;physical_wsl_source_retained=$true;ipc_reparse_entries_retained_not_copied=$ipc.Count;deleted_items=0;formatted_disks=0;target=$destinationRoot} |
        ConvertTo-Json | Tee-Object -FilePath 'D:\AI project\QLDAPM chat\docs\docker-relocation\copy-verification.json'
} finally {
    foreach ($stream in $held) { $stream.Dispose() }
}
