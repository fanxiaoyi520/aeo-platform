$ErrorActionPreference = "Stop"
. "$PSScriptRoot\docker-cli.ps1"

$root = Get-ProjectRoot
$composeFile = "infra/compose/docker-compose.prod.yml"
$envFile = ".env.prod"

if (-not (Test-Path (Join-Path $root $envFile))) {
    $example = Join-Path $root ".env.prod.example"
    if (Test-Path $example) {
        Copy-Item $example (Join-Path $root $envFile)
        Write-Host "Created $envFile from .env.prod.example — set real secrets before production use" -ForegroundColor Yellow
    } else {
        throw "Missing $envFile and .env.prod.example"
    }
}

Write-Host "==> Validating prod compose" -ForegroundColor Cyan
Invoke-DockerCompose -ComposeFile $composeFile -EnvFile $envFile -Arguments @("config") | Out-Null

Write-Host "==> Starting production environment (Docker)" -ForegroundColor Cyan
Invoke-DockerCompose -ComposeFile $composeFile -EnvFile $envFile -Arguments @("up", "-d", "--build")

Write-Host "==> Waiting for API to become healthy..."
Start-Sleep -Seconds 12

Write-Host "==> Running database migrations"
Invoke-DockerCompose -ComposeFile $composeFile -EnvFile $envFile -Arguments @(
    "exec", "-T", "api", "uv", "run", "alembic", "upgrade", "head"
)

Write-Host "==> Ingesting knowledge base (hash embeddings)"
Invoke-DockerCompose -ComposeFile $composeFile -EnvFile $envFile -Arguments @(
    "exec", "-T", "api", "uv", "run", "python", "/app/scripts/ingest_knowledge.py", "--reset", "--hash-embeddings"
)
if ($LASTEXITCODE -ne 0) {
    Write-Host "Knowledge ingest failed — run manually after fixing .env.prod" -ForegroundColor Yellow
}

Write-Host "==> Production environment ready" -ForegroundColor Green
Write-Host "Web:    http://127.0.0.1:3000"
Write-Host "API:    http://127.0.0.1:8000/docs"
Write-Host "Health: http://127.0.0.1:8000/health"
Write-Host "Ready:  http://127.0.0.1:8000/ready"
