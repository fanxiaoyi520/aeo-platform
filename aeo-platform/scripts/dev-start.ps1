param(
    [switch]$Ingest,
    [switch]$Rebuild,
    [switch]$Status
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\docker-cli.ps1"
. "$PSScriptRoot\dev-lib.ps1"

$Root = Get-DevRoot
Set-Location $Root

if ($Status) {
    Write-DevStatus
    exit 0
}

Write-Host "==> AEO Platform quick dev start" -ForegroundColor Cyan
Write-Host "    (Postgres/Redis in Docker; API + Web on Windows — no image rebuild)" -ForegroundColor Gray
Write-Host ""

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found. Run .\scripts\setup.ps1 first." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example" -ForegroundColor Yellow
}
Import-DotEnv (Join-Path $Root ".env")

if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    Write-Host "pnpm not found — web UI will not start (install Node 20 + pnpm 9.12)" -ForegroundColor Yellow
}

# Web talks to local API on Windows, not WSL-mapped IP.
& "$PSScriptRoot\sync-web-env.ps1" -LocalApi | Out-Null

Write-Host "==> Starting Postgres + Redis (Docker)" -ForegroundColor Cyan
$composeFile = "infra/compose/docker-compose.dev.yml"
$composeArgs = @("up", "-d")
if ($Rebuild) { $composeArgs += "--build" }
$composeArgs += @("postgres", "redis")
Invoke-DockerCompose -ComposeFile $composeFile -Arguments $composeArgs

Write-Host "==> Waiting for Postgres" -ForegroundColor Cyan
Start-Sleep -Seconds 4

Write-Host "==> Running migrations" -ForegroundColor Cyan
$env:DB_URL = "postgresql+asyncpg://aeo:aeo_dev_password@localhost:5432/aeo"
$env:DB_URL_SYNC = "postgresql+psycopg://aeo:aeo_dev_password@localhost:5432/aeo"
Push-Location (Join-Path $Root "apps\api")
uv run alembic upgrade head | Out-Null
Pop-Location

if ($Ingest) {
    Write-Host "==> Ingesting knowledge base" -ForegroundColor Cyan
    & "$PSScriptRoot\ingest.ps1"
}

Write-Host "==> Starting API (background)" -ForegroundColor Cyan
$env:RAG_USE_HASH_EMBEDDINGS = "true"
$apiRoot = Join-Path $Root "apps\api"
$apiCmd = @(
    "`$env:DB_URL='postgresql+asyncpg://aeo:aeo_dev_password@localhost:5432/aeo'"
    "`$env:DB_URL_SYNC='postgresql+psycopg://aeo:aeo_dev_password@localhost:5432/aeo'"
    "`$env:RAG_USE_HASH_EMBEDDINGS='true'"
    "`$env:LLM_BASE_URL='$($env:LLM_BASE_URL)'"
    "`$env:LLM_API_KEY='$($env:LLM_API_KEY)'"
    "`$env:LLM_MODEL='$($env:LLM_MODEL)'"
    "`$env:LLM_TIMEOUT_SECONDS='$($env:LLM_TIMEOUT_SECONDS)'"
    "uv run uvicorn aeo_api.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir src --reload-dir ..\orchestrator\src --reload-dir ..\..\packages\llm\src"
)
Start-DevService -Name "api" -WorkingDirectory $apiRoot -Command $apiCmd -Port 8000 | Out-Null

if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    Write-Host "==> Starting Web (background)" -ForegroundColor Cyan
    $webRoot = Join-Path $Root "apps\web"
    $webCmd = @("pnpm dev")
    Start-DevService -Name "web" -WorkingDirectory $webRoot -Command $webCmd -Port 3000 | Out-Null
}

Write-Host "==> Waiting for services" -ForegroundColor Cyan
$apiReady = Wait-HttpOk -Url "http://127.0.0.1:8000/health" -TimeoutSec 90
$webReady = $false
if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    $webReady = Wait-HttpOk -Url "http://127.0.0.1:3000" -TimeoutSec 120
}

Write-Host ""
if ($apiReady) {
    Write-Host "API ready:  http://127.0.0.1:8000/docs" -ForegroundColor Green
} else {
    Write-Host "API not ready — see $(Get-ServiceLogFile 'api')" -ForegroundColor Red
}

if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    if ($webReady) {
        Write-Host "Web ready:  http://127.0.0.1:3000" -ForegroundColor Green
        Write-Host "New task:   http://127.0.0.1:3000/tasks/new" -ForegroundColor Green
    } else {
        Write-Host "Web not ready — see $(Get-ServiceLogFile 'web')" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Stop all: .\scripts\dev-stop.ps1" -ForegroundColor Gray
Write-Host "Status:   .\scripts\dev-start.ps1 -Status" -ForegroundColor Gray

if (-not $apiReady) { exit 1 }
