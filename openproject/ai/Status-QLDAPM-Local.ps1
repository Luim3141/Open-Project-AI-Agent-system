[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot '.venv/Scripts/python.exe') (Join-Path $PSScriptRoot 'local_runtime.py') status
if ($LASTEXITCODE -ne 0) { throw 'Status unavailable: check Docker engine, private manifest and fixed stage identities.' }
