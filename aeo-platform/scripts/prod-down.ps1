$ErrorActionPreference = "Stop"
. "$PSScriptRoot\docker-cli.ps1"

$composeFile = "infra/compose/docker-compose.prod.yml"
$envFile = ".env.prod"
$envPath = Join-Path (Get-ProjectRoot) $envFile
if (-not (Test-Path $envPath)) {
    $envFile = $null
}

Write-Host "==> Stopping production environment" -ForegroundColor Cyan
Invoke-DockerCompose -ComposeFile $composeFile -EnvFile $envFile -Arguments @("down")
