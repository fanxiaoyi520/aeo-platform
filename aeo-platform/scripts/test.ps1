$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )
    Write-Host "--- $Name ---"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Write-Host "==> Running tests" -ForegroundColor Cyan

Invoke-Step "ruff check" { uv run ruff check apps packages }
Invoke-Step "ruff format check" { uv run ruff format --check apps packages }
Invoke-Step "mypy" { uv run python -m mypy apps packages }
Invoke-Step "pytest" { uv run pytest apps/api/tests apps/browser/tests apps/orchestrator/tests packages/shared/tests packages/llm/tests packages/rag/tests --cov=apps --cov=packages --cov-report=term-missing:skip-covered --cov-fail-under=70 }

Write-Host "==> All checks passed" -ForegroundColor Green
