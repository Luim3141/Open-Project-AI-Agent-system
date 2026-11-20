$ErrorActionPreference='Stop'
$control='C:\Users\LUIM\AppData\Local\Docker'
$entries=@(Get-ChildItem -LiteralPath $control -Force | Select-Object Name,Attributes,Target)
$registrations=@(Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' | ForEach-Object {
    Get-ItemProperty $_.PSPath | Select-Object PSChildName,DistributionName,BasePath,VhdFileName
})
$settings=Get-Content -LiteralPath 'C:\Users\LUIM\AppData\Roaming\Docker\settings-store.json' -Raw | ConvertFrom-Json
$result=[ordered]@{
    at=(Get-Date -Format o); identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
    control_root=(Get-Item -LiteralPath $control | Select-Object FullName,Attributes,Target)
    entries=$entries; registry=$registrations; custom_wsl=$settings.CustomWslDistroDir
    containerd_store=$settings.UseContainerdSnapshotter
    real_engine_exists=(Test-Path -LiteralPath ($control+'\wsl\main\ext4.vhdx'))
    d_engine_exists=(Test-Path -LiteralPath 'D:\Docker\wsl\main\ext4.vhdx')
    local_docker_roots=@(Get-ChildItem -LiteralPath 'C:\Users\LUIM\AppData\Local' -Directory -Filter 'Docker*' | Select-Object Name,Target)
}
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath 'D:\Docker\relocation-host-state.json' -Encoding UTF8
