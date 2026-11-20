[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot '.venv/Scripts/python.exe') (Join-Path $PSScriptRoot 'local_runtime.py') stop
if ($LASTEXITCODE -ne 0) { throw 'Stage Stop failed; do not retry active/unknown work automatically.' }
