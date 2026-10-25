#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$BaseRoot,
    [Parameter(Mandatory=$true)][ValidatePattern('^[1-9][0-9]{0,15}$')][string]$TelegramUserId,
    [Parameter(Mandatory=$true)][string]$ComfyOutputRoot,
    [Parameter(Mandatory=$true)][uri]$PrivateBaseUrl,
    [Parameter(Mandatory=$true)][uri]$PublicWebhookBaseUrl,
    [string]$ComfyContainerUrl = 'http://host.docker.internal:8188',
    [ValidateRange(1024,65535)][int]$N8nHostPort = 5681,
    [string]$PythonPath
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $ComfyOutputRoot -PathType Container)) {
    throw 'ComfyOutputRoot must be an existing output directory of the intended Comfy instance.'
}
if (-not $PythonPath) {
    $candidate = Join-Path $env:LOCALAPPDATA 'Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { $PythonPath = $candidate }
    else { $PythonPath = (Get-Command python -ErrorAction Stop).Source }
}
$generator = Join-Path $PSScriptRoot 'configure_local.py'
& $PythonPath $generator --base-root $BaseRoot --telegram-user-id $TelegramUserId `
    --comfy-output-root $ComfyOutputRoot --private-base-url $PrivateBaseUrl.AbsoluteUri `
    --public-webhook-base-url $PublicWebhookBaseUrl.AbsoluteUri `
    --comfy-container-url $ComfyContainerUrl --n8n-host-port $N8nHostPort
if ($LASTEXITCODE -ne 0) { throw 'Local preparation failed. No service was started.' }
