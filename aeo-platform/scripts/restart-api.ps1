$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> Stopping API on port 8000" -ForegroundColor Cyan
for ($attempt = 1; $attempt -le 5; $attempt++) {
    $connections = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if (-not $connections) { break }
    foreach ($conn in $connections) {
        $procId = $conn.OwningProcess
        cmd /c "taskkill /PID $procId /T /F >nul 2>&1"
        Write-Host "  stopped PID $procId"
    }
    Start-Sleep -Seconds 2
}
$remaining = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($remaining) {
    Write-Host "Port 8000 still in use. Close remaining listeners manually." -ForegroundColor Red
    exit 1
}

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
        $parts = $_ -split '=', 2
        if ($parts.Count -eq 2) {
            Set-Item -Path "env:$($parts[0].Trim())" -Value $parts[1].Trim()
        }
    }
}

$env:RAG_USE_HASH_EMBEDDINGS = "true"
if ($env:UV_PROJECT_ENVIRONMENT) {
    Write-Host "Using venv: $env:UV_PROJECT_ENVIRONMENT"
}

Write-Host "==> Starting API (http://127.0.0.1:8000)" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Set-Location apps\api
uv run uvicorn aeo_api.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir src --reload-dir ..\orchestrator\src --reload-dir ..\..\packages\llm\src
