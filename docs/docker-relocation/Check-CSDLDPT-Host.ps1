$ErrorActionPreference='Stop'
$resultPath='D:\Docker\csdldpt-real-host-check.json'
$result=[ordered]@{at=(Get-Date -Format o); phase='STARTED'}
$result | ConvertTo-Json | Set-Content -LiteralPath $resultPath -Encoding UTF8
try {
    $root=Get-Item -LiteralPath 'C:\Users\LUIM\AppData\Local\Docker'
    $result.control=[ordered]@{attributes=$root.Attributes.ToString(); target=$root.Target}
    $result.children=@(Get-ChildItem -LiteralPath $root.FullName -Force | Select-Object Name,Attributes,Target)
    $result.registry=@(Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' | ForEach-Object {
        Get-ItemProperty $_.PSPath | Select-Object DistributionName,BasePath,VhdFileName
    })
    $p=New-Object Diagnostics.Process
    $p.StartInfo.FileName='C:\Program Files\Docker\Docker\resources\bin\docker.exe'
    $p.StartInfo.Arguments='info --format "{{.ID}} {{.Driver}} {{.Containers}} {{.Images}}"'
    $p.StartInfo.UseShellExecute=$false
    $p.StartInfo.CreateNoWindow=$true
    $p.StartInfo.RedirectStandardOutput=$true
    $p.StartInfo.RedirectStandardError=$true
    $p.Start() | Out-Null
    if (-not $p.WaitForExit(20000)) {
        $p.Kill()
        $result.docker='TIMEOUT'
    } else {
        $result.docker_exit=$p.ExitCode
        $result.docker=$p.StandardOutput.ReadToEnd().Trim()
        $result.docker_error=$p.StandardError.ReadToEnd().Trim()
    }
    $result.phase='COMPLETED'
} catch { $result.phase='FAILED'; $result.error=$_.Exception.Message }
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $resultPath -Encoding UTF8
