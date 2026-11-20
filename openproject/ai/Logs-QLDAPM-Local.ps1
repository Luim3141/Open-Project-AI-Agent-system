[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot '.venv/Scripts/python.exe') (Join-Path $PSScriptRoot 'local_runtime.py') logs
if ($LASTEXITCODE -ne 0) { throw 'Private log capture failed; no raw logs have been printed.' }
