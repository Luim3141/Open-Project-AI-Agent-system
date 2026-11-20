$ErrorActionPreference = 'Stop'
$credentialPath = Join-Path $env:LOCALAPPDATA 'QLDAPM\jira-admin-scoped.dpapi'
$credentialPointer = [IntPtr]::Zero
try {
    if (Test-Path -LiteralPath $credentialPath) {
        $credentialSecret = Get-Content -LiteralPath $credentialPath -Raw | ConvertTo-SecureString
        $credentialPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($credentialSecret)
        $env:QLDAPM_JIRA_ADMIN_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($credentialPointer)
    }
    & 'D:\AI project\QLDAPM chat\.venv-jira-admin\Scripts\python.exe' "$PSScriptRoot\jira_admin_mcp.py"
    $serverExitCode = $LASTEXITCODE
} finally {
    $env:QLDAPM_JIRA_ADMIN_TOKEN = $null
    if ($credentialPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($credentialPointer)
    }
    if ($credentialSecret) { $credentialSecret.Dispose() }
}
exit $serverExitCode
