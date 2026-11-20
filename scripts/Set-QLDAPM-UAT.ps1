[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$target=Join-Path $env:LOCALAPPDATA 'QLDAPM/openproject-ai/telegram-ai/ui-uat.json'
if (-not (Test-Path -LiteralPath (Split-Path $target))) { throw 'QLDAPM Telegram runtime is not initialized.' }
if (Test-Path -LiteralPath $target) {
    $file=Get-Item -LiteralPath $target
    if ($file.LinkType -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Linked credential file denied.' }
    $old=Get-Content -LiteralPath $target -Raw | ConvertFrom-Json
    if ($old.login -or $old.password) { throw 'Existing UAT credentials retained; no overwrite.' }
}
$login=(Read-Host 'QLDAPM login currently used in the web app').Trim()
$secure=Read-Host 'QLDAPM password (hidden; not sent to chat)' -AsSecureString
$buffer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $passwordValue=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($buffer)
    if (-not $login -or -not $passwordValue) { throw 'Both login and password are required.' }
    $data=@{login=$login;password=$passwordValue} | ConvertTo-Json
    [IO.File]::WriteAllText($target,$data,[Text.UTF8Encoding]::new($false))
    Write-Host 'Saved to the private local UAT file. No account password was changed.'
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($buffer)
    $passwordValue=$null; $data=$null; $secure.Dispose()
}
