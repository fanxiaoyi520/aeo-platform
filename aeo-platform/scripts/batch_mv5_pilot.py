#!/usr/bin/env python3
"""MV5-02 batch runner — run all 6 agents across 50-SKU multi-platform test set."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from aeo_shared.batch_metrics import (
    AgentExecRecord,
    BatchMetricsAggregator,
    KpiTarget,
    SkuBatchResult,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TESTSET = ROOT / "pilot" / "mv5-50sku-testset.json"
DEFAULT_OUTPUT_DIR = ROOT / "pilot" / "reports"

ALL_AGENTS = ["selection", "ads", "content", "operations", "support", "analytics"]

MV5_KPI_TARGETS: dict[str, KpiTarget] = {
    "automation_rate": KpiTarget(target=Decimal("0.40"), operator="gte"),
    "avg_duration_ms": KpiTarget(target=Decimal("5000"), operator="lte"),
    "degradation_rate": KpiTarget(target=Decimal("0.30"), operator="lte"),
    "platform_coverage": KpiTarget(target=Decimal("1.0"), operator="eq"),
}


def _default_output_path() -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_DIR / f"mv5-batch-{stamp}.json"


def load_testset(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError(f"Invalid testset format: {path}")
    return items


def _build_product_info(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "category": item.get("category", "general"),
        "name": item.get("product_name", ""),
        "price_usd": item.get("price_usd", 0),
        "monthly_sales": item.get("monthly_sales", 0),
        "keywords": item.get("keywords", []),
        "competitor_asins": item.get("competitor_asins", []),
        "knowledge_doc": item.get("knowledge_doc"),
    }


def _is_degraded(item: dict[str, Any], agent: str) -> bool:
    if agent == "selection" and not item.get("competitor_asins"):
        return True
    if agent == "content" and not item.get("knowledge_doc"):
        return True
    return False


async def _run_agent(
    agent: str,
    item: dict[str, Any],
) -> AgentExecRecord:
    from aeo_orchestrator.runner import (
        run_ads_task,
        run_analytics_task,
        run_image_copy_task,
        run_ops_task,
        run_selection_task,
        run_support_task,
        run_tiktok_video_task,
    )

    sku = str(item.get("sku", ""))
    platform = item.get("platform", "amazon")
    market = item.get("market", "US")
    product_info = _build_product_info(item)
    task_id = f"mv5-{item.get('id', '')}-{agent}"
    degraded = _is_degraded(item, agent)

    started = time.perf_counter()
    try:
        if agent == "selection":
            await run_selection_task(
                sku=sku, platform=platform, market=market,
                product_info=product_info, task_id=task_id,
            )
        elif agent == "ads":
            await run_ads_task(
                sku=sku, platform=platform, market=market,
                product_info=product_info, task_id=task_id,
            )
        elif agent == "content":
            if platform == "tiktok":
                await run_tiktok_video_task(
                    sku=sku, platform=platform, market=market,
                    product_info=product_info, task_id=task_id,
                )
            else:
                await run_image_copy_task(
                    sku=sku, platform=platform, market=market,
                    product_info=product_info, task_id=task_id,
                )
        elif agent == "operations":
            await run_ops_task(
                sku=sku, platform=platform, market=market,
                product_info=product_info, task_id=task_id,
            )
        elif agent == "support":
            scenarios = item.get("support_scenarios", ["inquiry"])
            support_info = {**product_info, "scenario": scenarios[0] if scenarios else "inquiry"}
            await run_support_task(
                sku=sku, platform=platform, market=market,
                product_info=support_info, task_id=task_id,
            )
        elif agent == "analytics":
            await run_analytics_task(
                sku=sku, platform=platform, market=market,
                product_info=product_info, task_id=task_id,
            )

        duration_ms = int((time.perf_counter() - started) * 1000)
        return AgentExecRecord(
            agent=agent, status="completed", duration_ms=duration_ms,
            platform=platform, degraded=degraded,
        )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return AgentExecRecord(
            agent=agent, status="failed", duration_ms=duration_ms,
            platform=platform, degraded=degraded, error=str(exc),
        )


async def run_single_sku(
    item: dict[str, Any],
    *,
    agents: list[str],
) -> SkuBatchResult:
    agent_records: list[AgentExecRecord] = []
    for agent in agents:
        record = await _run_agent(agent, item)
        agent_records.append(record)

    return SkuBatchResult(
        sku_id=str(item.get("id", "")),
        sku=str(item.get("sku", "")),
        platform=str(item.get("platform", "amazon")),
        market=str(item.get("market", "US")),
        agents=agent_records,
    )


async def run_batch(
    items: list[dict[str, Any]],
    *,
    agents: list[str],
    limit: int | None = None,
) -> list[SkuBatchResult]:
    subset = items[:limit] if limit else items
    results: list[SkuBatchResult] = []
    for i, item in enumerate(subset, start=1):
        print(f"[{i}/{len(subset)}] {item.get('id', '?')} — {item.get('sku', '?')} ({item.get('platform', '?')})")
        result = await run_single_sku(item, agents=agents)
        results.append(result)
    return results


def build_report(
    sku_results: list[SkuBatchResult],
    *,
    testset_path: str,
) -> dict[str, Any]:
    agg = BatchMetricsAggregator()
    for r in sku_results:
        agg.add(r)

    summary = agg.build_summary()

    total_runs = summary["total_agent_runs"]
    completed = summary["completed"]
    degraded = summary["degraded_runs"]
    platforms_seen = len(summary["per_platform"])

    kpi_values: dict[str, Decimal] = {}
    if total_runs > 0:
        kpi_values["automation_rate"] = Decimal(str(completed)) / Decimal(str(total_runs))
        kpi_values["degradation_rate"] = Decimal(str(degraded)) / Decimal(str(total_runs))
    kpi_values["avg_duration_ms"] = Decimal(str(summary["avg_duration_ms"]))
    kpi_values["platform_coverage"] = Decimal("1.0") if platforms_seen >= 3 else Decimal("0.0")

    kpi_checks = agg.check_kpis(MV5_KPI_TARGETS, kpi_values)

    return {
        "milestone": "MV5",
        "task": "MV5-02",
        "testset": testset_path,
        "timestamp": datetime.now(UTC).isoformat(),
        "summary": summary,
        "per_sku": [r.to_dict() for r in sku_results],
        "kpi_check": kpi_checks,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MV5 50-SKU batch runner.")
    parser.add_argument("--testset", type=Path, default=DEFAULT_TESTSET)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--agents", nargs="*", default=ALL_AGENTS, choices=ALL_AGENTS)
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

    agents = args.agents or ALL_AGENTS
    limit = args.limit or len(items)

    if args.dry_run:
        print(f"Dry run: {min(limit, len(items))} SKUs × {len(agents)} agents from {testset_path}")
        for i, item in enumerate(items[:limit], start=1):
            print(f"  [{i}] {item.get('id', '?')} — {item.get('sku', '?')} ({item.get('platform', '?')})")
        return 0

    print(f"Running {len(agents)} agents on {min(limit, len(items))} SKUs...")
    sku_results = asyncio.run(run_batch(items, agents=agents, limit=limit))

    report = build_report(sku_results, testset_path=str(testset_path))
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8",
    )

    s = report["summary"]
    print(f"\nBatch complete: {s['completed']}/{s['total_agent_runs']} agent runs passed")
    print(f"SKUs: {s['total_skus']} | Degraded: {s['degraded_runs']}")
    print(f"Platforms: {', '.join(s['per_platform'].keys())}")

    passed_kpis = sum(1 for c in report["kpi_check"] if c["passed"])
    total_kpis = len(report["kpi_check"])
    print(f"KPIs: {passed_kpis}/{total_kpis} passed")
    print(f"Output: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
