# HISTORICAL one-time migration record. Do not rerun; see CHECKPOINT.md and MSIX path caveat.
$ErrorActionPreference = 'Stop'
$sourceRoot = 'C:\Users\LUIM\AppData\Local\Docker'
$destinationRoot = 'D:\Docker'
$recordRoot = Join-Path $env:LOCALAPPDATA 'QLDAPM\openproject-ai\operator\docker-relocation-20261016'
$verification = Get-Content -LiteralPath 'D:\AI project\QLDAPM chat\docs\docker-relocation\copy-verification.json' -Raw | ConvertFrom-Json
if ($verification.phase -ne 'COPY_VERIFIED' -or -not $verification.sha256_all_match -or $verification.deleted_items -ne 0) { throw 'VERIFIED_COPY_REQUIRED' }
if ([IO.Path]::GetFullPath($sourceRoot) -ne 'C:\Users\LUIM\AppData\Local\Docker' -or
    [IO.Path]::GetFullPath($destinationRoot) -ne 'D:\Docker' -or
    (Get-Item -LiteralPath $sourceRoot -Force).LinkType -or
    (Get-Item -LiteralPath $destinationRoot -Force).LinkType -or
    (Get-Item -LiteralPath "$destinationRoot\wsl" -Force).LinkType) { throw 'PHYSICAL_SOURCE_TARGET_CHANGED' }
foreach ($disk in @('disk\docker_data.vhdx','main\ext4.vhdx')) {
    $stream = [IO.File]::Open((Join-Path "$destinationRoot\wsl" $disk), [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::None)
    $stream.Dispose()
}
$retained = 'C:\Users\LUIM\AppData\Local\Docker.retained-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
if ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($retained)) -ne 'C:\Users\LUIM\AppData\Local' -or
    (Test-Path -LiteralPath $retained)) { throw 'RETAINED_PATH_NOT_SAFE' }
# Same-parent rename only; no recursive cross-shell move or removal of either dataset.
Move-Item -LiteralPath $sourceRoot -Destination $retained
try {
    New-Item -ItemType Junction -Path $sourceRoot -Target $destinationRoot | Out-Null
} catch {
    if (-not (Test-Path -LiteralPath $sourceRoot)) { Move-Item -LiteralPath $retained -Destination $sourceRoot }
    throw
}
if ((Get-Item -LiteralPath $sourceRoot -Force).Target -ne $destinationRoot) { throw 'JUNCTION_TARGET_MISMATCH' }
$state = [pscustomobject]@{phase='SWITCHED_STARTING';physical_data_root=$destinationRoot;compatibility_junction=$sourceRoot;retained_original_root=$retained;retained_original_wsl='D:\AI project\CSDLDPT\.docker-runtime\wsl';copied_files=$verification.files;deleted_items=0;formatted_disks=0;wsl_unregistered=$false}
$state | ConvertTo-Json | Set-Content -LiteralPath "$recordRoot\switch-state.json" -Encoding utf8
$state | ConvertTo-Json | Set-Content -LiteralPath 'D:\AI project\QLDAPM chat\docs\docker-relocation\switch-state.json' -Encoding utf8
& docker desktop start --detach *> "$recordRoot\desktop-start.log"
if ($LASTEXITCODE -ne 0) { throw 'DESKTOP_START_FAILED_KEEP_BOTH_DATASETS_AND_RECONCILE' }
$state | ConvertTo-Json
