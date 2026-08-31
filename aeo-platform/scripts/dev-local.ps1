$ErrorActionPreference = "Stop"
. "$PSScriptRoot\docker-cli.ps1"

Write-Host "==> AEO Platform local dev (no Docker)" -ForegroundColor Cyan

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found. Run .\scripts\setup.ps1 first." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example" -ForegroundColor Yellow
}

Get-Content ".env" | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    $parts = $_ -split '=', 2
    if ($parts.Count -eq 2) {
        Set-Item -Path "env:$($parts[0].Trim())" -Value $parts[1].Trim()
    }
}

Write-Host ""
Write-Host "Open in browser:" -ForegroundColor Green
Write-Host "  http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  http://127.0.0.1:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "For full stack (PostgreSQL+Redis), install Docker CLI:" -ForegroundColor Yellow
Write-Host "  .\scripts\install-docker-cli.ps1" -ForegroundColor White
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

Set-Location apps/api
uv run uvicorn aeo_api.main:app --host 127.0.0.1 --port 8000 --reload
