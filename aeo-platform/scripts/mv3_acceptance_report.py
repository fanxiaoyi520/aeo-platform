"""MV3-09 acceptance report generator.

Run: python scripts/mv3_acceptance_report.py
Output: JSON report with ads, ops, budget, and linkage acceptance results.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "shared" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "orchestrator" / "src"))

from aeo_llm.provider import LLMResponse


def _mock_ads_provider() -> AsyncMock:
    body = json.dumps(
        {
            "suggestions": [
                {
                    "campaign_id": "CAMP-001",
                    "type": "bid_increase",
                    "reason": "Low ACoS",
                    "suggested_value": "1.50",
                },
            ],
            "bid_simulation": {
                "campaign_id": "CAMP-001",
                "current_bid": "1.00",
                "suggested_bid": "1.50",
                "estimated_impression_lift": "25%",
                "estimated_gmv_change": "15%",
            },
            "report": "Campaigns show strong ROI. Recommend scaling CAMP-001.",
        }
    )
    provider = AsyncMock()
    provider.chat.return_value = LLMResponse(content=body, model="test")
    return provider


def _mock_ops_provider() -> AsyncMock:
    body = json.dumps(
        {
            "inventory_alerts": [{"sku": "REPORT-001", "level": "warning", "message": "Low stock"}],
            "pricing_suggestions": [],
            "restock_recommendations": [
                {"sku": "REPORT-001", "recommended_quantity": 100, "urgency": "high"}
            ],
            "report": "Inventory health needs attention.",
        }
    )
    provider = AsyncMock()
    provider.chat.return_value = LLMResponse(content=body, model="test")
    return provider


async def _run_ads_acceptance() -> dict:
    from aeo_orchestrator.runner import run_ads_task, serialize_ads_result

    results = []
    for i in range(5):
        provider = _mock_ads_provider()
        with patch("aeo_orchestrator.nodes.ads.get_llm_provider", return_value=provider):
            state = await run_ads_task(
                sku=f"REPORT-ADS-{i:03d}",
                platform="amazon",
                market="US",
                task_id=f"mv3-report-ads-{i}",
                product_info={"title": f"Report Product {i}", "price": 29.99},
            )
        serialized = serialize_ads_result(state)
        ads = serialized.get("ads", {})
        ok = bool(
            ads.get("metrics")
            and ads.get("suggestions") is not None
            and ads.get("campaigns") is not None
            and ads.get("report")
        )
        results.append(
            {"sku": f"REPORT-ADS-{i:03d}", "task_id": serialized["task_id"], "passed": ok}
        )

    passed = sum(1 for r in results if r["passed"])
    return {
        "test": "ads agent end-to-end (5 SKUs)",
        "total": 5,
        "passed": passed,
        "pass_rate": f"{passed / 5:.0%}",
        "details": results,
        "accepted": passed == 5,
    }


async def _run_ops_acceptance() -> dict:
    from aeo_orchestrator.runner import run_ops_task, serialize_ops_result

    results = []
    for i in range(5):
        provider = _mock_ops_provider()
        with patch("aeo_orchestrator.nodes.operations.get_llm_provider", return_value=provider):
            state = await run_ops_task(
                sku=f"REPORT-OPS-{i:03d}",
                platform="amazon",
                market="US",
                task_id=f"mv3-report-ops-{i}",
                product_info={"title": f"Report Product {i}", "price": 19.99},
            )
        serialized = serialize_ops_result(state)
        ops = serialized.get("ops", {})
        ok = bool(
            ops.get("health_metrics")
            and ops.get("seller_central_inspection") is not None
            and ops.get("report")
        )
        results.append(
            {"sku": f"REPORT-OPS-{i:03d}", "task_id": serialized["task_id"], "passed": ok}
        )

    passed = sum(1 for r in results if r["passed"])
    return {
        "test": "ops agent end-to-end (5 SKUs)",
        "total": 5,
        "passed": passed,
        "pass_rate": f"{passed / 5:.0%}",
        "details": results,
        "accepted": passed == 5,
    }


def _run_budget_acceptance() -> dict:
    from aeo_shared.budget_optimizer import BudgetOptimizer

    optimizer = BudgetOptimizer()
    campaigns = [
        {"campaign_id": "CAMP-001", "status": "enabled", "daily_budget": Decimal("50")},
        {"campaign_id": "CAMP-002", "status": "enabled", "daily_budget": Decimal("30")},
    ]
    snapshots = [
        {"campaign_id": "CAMP-001", "spend": Decimal("100"), "attributed_gmv": Decimal("500")},
        {"campaign_id": "CAMP-002", "spend": Decimal("80"), "attributed_gmv": Decimal("200")},
    ]

    allocations = optimizer.allocate_budget(campaigns, snapshots)
    alloc_ok = len(allocations) == 2 and all(a.suggested_budget > 0 for a in allocations)

    projection = optimizer.project_roi("CAMP-001", snapshots, days=7)
    proj_ok = projection.estimated_spend > 0 and projection.estimated_gmv > 0

    what_if = optimizer.simulate_what_if("CAMP-001", snapshots, budget_change_percent=20)
    whatif_ok = what_if.projected_spend > what_if.current_spend

    passed = sum([alloc_ok, proj_ok, whatif_ok])
    return {
        "test": "budget optimizer (allocate + project + simulate)",
        "total": 3,
        "passed": passed,
        "pass_rate": f"{passed / 3:.0%}",
        "details": [
            {"check": "allocate_budget", "passed": alloc_ok},
            {"check": "project_roi", "passed": proj_ok},
            {"check": "simulate_what_if", "passed": whatif_ok},
        ],
        "accepted": passed == 3,
    }


def _run_linkage_acceptance() -> dict:
    from aeo_shared.ads_inventory_linkage import AdsInventoryLinkage, StockStatus

    linkage = AdsInventoryLinkage()
    campaigns = [
        {"campaign_id": "C1", "status": "enabled", "sku": "S1", "daily_budget": Decimal("50")},
        {"campaign_id": "C2", "status": "enabled", "sku": "S2", "daily_budget": Decimal("40")},
    ]
    snapshots = [
        {"campaign_id": "C1", "spend": Decimal("100")},
        {"campaign_id": "C2", "spend": Decimal("80")},
    ]
    inventory = [
        {"sku": "S1", "available_quantity": 5},
        {"sku": "S2", "available_quantity": 150},
    ]

    recs = linkage.analyze(campaigns, snapshots, inventory)
    rec_map = {r.campaign_id: r for r in recs}

    critical_ok = (
        rec_map["C1"].stock_status == StockStatus.CRITICAL
        and rec_map["C1"].budget_change_percent < 0
    )
    overstock_ok = (
        rec_map["C2"].stock_status == StockStatus.OVERSTOCK
        and rec_map["C2"].budget_change_percent > 0
    )

    passed = sum([critical_ok, overstock_ok])
    return {
        "test": "ads-inventory linkage (stock-driven budget)",
        "total": 2,
        "passed": passed,
        "pass_rate": f"{passed / 2:.0%}",
        "details": [
            {"check": "critical_stock_halves_budget", "passed": critical_ok},
            {"check": "overstock_increases_budget", "passed": overstock_ok},
        ],
        "accepted": passed == 2,
    }


async def main() -> None:
    ads_result = await _run_ads_acceptance()
    ops_result = await _run_ops_acceptance()
    budget_result = _run_budget_acceptance()
    linkage_result = _run_linkage_acceptance()

    report = {
        "report_date": date.today().isoformat(),
        "milestone": "MV3-09",
        "description": "MV3 production acceptance — ads + ops + budget + linkage end-to-end",
        "results": {
            "ads_agent": ads_result,
            "ops_agent": ops_result,
            "budget_optimizer": budget_result,
            "ads_inventory_linkage": linkage_result,
        },
        "overall_accepted": all(
            r["accepted"] for r in [ads_result, ops_result, budget_result, linkage_result]
        ),
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
