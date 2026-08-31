$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

Write-Host "==> Ingesting knowledge base (hash embeddings, no API key needed)" -ForegroundColor Cyan
$env:RAG_USE_HASH_EMBEDDINGS = "true"
uv run python scripts/ingest_knowledge.py --reset --hash-embeddings

Write-Host "==> Done. Total chunks indexed." -ForegroundColor Green
