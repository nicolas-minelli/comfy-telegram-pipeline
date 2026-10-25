#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$OutputRoot,
    [Parameter(Mandatory=$true)][string]$TelegramWebhookUrl,
    [ValidateRange(1024,65535)][int]$N8nHostPort = 5678,
    [ValidateRange(1024,65535)][int]$GatewayHostPort = 5680,
    [ValidateRange(1,65535)][int]$PrivateHttpsPort = 443,
    [ValidatePattern('^[a-z0-9][a-z0-9_-]{0,50}$')][string]$ProjectName = 'telegram-ingress-example',
    [string]$PythonPath
)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
if (-not [IO.Path]::IsPathRooted($OutputRoot)) { throw 'OutputRoot must be an absolute path outside the repository.' }
if (-not $PythonPath) {
    $candidate = Join-Path $env:LOCALAPPDATA 'Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { $PythonPath = $candidate }
    else { $PythonPath = (Get-Command python -CommandType Application -ErrorAction Stop).Source }
}
$generator = Join-Path $PSScriptRoot 'configure_ingress.py'
& $PythonPath $generator --output-root $OutputRoot --telegram-webhook-url $TelegramWebhookUrl `
    --n8n-host-port $N8nHostPort --gateway-host-port $GatewayHostPort `
    --private-https-port $PrivateHttpsPort --project-name $ProjectName
if ($LASTEXITCODE -ne 0) { throw 'Ingress preparation failed. No service or Tailscale route was started.' }
Write-Output ('Review private files in: ' + $OutputRoot)
