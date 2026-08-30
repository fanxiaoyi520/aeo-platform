$ErrorActionPreference = "Stop"
. "$PSScriptRoot\docker-cli.ps1"

Write-Host "==> Starting dev environment (Docker CLI)" -ForegroundColor Cyan

$composeFile = "infra/compose/docker-compose.dev.yml"
Invoke-DockerCompose -ComposeFile $composeFile -Arguments @("up", "-d", "--build")

Write-Host "==> Waiting for services..."
Start-Sleep -Seconds 8

Write-Host "==> Running migrations"
$root = Get-ProjectRoot
$env:DB_URL = "postgresql+asyncpg://aeo:aeo_dev_password@localhost:5432/aeo"
$env:DB_URL_SYNC = "postgresql+psycopg://aeo:aeo_dev_password@localhost:5432/aeo"

if (Test-DockerCli) {
    Push-Location (Join-Path $root "apps\api")
    uv run alembic upgrade head
    Pop-Location
} elseif (Test-WslDockerCli) {
    Push-Location (Join-Path $root "apps\api")
    $env:DB_URL = "postgresql+asyncpg://aeo:aeo_dev_password@localhost:5432/aeo"
    $env:DB_URL_SYNC = "postgresql+psycopg://aeo:aeo_dev_password@localhost:5432/aeo"
    uv run alembic upgrade head
    Pop-Location
}

Write-Host "==> Ingesting knowledge base (hash embeddings)"
& "$PSScriptRoot\ingest.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Knowledge ingest failed — run .\scripts\ingest.ps1 manually after fixing .env" -ForegroundColor Yellow
}

Write-Host "==> Dev environment ready" -ForegroundColor Green
Write-Host "Docs:  http://127.0.0.1:8000/docs"
Write-Host "Health: http://127.0.0.1:8000/health"
Write-Host "Ready:  http://127.0.0.1:8000/ready"
