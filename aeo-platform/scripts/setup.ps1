$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> AEO Platform setup" -ForegroundColor Cyan

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..."
    irm https://astral.sh/uv/0.4.18/install.ps1 | iex
}

Write-Host "==> Sync Python dependencies"
uv sync --all-packages --group dev

if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    Write-Host "==> Install frontend workspace (pnpm)"
    pnpm install
} else {
    Write-Host "pnpm not found — skip frontend deps (install Node 20 + pnpm 9.12 for apps/web)" -ForegroundColor Yellow
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example — please set LLM_API_KEY" -ForegroundColor Yellow
}

Write-Host "==> Setup complete" -ForegroundColor Green
Write-Host "Next: .\scripts\dev-start.ps1"
