param(
    [string]$ApiBase = "http://127.0.0.1:8000",
    [string]$WebBase = "http://127.0.0.1:3000"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env.prod"

function Get-EnvValue {
    param([string]$Key)
    if (-not (Test-Path $envFile)) {
        throw "Missing .env.prod — copy from .env.prod.example and set AUTH_API_KEY"
    }
    foreach ($line in Get-Content $envFile) {
        if ($line -match "^\s*#") { continue }
        if ($line -match "^${Key}=(.*)$") {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    throw "Missing ${Key} in .env.prod"
}

function Invoke-DemoStep {
    param(
        [string]$Name,
        [scriptblock]$Action
    )
    Write-Host "--- $Name ---" -ForegroundColor Cyan
    & $Action
}

function Assert-Status {
    param(
        [string]$Label,
        [int]$Status,
        [int]$Expected
    )
    if ($Status -ne $Expected) {
        throw "${Label}: expected HTTP ${Expected}, got ${Status}"
    }
    Write-Host "  OK ($Label -> $Status)" -ForegroundColor Green
}

Write-Host "==> Launch AEO production demo (S6-05)" -ForegroundColor Cyan
Write-Host "API: $ApiBase"
Write-Host "Web: $WebBase"
Write-Host ""

Invoke-DemoStep "Health (public)" {
    $r = Invoke-WebRequest -Uri "$ApiBase/health" -UseBasicParsing
    Assert-Status "GET /health" $r.StatusCode 200
}

Invoke-DemoStep "Ready (public)" {
    $r = Invoke-WebRequest -Uri "$ApiBase/ready" -UseBasicParsing
    Assert-Status "GET /ready" $r.StatusCode 200
    $body = $r.Content | ConvertFrom-Json
    if (-not $body.data.checks.database) {
        throw "database check failed"
    }
    if (-not $body.data.checks.redis) {
        throw "redis check failed"
    }
    Write-Host "  OK (database + redis)" -ForegroundColor Green
}

Invoke-DemoStep "Auth guard" {
  try {
    Invoke-WebRequest -Uri "$ApiBase/api/v1/tasks" -UseBasicParsing | Out-Null
    throw "Expected 401 without API key"
  } catch {
    $status = $_.Exception.Response.StatusCode.value__
    Assert-Status "GET /api/v1/tasks (no key)" $status 401
  }
}

$apiKey = Get-EnvValue "AUTH_API_KEY"
$headers = @{ Authorization = "Bearer $apiKey" }

Invoke-DemoStep "Knowledge stats (authenticated)" {
    $r = Invoke-WebRequest -Uri "$ApiBase/api/v1/knowledge/stats" -Headers $headers -UseBasicParsing
    Assert-Status "GET /api/v1/knowledge/stats" $r.StatusCode 200
    $stats = ($r.Content | ConvertFrom-Json).data
    Write-Host "  documents: $($stats.document_count), chunks: $($stats.chunk_count)" -ForegroundColor Gray
}

Invoke-DemoStep "Audit logs (authenticated)" {
    $r = Invoke-WebRequest -Uri "$ApiBase/api/v1/audit-logs?limit=5" -Headers $headers -UseBasicParsing
    Assert-Status "GET /api/v1/audit-logs" $r.StatusCode 200
    $items = ($r.Content | ConvertFrom-Json).data.items
    Write-Host "  recent audit entries: $($items.Count)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "==> Demo smoke checks passed" -ForegroundColor Green
Write-Host "Next: open $WebBase/tasks/new for full HITL walkthrough"
Write-Host "API docs: $ApiBase/docs"
