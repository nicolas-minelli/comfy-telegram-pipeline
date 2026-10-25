#requires -Version 5.1
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$secureToken = Read-Host 'Token for your NEW test bot (hidden input)' -AsSecureString
$tokenPointer = [IntPtr]::Zero
$token = $null
$apiRoot = $null
try {
    $tokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
    $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPointer)
    if ($token -notmatch '^\d+:[A-Za-z0-9_-]+$') { throw 'Invalid token format.' }
    # Telegram Bot API embeds the token in the URL internally. Never print it or a raw HTTP error.
    $apiRoot = 'https://api.telegram.org/bot' + $token
    $info = Invoke-RestMethod -Uri ($apiRoot + '/getWebhookInfo') -TimeoutSec 15
    if (-not $info.ok) { throw 'Telegram did not accept the request.' }
    if ($info.result.url) {
        Write-Output 'Webhook already registered. Nothing changed; use a new test bot or retrieve the ID from its existing authorized workflow.'
        return
    }
    $challenge = '/whoami ' + [Guid]::NewGuid().ToString('N').Substring(0,12)
    Write-Output ('Send this exact text in a PRIVATE chat with your own test bot: ' + $challenge)
    Read-Host 'After sending it, press Enter here' | Out-Null
    $updates = Invoke-RestMethod -Uri ($apiRoot + '/getUpdates?timeout=0') -TimeoutSec 15
    if (-not $updates.ok) { throw 'Telegram did not return updates.' }
    $match = @($updates.result | Where-Object {
        $_.message.chat.type -eq 'private' -and $_.message.text -eq $challenge -and
        $_.message.from.is_bot -eq $false -and $_.message.chat.id -eq $_.message.from.id
    } | Select-Object -Last 1)
    if ($match.Count -ne 1) {
        Write-Output 'Matching private message not found. Check the bot username and retry. No webhook was changed.'
        return
    }
    [PSCustomObject]@{ user_id = [string]$match[0].message.from.id; chat_id = [string]$match[0].message.chat.id }
} catch {
    # Avoid exposing the token-bearing URL in a normal PowerShell error message.
    throw 'Identity lookup failed. Check the test bot token/network. Do not share raw HTTP errors or your token.'
} finally {
    if ($tokenPointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPointer) }
    $token = $null
    $apiRoot = $null
    $secureToken = $null
}
# No sendMessage, deleteWebhook, setWebhook or update offset changes.
