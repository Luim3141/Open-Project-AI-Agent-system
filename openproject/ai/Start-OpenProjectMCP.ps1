[CmdletBinding()]
param([ValidateSet(19,20,21,22,23)][int]$UserId=21,[switch]$Remote)
$ErrorActionPreference='Stop'
$runtime=Join-Path $env:LOCALAPPDATA 'QLDAPM/openproject-ai'
$env:QLDAPM_AI_TOKEN_FILE=Join-Path $runtime "operator/user-$UserId.token"
if(-not (Test-Path -LiteralPath $env:QLDAPM_AI_TOKEN_FILE)){throw 'Member token missing. Complete local registration first; never paste it into chat.'}
$env:QLDAPM_AI_URL='http://127.0.0.1:18089'
if($Remote){
    $url=[IO.File]::ReadAllText((Join-Path $runtime 'current-url.txt')).Trim()
    if($url -notmatch '^https://[a-z0-9-]+\.trycloudflare\.com$'){throw 'Start a verified AI Quick Tunnel first.'}
    $env:QLDAPM_AI_URL=$url
}
Push-Location $PSScriptRoot
try { & (Join-Path $PSScriptRoot '.venv/Scripts/python.exe') -m gateway.stdio; exit $LASTEXITCODE }
finally { Pop-Location }
