#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PreparedRoot,
    [string]$ComfyHostUrl = 'http://127.0.0.1:8188',
    [switch]$CheckDocker,
    [string]$ProjectName = 'comfy-pipeline-lab'
)
$ErrorActionPreference = 'Stop'
$config = Get-Content -LiteralPath (Join-Path $PreparedRoot 'deployment\settings.local.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$keyPath = Join-Path $config.media_root '.telegram-ui\comfy-control.key'
$report = [ordered]@{ key_file_exists = (Test-Path -LiteralPath $keyPath -PathType Leaf); queue_ok = $false; health_ok = $false }
$key = $null
try {
    $queue = Invoke-RestMethod -Uri ($ComfyHostUrl.TrimEnd('/') + '/queue') -TimeoutSec 8
    $report.queue_ok = ($null -ne $queue.queue_running -and $null -ne $queue.queue_pending)
    $report.running = @($queue.queue_running).Count
    $report.pending = @($queue.queue_pending).Count
} catch { $report.queue_error = 'Comfy queue unavailable. Check process, port, binding and firewall.' }
try {
    $key = [System.IO.File]::ReadAllText($keyPath).Trim()
    if ($key -notmatch '^[a-f0-9]{64}$') { throw 'Invalid local key format.' }
    $health = Invoke-RestMethod -Uri ($ComfyHostUrl.TrimEnd('/') + '/n8n/jobs/health') `
        -Headers @{ Authorization = ('Bearer ' + $key) } -TimeoutSec 8
    $report.health_ok = ($health.ok -eq $true)
    $report.protocol_ok = ($health.protocol_version -ge 2)
    $report.finalizer_ok = ($health.finalizer_available -eq $true -and $health.finalizer_named_output -eq $true)
    $report.aspect_ok = (@($health.capabilities) -contains 'aspect-ratio-v1')
    $report.shared_root_matches = ($health.shared_root.Replace('\','/').TrimEnd('/') -ieq $config.media_root.Replace('\','/').TrimEnd('/'))
    $report.output_root_matches = ($health.output_root.Replace('\','/').TrimEnd('/') -ieq $config.comfy_output_root.Replace('\','/').TrimEnd('/'))
    $boot = Get-Content -LiteralPath (Join-Path $config.media_root '.telegram-ui\comfy-boot.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $report.boot_matches = ($boot.boot_id -eq $health.boot_id)
    $info = Invoke-RestMethod -Uri ($ComfyHostUrl.TrimEnd('/') + '/object_info') -TimeoutSec 15
    $repoRoot = Split-Path $PSScriptRoot -Parent
    $required = Get-ChildItem -LiteralPath (Join-Path $repoRoot 'comfy\api') -Filter '*.json' | ForEach-Object {
        $graph = Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        $graph.PSObject.Properties.Value | ForEach-Object { $_.class_type }
    } | Sort-Object -Unique
    $report.missing_nodes = @($required | Where-Object { -not $info.PSObject.Properties[$_] })
} catch { $report.health_error = 'Integration check failed. Check the local key, plugin loading and matching roots; no secret is printed.' }
finally { $key = $null }
if ($CheckDocker) {
    # Only reads paths/key inside the selected container and queries /queue + /health.
    $nodeCode = @'
(async()=>{const fs=require('fs');const c={url:process.argv[1]};const k=fs.readFileSync('/files/.telegram-ui/comfy-control.key','utf8').trim();if(!/^[a-f0-9]{64}$/.test(k))throw Error();const q=await fetch(c.url+'/queue',{signal:AbortSignal.timeout(8000)});const h=await fetch(c.url+'/n8n/jobs/health',{headers:{Authorization:'Bearer '+k},signal:AbortSignal.timeout(8000)});const data=await h.json();console.log(JSON.stringify({container_queue_status:q.status,container_health_status:h.status,container_health_ok:data.ok===true,ltx_template_exists:fs.existsSync('/files/workflows/ltx.json'),output_mount_exists:fs.existsSync('/comfy-output')}));if(!q.ok||!h.ok)process.exitCode=1;})().catch(()=>{console.error('Container check failed; check mounts, key, backend URL and network. No key was printed.');process.exitCode=1;});
'@
    $composeFile = Join-Path $PreparedRoot 'deployment\compose.local.yaml'
    $probeUrl = $config.comfy_container_url.TrimEnd('/')
    & docker compose -p $ProjectName -f $composeFile exec -T n8n node -e $nodeCode $probeUrl
    $report.docker_probe_exit_code = $LASTEXITCODE
}
[PSCustomObject]$report | ConvertTo-Json -Depth 5
# Deliberately no queue mutation, /prompt submission, interrupt or credential output.
