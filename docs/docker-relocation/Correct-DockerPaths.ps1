# HISTORICAL one-time migration record. Do not rerun; see CHECKPOINT.md and MSIX path caveat.
$ErrorActionPreference = 'Stop'
$controlRoot = 'C:\Users\LUIM\AppData\Local\Docker'
$dataRoot = 'D:\Docker'
$privateRoot = Join-Path $env:LOCALAPPDATA 'QLDAPM\openproject-ai\operator\docker-relocation-20261016'
if (Get-Process -Name '*docker*','vmmemWSL' -ErrorAction SilentlyContinue) { throw 'Docker/WSL must be stopped' }
$current = Get-Item -LiteralPath $controlRoot
if (($current.Attributes -band [IO.FileAttributes]::ReparsePoint) -and $current.Target -ne $dataRoot) { throw 'Unexpected current root target' }
foreach ($part in 'wsl\main\ext4.vhdx','wsl\disk\docker_data.vhdx') {
    if (-not (Test-Path -LiteralPath (Join-Path $dataRoot $part))) { throw 'Missing copied VHDX' }
}
$settingsPath = Join-Path $env:APPDATA 'Docker\settings-store.json'
if (-not (Test-Path -LiteralPath (Join-Path $privateRoot 'settings-before-direct-path.json'))) {
    Copy-Item -LiteralPath $settingsPath -Destination (Join-Path $privateRoot 'settings-before-direct-path.json')
}
$registryRows = @(Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' | ForEach-Object { Get-ItemProperty $_.PSPath })
$registryRows | Select-Object PSPath,PSChildName,DistributionName,BasePath,VhdFileName | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $privateRoot 'registry-before-correction-retry.json') -Encoding UTF8
$distro = @($registryRows | Where-Object DistributionName -eq 'docker-desktop')
if ($distro.Count -ne 1) { throw 'Expected exactly one registered Docker distro' }
$retainedLink = $controlRoot + '.redirect-retained-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
Rename-Item -LiteralPath $controlRoot -NewName (Split-Path $retainedLink -Leaf)
New-Item -ItemType Directory -Path $controlRoot -Force | Out-Null
if (Get-ChildItem -LiteralPath $controlRoot -Force) { throw 'Control root recreated by another process; stop before proceeding' }
Set-Acl -LiteralPath $controlRoot -AclObject (Get-Acl -LiteralPath 'C:\Users\LUIM\AppData\Local\Docker.retained-20261016-012335')
New-Item -ItemType Directory -Path (Join-Path $controlRoot 'run') | Out-Null
foreach ($part in 'wsl','log','tasks') {
    New-Item -ItemType Junction -Path (Join-Path $controlRoot $part) -Target (Join-Path $dataRoot $part) | Out-Null
}
Get-ChildItem -LiteralPath $dataRoot -File | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $controlRoot $_.Name)
}
$settings = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
$settings | Add-Member -NotePropertyName CustomWslDistroDir -NotePropertyValue 'D:\Docker\wsl' -Force
$settings | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $settingsPath -Encoding UTF8
# Direct physical path avoids WSL/HCS resolution through a redirected parent.
Set-ItemProperty -LiteralPath $distro[0].PSPath -Name BasePath -Value '\\?\D:\Docker\wsl\main'
[ordered]@{ phase='DIRECT_PATH_CONFIGURED'; control_root=$controlRoot; physical_wsl='D:\Docker\wsl'; retained_link=$retainedLink; registry_key=$distro[0].PSChildName; no_deletion=$true } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $privateRoot 'direct-path-correction.json') -Encoding UTF8
Write-Output 'Direct WSL path configured; original directories and redirect retained'
