# HISTORICAL one-time migration record. Do not rerun; see CHECKPOINT.md and MSIX path caveat.
$ErrorActionPreference='Stop'
$receipt='D:\Docker\real-host-switch.json'
try {
    if (Get-Process -Name 'com.docker.backend','Docker Desktop' -ErrorAction SilentlyContinue) { throw 'Desktop must be stopped' }
    & 'C:\Windows\System32\wsl.exe' --shutdown
    if ($LASTEXITCODE -ne 0) { throw 'WSL shutdown failed' }
    foreach ($path in 'D:\Docker\wsl\main\ext4.vhdx','D:\Docker\wsl\disk\docker_data.vhdx') {
        $gate=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
        $gate.Dispose()
    }
    $rows=@(Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' | ForEach-Object { Get-ItemProperty $_.PSPath })
    $distro=@($rows | Where-Object DistributionName -eq 'docker-desktop')
    if ($distro.Count -ne 1) { throw 'Expected one Docker registration' }
    $before=$distro[0] | Select-Object PSChildName,DistributionName,BasePath,VhdFileName
    $before | ConvertTo-Json | Set-Content -LiteralPath 'D:\Docker\real-registry-before.json' -Encoding UTF8
    $control='C:\Users\LUIM\AppData\Local\Docker'
    $stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
    $retained=@()
    foreach ($part in 'wsl','log','tasks') {
        $path=Join-Path $control $part
        if (Test-Path -LiteralPath $path) {
            $item=Get-Item -LiteralPath $path
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw ('Unexpected real junction: '+$part) }
            $name=$part+'.retained-'+$stamp
            Rename-Item -LiteralPath $path -NewName $name
            $retained += Join-Path $control $name
        }
        New-Item -ItemType Junction -Path $path -Target ('D:\Docker\'+$part) | Out-Null
    }
    # Socket files belong to the old stopped process; retain them instead of deleting.
    foreach ($path in ($control+'\run'),'C:\Users\LUIM\AppData\Local\docker-secrets-engine') {
        if (Test-Path -LiteralPath $path) {
            $parent=Split-Path $path -Parent
            $name=(Split-Path $path -Leaf)+'.retained-'+$stamp
            Rename-Item -LiteralPath $path -NewName $name
            $retained += Join-Path $parent $name
        }
        New-Item -ItemType Directory -Path $path | Out-Null
    }
    Set-ItemProperty -LiteralPath $distro[0].PSPath -Name BasePath -Value '\\?\D:\Docker\wsl\main'
    $settingsPath='C:\Users\LUIM\AppData\Roaming\Docker\settings-store.json'
    $settings=Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
    $settings | Add-Member -NotePropertyName CustomWslDistroDir -NotePropertyValue 'D:\Docker\wsl' -Force
    [IO.File]::WriteAllText($settingsPath, ($settings | ConvertTo-Json -Depth 20), (New-Object Text.UTF8Encoding($false)))
    [ordered]@{ phase='REAL_HOST_SWITCHED'; before=$before; after_base_path=(Get-ItemProperty -LiteralPath $distro[0].PSPath).BasePath; retained=$retained; deleted_items=0; formatted_disks=0 } |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $receipt -Encoding UTF8
    Start-Process -FilePath 'C:\Program Files\Docker\Docker\Docker Desktop.exe' -WindowStyle Hidden
} catch {
    [ordered]@{phase='FAILED_KEEP_ALL_COPIES'; error=$_.Exception.Message} | ConvertTo-Json | Set-Content -LiteralPath $receipt -Encoding UTF8
    exit 1
}
