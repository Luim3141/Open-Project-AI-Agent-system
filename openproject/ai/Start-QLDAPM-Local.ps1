[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
# Initial provision/exception repair only; normal daily use is opening Docker Desktop.
& (Join-Path $PSScriptRoot '.venv/Scripts/python.exe') (Join-Path $PSScriptRoot 'local_runtime.py') start
if ($LASTEXITCODE -ne 0) { throw 'Local staging start failed. Inspect/reconcile before retry; no main promotion.' }
