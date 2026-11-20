[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot '.venv/Scripts/python.exe') (Join-Path $PSScriptRoot 'local_runtime.py') repair
if ($LASTEXITCODE -ne 0) { throw 'Repair failed; reconcile private state before retry. No main promotion or seeder.' }
