# P1-SPAPI mock 端到端演示 — 无需卖家号
# 用法: cd aeo-platform; .\scripts\demo_spapi_mock.ps1
# 可选: .\scripts\demo_spapi_mock.ps1 -FullRun  # 需 .env 中 LLM_* 配置

param(
    [string]$Sku = "HOMEBREW-KETTLE-1L",
    [switch]$FullRun
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:AMAZON_DATA_SOURCE = "mock"

function Invoke-Step {
    param([string]$Name, [scriptblock]$Action)
    Write-Host "--- $Name ---" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "==> SP-API Mock Demo (P1-SPAPI)" -ForegroundColor Green
Write-Host "SKU: $Sku"
Write-Host "AMAZON_DATA_SOURCE: $env:AMAZON_DATA_SOURCE"
Write-Host ""

Invoke-Step "Step 1: Load mock listing (aeo-integrations)" {
    uv run python -c @"
from aeo_integrations.amazon import get_listings_client
listing = get_listings_client().get_listing('$Sku')
print(f'  SKU:    {listing.sku}')
print(f'  Title:  {listing.title}')
print(f'  Brand:  {listing.brand}')
print(f'  Status: {listing.status}')
print(f'  Price:  {listing.price} {listing.currency}')
print(f'  Bullets: {len(listing.bullets)}')
"@
}

Invoke-Step "Step 2: research_agent enrichment (aeo-orchestrator)" {
    uv run python -c @"
import asyncio
from aeo_orchestrator.nodes.research import research_node
from aeo_orchestrator.state import initial_state

state = initial_state(
    task_id='demo-spapi-mock',
    platform='amazon',
    sku='$Sku',
    product_info={'competitor_asins': ['B07TZ5YHJZ', 'B08C7KG5LP']},
)
result = asyncio.run(research_node(state))
research = result['research']
product = result['product_info']
print(f'  amazon_listing_loaded: {research[\"amazon_listing_loaded\"]}')
print(f'  product_info.title:    {product.get(\"title\", \"\")}')
print(f'  keywords (first 3):    {research[\"keywords\"][:3]}')
print(f'  competitors:           {len(research[\"competitors\"])}')
print(f'  degraded:              {research[\"degraded\"]}')
"@
}

Invoke-Step "Step 3: Integration tests (pilot SKUs)" {
    uv run pytest packages/integrations/tests/test_amazon_mock.py -q --tb=no
}

if ($FullRun) {
    Invoke-Step "Step 4: Full listing graph (LLM required)" {
        uv run aeo-orchestrate run `
            --sku $Sku `
            --platform amazon `
            --market US `
            --competitor B07TZ5YHJZ `
            --competitor B08C7KG5LP `
            --auto-approve
    }
} else {
    Write-Host ""
    Write-Host "Skip full LLM run (use -FullRun to execute aeo-orchestrate CLI)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==> Mock demo passed" -ForegroundColor Green
Write-Host "Pilot SKUs: HOMEBREW-KETTLE-1L, HOMEBREW-VACUUM-S, KITCHEN-AIRFRYER-4QT, KITCHEN-BLENDER-PRO, GLOW-HAIRDRYER-ION"
Write-Host "Next: P1-03 feasibility -> docs/specs/P1-03-spapi-feasibility.md"
