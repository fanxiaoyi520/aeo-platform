#!/usr/bin/env python3
"""MV3-09 batch runner — run ads + ops + budget + linkage on SKU test set."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

from aeo_llm.provider import LLMResponse
from aeo_orchestrator.runner import (
    run_ads_task,
    run_ops_task,
    serialize_ads_result,
    serialize_ops_result,
)
from aeo_shared.ads_inventory_linkage import AdsInventoryLinkage
from aeo_shared.budget_optimizer import BudgetOptimizer

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TESTSET = ROOT / "pilot" / "sample-sku-testset.json"
DEFAULT_OUTPUT_DIR = ROOT / "pilot" / "reports"


def _default_output_path() -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_DIR / f"mv3-batch-{stamp}.json"


def load_testset(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError(f"Invalid testset format: {path}")
    return items


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
            "report": "Campaigns show strong ROI.",
        }
    )
    provider = AsyncMock()
    provider.chat.return_value = LLMResponse(content=body, model="test")
    return provider


def _mock_ops_provider() -> AsyncMock:
    body = json.dumps(
        {
            "inventory_alerts": [],
            "pricing_suggestions": [],
            "restock_recommendations": [],
            "report": "Inventory healthy.",
        }
    )
    provider = AsyncMock()
    provider.chat.return_value = LLMResponse(content=body, model="test")
    return provider


async def run_single(
    item: dict[str, Any],
    index: int,
    total: int,
) -> dict[str, Any]:
    sku = str(item.get("sku", f"SKU-{index}"))
    platform = item.get("platform", "amazon")
    market = item.get("market", "US")
    product_info = {
        "category": item.get("category", "general"),
        "name": item.get("product_name", sku),
    }

    print(f"[{index}/{total}] {item.get('id', sku)} — {sku} ({platform}/{market})")
    started = time.perf_counter()

    try:
        ads_provider = _mock_ads_provider()
        with patch("aeo_orchestrator.nodes.ads.get_llm_provider", return_value=ads_provider):
            ads_state = await run_ads_task(
                sku=sku,
                platform=platform,
                market=market,
                product_info=product_info,
                task_id=f"mv3-ads-{item.get('id', index)}",
            )
        ads_result = serialize_ads_result(ads_state)

        ops_provider = _mock_ops_provider()
        with patch("aeo_orchestrator.nodes.operations.get_llm_provider", return_value=ops_provider):
            ops_state = await run_ops_task(
                sku=sku,
                platform=platform,
                market=market,
                product_info=product_info,
                task_id=f"mv3-ops-{item.get('id', index)}",
            )
        ops_result = serialize_ops_result(ops_state)

        duration_ms = int((time.perf_counter() - started) * 1000)
        return {
            "sku": sku,
            "platform": platform,
            "market": market,
            "status": "completed",
            "duration_ms": duration_ms,
            "ads": ads_result.get("ads", {}),
            "ops": ops_result.get("ops", {}),
        }
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return {
            "sku": sku,
            "platform": platform,
            "market": market,
            "status": "failed",
            "error": str(exc),
            "duration_ms": duration_ms,
        }


async def run_batch(
    items: list[dict[str, Any]], *, limit: int | None = None
) -> list[dict[str, Any]]:
    subset = items[:limit] if limit else items
    results = []
    for i, item in enumerate(subset, start=1):
        result = await run_single(item, i, len(subset))
        results.append(result)
    return results


def run_budget_and_linkage() -> dict[str, Any]:
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
    projection = optimizer.project_roi("CAMP-001", snapshots, days=7)

    linkage = AdsInventoryLinkage()
    linkage_campaigns = [
        {"campaign_id": "C1", "status": "enabled", "sku": "S1", "daily_budget": Decimal("50")},
    ]
    linkage_snapshots = [{"campaign_id": "C1", "spend": Decimal("100")}]
    inventory = [{"sku": "S1", "available_quantity": 5}]
    linkage_recs = linkage.analyze(linkage_campaigns, linkage_snapshots, inventory)

    return {
        "budget_allocations": [
            {
                "campaign_id": a.campaign_id,
                "current_budget": str(a.current_budget),
                "suggested_budget": str(a.suggested_budget),
                "change_percent": a.change_percent,
            }
            for a in allocations
        ],
        "roi_projection": {
            "campaign_id": projection.campaign_id,
            "estimated_spend": str(projection.estimated_spend),
            "estimated_gmv": str(projection.estimated_gmv),
            "estimated_roi": projection.estimated_roi,
        },
        "linkage_recommendations": [
            {
                "campaign_id": r.campaign_id,
                "stock_status": r.stock_status,
                "suggested_budget": str(r.suggested_budget),
                "budget_change_percent": r.budget_change_percent,
            }
            for r in linkage_recs
        ],
    }


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    completed = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") == "failed")
    total_duration = sum(r.get("duration_ms", 0) for r in results)

    return {
        "total": len(results),
        "completed": completed,
        "failed": failed,
        "total_duration_ms": total_duration,
        "avg_duration_ms": total_duration // len(results) if results else 0,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MV3 ads+ops batch runner.")
    parser.add_argument("--testset", type=Path, default=DEFAULT_TESTSET)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    testset_path = args.testset if args.testset.is_absolute() else ROOT / args.testset
    items = load_testset(testset_path)

    output_path = args.output or _default_output_path()
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        print(f"Dry run: {min(args.limit, len(items))} SKUs from {testset_path}")
        for i, item in enumerate(items[: args.limit], start=1):
            print(f"  [{i}] {item.get('id', '?')} — {item.get('sku', '?')}")
        return 0

    results = asyncio.run(run_batch(items, limit=args.limit))
    budget_linkage = run_budget_and_linkage()
    summary = build_summary(results)

    output_data = {
        "summary": summary,
        "results": results,
        "budget_and_linkage": budget_linkage,
    }
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nBatch complete: {summary['completed']}/{summary['total']} completed")
    print(f"Avg duration: {summary['avg_duration_ms']}ms")
    print(f"Output: {output_path}")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
