$ErrorActionPreference = "Stop"
. "$PSScriptRoot\docker-cli.ps1"

Write-Host "==> Stopping dev environment" -ForegroundColor Cyan
Invoke-DockerCompose -ComposeFile "infra/compose/docker-compose.dev.yml" -Arguments @("down")
