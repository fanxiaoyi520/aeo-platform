#!/usr/bin/env python3
"""MV2-08 batch runner — run selection-to-content pipeline on SKU test set."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aeo_orchestrator.runner import (
    run_selection_to_content_task,
    serialize_selection_to_content_result,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TESTSET = ROOT / "pilot" / "sample-sku-testset.json"
DEFAULT_OUTPUT_DIR = ROOT / "pilot" / "reports"


def _default_output_path() -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_DIR / f"mv2-batch-{stamp}.json"


def load_testset(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError(f"Invalid testset format: {path}")
    return items


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
        state = await run_selection_to_content_task(
            sku=sku,
            platform=platform,
            market=market,
            product_info=product_info,
            task_id=f"mv2-{item.get('id', index)}",
        )
        result = serialize_selection_to_content_result(state)
        duration_ms = int((time.perf_counter() - started) * 1000)
        result["duration_ms"] = duration_ms
        result["status"] = "completed"
        return result
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return {
            "sku": sku,
            "platform": platform,
            "market": market,
            "status": "failed",
            "error": str(exc),
            "duration_ms": duration_ms,
            "stages_completed": [],
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


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    completed = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") == "failed")
    total_duration = sum(r.get("duration_ms", 0) for r in results)

    stage_counts: dict[str, int] = {}
    for r in results:
        for stage in r.get("stages_completed", []):
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

    return {
        "total": len(results),
        "completed": completed,
        "failed": failed,
        "total_duration_ms": total_duration,
        "avg_duration_ms": total_duration // len(results) if results else 0,
        "stage_counts": stage_counts,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MV2 selection-to-content batch runner.")
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
    summary = build_summary(results)

    output_data = {"summary": summary, "results": results}
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nBatch complete: {summary['completed']}/{summary['total']} completed")
    print(f"Avg duration: {summary['avg_duration_ms']}ms")
    print(f"Output: {output_path}")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
