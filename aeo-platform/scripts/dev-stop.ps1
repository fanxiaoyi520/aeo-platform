$ErrorActionPreference = "Stop"
. "$PSScriptRoot\docker-cli.ps1"
. "$PSScriptRoot\dev-lib.ps1"

Write-Host "==> Stopping AEO Platform dev environment" -ForegroundColor Cyan

Write-Host "==> Stopping local API + Web" -ForegroundColor Cyan
Stop-DevService -Name "api" -Port 8000
Stop-DevService -Name "web" -Port 3000

Write-Host "==> Stopping Docker (Postgres + Redis)" -ForegroundColor Cyan
Invoke-DockerCompose -ComposeFile "infra/compose/docker-compose.dev.yml" -Arguments @("stop", "postgres", "redis")

Write-DevStatus
Write-Host ""
Write-Host "Dev environment stopped." -ForegroundColor Green
