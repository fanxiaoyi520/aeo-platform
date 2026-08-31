#!/usr/bin/env python3
"""MS7 batch pilot — run SKU test set and emit CSV metrics report (S7-02)."""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from aeo_orchestrator.hitl import approve_hitl, is_waiting_hitl, run_until_hitl
from aeo_orchestrator.runner import build_runner_graph
from aeo_orchestrator.state import TaskState, TaskStatus, initial_state
from aeo_shared.pilot_metrics import (
    PilotRunRecord,
    build_product_info,
    extract_pilot_record,
    load_pilot_testset,
    summarize_pilot_runs,
    write_pilot_csv,
    write_pilot_summary,
)
from langgraph.graph.state import CompiledStateGraph

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TESTSET = ROOT / "pilot" / "sample-sku-testset.json"
DEFAULT_OUTPUT_DIR = ROOT / "pilot" / "reports"


def _default_output_path() -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_DIR / f"batch-{stamp}.csv"


def _build_dry_run_records(items: list[dict[str, Any]]) -> list[PilotRunRecord]:
    return [
        extract_pilot_record(
            item,
            duration_ms=0,
            status="planned",
            hitl_required=False,
            auto_approved=False,
            degraded_mode=not bool(item.get("competitor_asins")),
            compliance_retries=0,
            generated=None,
            final_output=None,
        )
        for item in items
    ]


async def _run_single_item(
    item: dict[str, Any],
    graph: CompiledStateGraph[TaskState, None, TaskState, TaskState],
    *,
    auto_approve: bool,
) -> PilotRunRecord:
    started = time.perf_counter()
    product_info = build_product_info(item)
    platform = cast(Literal["amazon", "tiktok"], item["platform"])
    state = initial_state(
        task_id=f"pilot-{item['id']}",
        platform=platform,
        sku=str(item["sku"]),
        market=str(item.get("market", "US")),
        product_info=product_info,
    )
    try:
        result = await run_until_hitl(graph, state)
        hitl_required = is_waiting_hitl(graph, state["task_id"])
        auto_approved = False
        if auto_approve and hitl_required:
            result = await approve_hitl(graph, state["task_id"])
            auto_approved = True

        status = result.get("status", TaskStatus.FAILED)
        status_value = status.value if isinstance(status, TaskStatus) else str(status)
        duration_ms = int((time.perf_counter() - started) * 1000)
        return extract_pilot_record(
            item,
            duration_ms=duration_ms,
            status=status_value,
            hitl_required=hitl_required,
            auto_approved=auto_approved,
            degraded_mode=bool(result.get("degraded_mode", False)),
            compliance_retries=int(result.get("retry_count", 0)),
            generated=result.get("generated")
            if isinstance(result.get("generated"), dict)
            else None,
            final_output=result.get("final_output")
            if isinstance(result.get("final_output"), dict)
            else None,
            error=str(result["error"]) if result.get("error") else None,
        )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return extract_pilot_record(
            item,
            duration_ms=duration_ms,
            status="failed",
            hitl_required=False,
            auto_approved=False,
            degraded_mode=False,
            compliance_retries=0,
            generated=None,
            final_output=None,
            error=str(exc),
        )


async def run_batch(
    items: list[dict[str, Any]],
    *,
    auto_approve: bool,
) -> list[PilotRunRecord]:
    graph = build_runner_graph()
    records: list[PilotRunRecord] = []
    for index, item in enumerate(items, start=1):
        print(f"[{index}/{len(items)}] {item['id']} {item['sku']} ({item['platform']})")
        records.append(await _run_single_item(item, graph, auto_approve=auto_approve))
    return records


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MS7 pilot SKU batch and export metrics CSV.")
    parser.add_argument(
        "--testset",
        type=Path,
        default=DEFAULT_TESTSET,
        help="Path to pilot SKU test set JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="CSV output path (default: pilot/reports/batch-<timestamp>.csv)",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Auto-approve HITL for non-interactive batch runs",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Run only the first N SKUs from the test set",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate test set and write planned CSV without calling LLM",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    testset_path = args.testset if args.testset.is_absolute() else ROOT / args.testset
    items = load_pilot_testset(testset_path)
    if args.limit is not None:
        items = items[: args.limit]

    output_path = args.output or _default_output_path()
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    summary_path = output_path.with_suffix(".summary.json")

    if args.dry_run:
        records = _build_dry_run_records(items)
        write_pilot_csv(records, output_path)
        summary = summarize_pilot_runs(records)
        summary["mode"] = "dry_run"
        write_pilot_summary(summary, summary_path)
        print(f"Dry run: {len(records)} SKUs planned -> {output_path}")
        return 0

    records = asyncio.run(run_batch(items, auto_approve=args.auto_approve))
    write_pilot_csv(records, output_path)
    summary = summarize_pilot_runs(records)
    summary["mode"] = "live"
    write_pilot_summary(summary, summary_path)

    print(f"Batch complete: {summary['completed']}/{summary['total']} completed")
    print(f"CSV:     {output_path}")
    print(f"Summary: {summary_path}")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
