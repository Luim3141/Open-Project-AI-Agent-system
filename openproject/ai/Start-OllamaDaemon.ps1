# Start and Ensure Ollama Daemon with BGE-M3 Model for QLDAPM
$ErrorActionPreference = "Stop"
$daemonLock = [System.Threading.Mutex]::new($false, 'Local\QLDAPM-Ollama-Health')
if (-not $daemonLock.WaitOne(0)) { $daemonLock.Dispose(); return }
try {

$OllamaPath = Join-Path $env:LOCALAPPDATA 'Programs/Ollama/ollama.exe'
if (-not (Test-Path $OllamaPath)) {
    Write-Error "Ollama executable not found at $OllamaPath"
}

# 1. Check if Ollama is already listening on 11434
$running = $false
try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2
    if ($null -ne $res -and $null -ne $res.models) {
        $running = $true
        Write-Host "[OK] Ollama daemon is already running on port 11434."
    }
} catch {
    $running = $false
}

# 2. Launch background daemon if not running
if (-not $running) {
    if (Get-NetTCPConnection -LocalPort 11434 -State Listen -ErrorAction SilentlyContinue) {
        throw 'Port 11434 is occupied but Ollama health is invalid; inspect the existing listener before recovery.'
    }
    Write-Host "[INFO] Starting Ollama daemon in background..."
    Start-Process -FilePath $OllamaPath -ArgumentList "serve" -WindowStyle Hidden
    
    $attempts = 0
    while ($attempts -lt 15) {
        Start-Sleep -Seconds 1
        try {
            $check = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2
            if ($check) {
                Write-Host "[OK] Ollama daemon successfully started."
                $running = $true
                break
            }
        } catch {}
        $attempts++
    }
    if (-not $running) {
        Write-Error "Failed to start Ollama daemon after 15 seconds."
    }
}

# 3. Verify BGE-M3 model availability
$models = (Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags").models
$hasBge = $models | Where-Object { $_.name -like "*bge-m3*" }
if ($hasBge) {
    Write-Host "[OK] BGE-M3 model is active and ready."
} else {
    throw 'BGE-M3 is missing; recovery will not pull or change models automatically.'
}
} finally {
    $daemonLock.ReleaseMutex()
    $daemonLock.Dispose()
}
