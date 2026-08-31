param(
    [switch]$LocalApi
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\docker-cli.ps1"

$Root = Get-ProjectRoot
$WebEnv = Join-Path $Root "apps\web\.env.local"
$Example = Join-Path $Root "apps\web\.env.local.example"

if (-not (Test-Path $WebEnv) -and (Test-Path $Example)) {
    Copy-Item $Example $WebEnv
}

function Get-WslHostIp {
    $raw = (wsl hostname -I 2>$null)
    if (-not $raw) { return $null }
    $ip = $raw.Trim().Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)[0]
    if ($ip -match '^\d+\.\d+\.\d+\.\d+$') { return $ip }
    return $null
}

$apiUrl = "http://127.0.0.1:8000"
if (-not $LocalApi -and (Test-WslDockerCli)) {
    $wslIp = Get-WslHostIp
    if ($wslIp) {
        $apiUrl = "http://${wslIp}:8000"
        Write-Host "WSL Docker detected — API_BASE_URL=$apiUrl" -ForegroundColor Yellow
    }
}

$authKey = "dev-api-key-change-in-production"
if (Test-Path (Join-Path $Root ".env")) {
    foreach ($line in Get-Content (Join-Path $Root ".env")) {
        if ($line -match '^\s*AUTH_API_KEY\s*=\s*(.+)\s*$') {
            $authKey = $Matches[1].Trim()
            break
        }
    }
}

$content = @"
# Auto-synced by scripts/sync-web-env.ps1 — do not hand-edit API_BASE_URL when using WSL Docker
API_BASE_URL=$apiUrl
AUTH_API_KEY=$authKey
"@

Set-Content -Path $WebEnv -Value $content.TrimEnd() -Encoding utf8
Write-Host "Updated $WebEnv" -ForegroundColor Green
