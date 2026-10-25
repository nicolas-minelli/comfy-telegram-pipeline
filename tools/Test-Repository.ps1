#requires -Version 5.1
[CmdletBinding()]
param([string]$PythonPath)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
foreach ($scriptFile in (Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.ps1')) {
    $parseTokens = $null
    $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $scriptFile.FullName, [ref]$parseTokens, [ref]$parseErrors
    ) | Out-Null
    if (@($parseErrors).Count -gt 0) {
        $parseErrors | ForEach-Object { Write-Output $_.Message }
        throw ('PowerShell syntax check failed: ' + $scriptFile.Name)
    }
}
if (-not $PythonPath) {
    $candidate = Join-Path $env:LOCALAPPDATA 'Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { $PythonPath = $candidate }
    else { $PythonPath = (Get-Command python -ErrorAction Stop).Source }
}
Get-Command node -ErrorAction Stop | Out-Null
Push-Location $repoRoot
try {
    & node '.\tools\export-runtime-graphs.cjs'
    if ($LASTEXITCODE -ne 0) { throw 'Runtime graph test failed.' }
    & $PythonPath -B '.\tests\test_custom_node_contracts.py'
    if ($LASTEXITCODE -ne 0) { throw 'Custom node contract test failed.' }
    & $PythonPath -B '.\tests\test_local_configuration.py'
    if ($LASTEXITCODE -ne 0) { throw 'Local configuration test failed.' }
} finally {
    Pop-Location
}
Write-Output 'PowerShell parse checks and offline tests passed. No service or GPU test was performed.'
