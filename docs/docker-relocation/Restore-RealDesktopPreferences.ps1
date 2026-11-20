# HISTORICAL one-time migration record. Do not rerun; see CHECKPOINT.md and MSIX path caveat.
$ErrorActionPreference='Stop'
try {
    if (Get-Process -Name 'com.docker.backend','Docker Desktop' -ErrorAction SilentlyContinue) { throw 'Desktop must be stopped before restoring preferences' }
    $path='C:\Users\LUIM\AppData\Roaming\Docker\settings-store.json'
    $settings=Get-Content -LiteralPath 'D:\Docker\settings-original-preserved.json' -Raw | ConvertFrom-Json
    if ($settings.UseContainerdSnapshotter -ne $true) { throw 'Original containerd store setting missing' }
    $settings | Add-Member -NotePropertyName CustomWslDistroDir -NotePropertyValue 'D:\Docker\wsl' -Force
    [IO.File]::WriteAllText($path, ($settings | ConvertTo-Json -Depth 20), (New-Object Text.UTF8Encoding($false)))
    'PASS: original settings restored, containerd enabled, WSL data root D' | Set-Content -LiteralPath 'D:\Docker\real-settings-restored.txt'
    Start-Process -FilePath 'C:\Program Files\Docker\Docker\Docker Desktop.exe' -WindowStyle Hidden
} catch {
    ('FAIL: '+$_.Exception.Message) | Set-Content -LiteralPath 'D:\Docker\real-settings-restored.txt'
    exit 1
}
