#requires -Version 5.1
[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [Parameter(Mandatory=$true)][string]$PreparedRoot,
    [Parameter(Mandatory=$true)][string]$ComfyRoot
)
$ErrorActionPreference = 'Stop'
$settingsFile = Join-Path $PreparedRoot 'deployment\settings.local.json'
if (-not (Test-Path -LiteralPath $settingsFile -PathType Leaf)) { throw 'Prepared local deployment not found.' }
if (-not (Test-Path -LiteralPath (Join-Path $ComfyRoot 'main.py') -PathType Leaf)) {
    throw 'ComfyRoot must contain main.py. Select the intended Comfy instance.'
}
$customRoot = Join-Path $ComfyRoot 'custom_nodes'
if (-not (Test-Path -LiteralPath $customRoot -PathType Container)) { throw 'Comfy custom_nodes directory not found.' }
$names = @('n8n_job_control','n8n_video_finalizer')
# Check both destinations before copying either. Deliberately refuses an update/overwrite.
foreach ($name in $names) {
    $source = Join-Path $PreparedRoot ('deployment\custom_nodes\' + $name + '\__init__.py')
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing prepared source: $name" }
    if (Test-Path -LiteralPath (Join-Path $customRoot $name)) {
        throw "Destination already exists: $name. Existing installations are never overwritten by this script."
    }
}
foreach ($name in $names) {
    $destination = Join-Path $customRoot $name
    if ($PSCmdlet.ShouldProcess($destination, 'Install configured custom node in selected Comfy instance')) {
        New-Item -ItemType Directory -Path $destination -ErrorAction Stop | Out-Null
        Copy-Item -LiteralPath (Join-Path $PreparedRoot ('deployment\custom_nodes\' + $name + '\__init__.py')) `
            -Destination (Join-Path $destination '__init__.py') -ErrorAction Stop
    }
}
Write-Output 'No Comfy process was started or restarted. Load the selected instance after reviewing the configuration.'
