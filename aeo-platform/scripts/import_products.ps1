param(
    [string]$Csv = "knowledge/templates/pilot-sku-batch.csv",
    [switch]$SyncTestset,
    [switch]$Ingest,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$argsList = @("scripts/import_products.py", $Csv)
if ($SyncTestset) { $argsList += "--sync-testset" }
if ($Ingest) { $argsList += "--ingest" }
if ($DryRun) { $argsList += "--dry-run" }

Write-Host "==> Importing products from $Csv" -ForegroundColor Cyan
uv run python @argsList
