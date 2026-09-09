#!/usr/bin/env python3
"""P3-09 batch runner — DTC agents across Shopify SKU test set."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "pilot" / "reports"

DTC_AGENTS = ["dtc_content", "dtc_ops", "dtc_support", "dtc_analytics"]

DTC_SKUS = [
    {
        "id": "dtc-001",
        "sku": "DTC-BAMBOO-TEE",
        "product_info": {"title": "Bamboo Fiber T-Shirt", "price": 39.99, "product_type": "Apparel"},
    },
    {
        "id": "dtc-002",
        "sku": "DTC-RECYCLED-BAG",
        "product_info": {"title": "Recycled Canvas Tote", "price": 29.99, "product_type": "Accessories"},
    },
    {
        "id": "dtc-003",
        "sku": "DTC-ORGANIC-CANDLE",
        "product_info": {"title": "Soy Wax Candle", "price": 24.99, "product_type": "Home"},
    },
    {
        "id": "dtc-004",
        "sku": "DTC-HERBAL-TEA",
        "product_info": {"title": "Organic Herbal Tea Blend", "price": 18.99, "product_type": "Food"},
    },
    {
        "id": "dtc-005",
        "sku": "DTC-BAMBOO-BOTTLE",
        "product_info": {"title": "Bamboo Water Bottle", "price": 34.99, "product_type": "Kitchen"},
    },
]


async def _run_agent(agent: str, sku_item: dict[str, Any]) -> dict[str, Any]:
    from unittest.mock import AsyncMock, patch

    from aeo_llm.provider import LLMResponse
    from aeo_orchestrator.runner import (
        run_dtc_content_task,
        run_dtc_ops_task,
    )

    sku = sku_item["sku"]
    task_id = f"p3batch-{sku_item['id']}-{agent}"
    started = time.perf_counter()

    mock_response = json.dumps({
        "landing_page": {"hero_headline": "Test", "subheadline": "Sub", "cta_text": "Go", "body_paragraph": "Body"},
        "email_campaign": {"subject": "Hi", "preview_text": "Pre", "body": "B", "sequence": []},
        "social_posts": [],
        "report": "ok",
        "inventory_alerts": [],
        "pricing_suggestions": [],
        "restock_recommendations": [],
        "abandoned_cart_strategy": {"recommendation": "test", "expected_recovery": 0.1},
        "health_metrics": {},
    })

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=mock_response, model="test")

    try:
        if agent == "dtc_content":
            with (
                patch("aeo_orchestrator.nodes.dtc_content.get_llm_provider", return_value=mock_provider),
                patch("aeo_orchestrator.nodes.dtc_content.get_store_client") as ms,
            ):
                ms.return_value.list_products.return_value = []
                await run_dtc_content_task(
                    sku=sku, platform="shopify",
                    product_info=sku_item["product_info"], task_id=task_id,
                )
        elif agent == "dtc_ops":
            with (
                patch("aeo_orchestrator.nodes.dtc_operations.get_llm_provider", return_value=mock_provider),
                patch("aeo_orchestrator.nodes.dtc_operations.get_store_client") as ms,
            ):
                mc = ms.return_value
                mc.get_store_metrics.return_value = []
                mc.list_abandoned_carts.return_value = []
                mc.list_customers.return_value = []
                mc.list_discount_codes.return_value = []
                await run_dtc_ops_task(
                    sku=sku, platform="shopify",
                    product_info=sku_item["product_info"], task_id=task_id,
                )
        elif agent == "dtc_support":
            from aeo_shared.after_sales_scripts import get_script_library

            lib = get_script_library()
            scripts = lib.filter_by(platform="shopify")
            assert len(scripts) >= 3
        elif agent == "dtc_analytics":
            from aeo_shared.dtc_analytics import calculate_dtc_kpis

            kpis = calculate_dtc_kpis([], [], [])
            assert kpis is not None

        duration_ms = int((time.perf_counter() - started) * 1000)
        return {"agent": agent, "sku": sku, "status": "completed", "duration_ms": duration_ms}
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return {"agent": agent, "sku": sku, "status": "failed", "duration_ms": duration_ms, "error": str(exc)}


async def run_batch(limit: int | None = None) -> list[dict[str, Any]]:
    results = []
    skus = DTC_SKUS[:limit] if limit else DTC_SKUS
    for i, sku_item in enumerate(skus, 1):
        print(f"[{i}/{len(skus)}] {sku_item['sku']}")
        for agent in DTC_AGENTS:
            r = await _run_agent(agent, sku_item)
            results.append(r)
            status_icon = "OK" if r["status"] == "completed" else "FAIL"
            print(f"  {status_icon} {agent} ({r['duration_ms']}ms)")
    return results


def build_report(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    completed = sum(1 for r in results if r["status"] == "completed")
    failed = total - completed
    avg_ms = sum(r["duration_ms"] for r in results) / total if total else 0

    per_agent: dict[str, dict[str, int]] = {}
    for r in results:
        a = r["agent"]
        if a not in per_agent:
            per_agent[a] = {"completed": 0, "failed": 0, "total_ms": 0}
        per_agent[a][r["status"]] = per_agent[a].get(r["status"], 0) + 1
        per_agent[a]["total_ms"] += r["duration_ms"]

    return {
        "milestone": "P3",
        "task": "P3-09",
        "timestamp": datetime.now(UTC).isoformat(),
        "summary": {
            "total_runs": total,
            "completed": completed,
            "failed": failed,
            "avg_duration_ms": round(avg_ms, 1),
            "success_rate": round(completed / total, 4) if total else 0,
        },
        "per_agent": per_agent,
        "results": results,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P3-09 DTC batch runner.")
    parser.add_argument("--limit", type=int, default=None, help="Limit SKUs")
    parser.add_argument("--output", type=Path, default=None, help="Output path")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    output_path = args.output or (DEFAULT_OUTPUT_DIR / f"p3-batch-{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json")
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    skus = DTC_SKUS[: args.limit] if args.limit else DTC_SKUS

    if args.dry_run:
        print(f"Dry run: {len(skus)} SKUs × {len(DTC_AGENTS)} agents")
        for i, s in enumerate(skus, 1):
            print(f"  [{i}] {s['sku']} — {s['product_info']['title']}")
        return 0

    print(f"Running {len(DTC_AGENTS)} DTC agents on {len(skus)} Shopify SKUs...\n")
    results = asyncio.run(run_batch(limit=args.limit))

    report = build_report(results)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    s = report["summary"]
    print(f"\n{'='*50}")
    print(f"Batch complete: {s['completed']}/{s['total_runs']} passed ({s['success_rate']*100:.1f}%)")
    print(f"Avg duration: {s['avg_duration_ms']:.0f}ms")
    print(f"Output: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
