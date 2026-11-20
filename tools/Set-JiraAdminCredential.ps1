# Run by the owner in an interactive PowerShell, not by the agent.
[CmdletBinding()]
param([switch]$Replace)
$ErrorActionPreference = 'Stop'
$credentialDirectory = Join-Path $env:LOCALAPPDATA 'QLDAPM'
$credentialPath = Join-Path $credentialDirectory 'jira-admin-scoped.dpapi'
if ((Test-Path -LiteralPath $credentialPath) -and -not $Replace) {
    throw 'Credential exists. Explicitly use -Replace only for an approved replacement.'
}
Write-Host 'Create a Jira scoped API token: read:jira-user, read:jira-work, manage:jira-configuration.'
Write-Host 'Use hiepk40c@gmail.com, name QLDAPM-Codex-admin, expiry 30 days. Never paste it in chat.'
Write-Host 'URL: https://id.atlassian.com/manage-profile/security/api-tokens'
$credentialSecret = Read-Host 'Paste the new scoped API token (hidden)' -AsSecureString
if ($credentialSecret.Length -eq 0) { throw 'Empty token; nothing saved.' }
try {
    $null = New-Item -ItemType Directory -Path $credentialDirectory -Force
    $encryptedCredential = ConvertFrom-SecureString -SecureString $credentialSecret
    [IO.File]::WriteAllText($credentialPath, $encryptedCredential)
    Write-Host 'Saved encrypted DPAPI credential outside repository. No API call performed.'
} finally {
    $credentialSecret.Dispose()
    $encryptedCredential = $null
}
