#!/usr/bin/env python3
"""MV5-03 report generator — read batch results and produce ROI comparison report."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

from aeo_shared.batch_metrics import AgentExecRecord, SkuBatchResult
from aeo_shared.roi_comparison import CostBaseline, build_full_report

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "pilot" / "reports"


def load_batch_results(path: Path) -> list[SkuBatchResult]:
    data = json.loads(path.read_text(encoding="utf-8"))
    results_data = data.get("results", data) if isinstance(data, dict) else data
    if not isinstance(results_data, list):
        raise ValueError(f"Invalid batch results format: {path}")

    results: list[SkuBatchResult] = []
    for item in results_data:
        agents = [
            AgentExecRecord(
                agent=a.get("agent", "unknown"),
                status=a.get("status", "unknown"),
                duration_ms=a.get("duration_ms", 0),
                platform=a.get("platform", "amazon"),
                degraded=a.get("degraded", False),
                error=a.get("error"),
            )
            for a in item.get("agents", [])
        ]
        results.append(
            SkuBatchResult(
                sku_id=item.get("sku_id", item.get("id", "unknown")),
                sku=item.get("sku", "unknown"),
                platform=item.get("platform", "amazon"),
                market=item.get("market", "US"),
                agents=agents,
            )
        )
    return results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MV5-03 ROI comparison report generator.")
    parser.add_argument("--input", type=Path, required=True, help="Batch results JSON from MV5-02")
    parser.add_argument("--output", type=Path, default=None, help="Output report path")
    parser.add_argument(
        "--ai-cost",
        type=Decimal,
        default=Decimal("0.001"),
        help="AI cost per task (default: 0.001)",
    )
    parser.add_argument(
        "--human-cost",
        type=Decimal,
        default=Decimal("0.05"),
        help="Human cost per task (default: 0.05)",
    )
    parser.add_argument(
        "--avg-sales",
        type=Decimal,
        default=Decimal("1000.00"),
        help="Average monthly sales per SKU (default: 1000.00)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    input_path = args.input if args.input.is_absolute() else ROOT / args.input
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return 1

    results = load_batch_results(input_path)
    if not results:
        print("Warning: No results found in input file", file=sys.stderr)

    baseline = CostBaseline(
        ai_cost_per_task=args.ai_cost,
        human_cost_per_task=args.human_cost,
        avg_monthly_sales_per_sku=args.avg_sales,
    )

    report = build_full_report(results, baseline, testset_path=str(input_path))

    output_path = args.output or (DEFAULT_OUTPUT_DIR / "mv5-03-roi-report.json")
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Report generated: {output_path}")
    print(f"  Total SKUs: {report.summary['total_skus']}")
    print(f"  Automation rate: {report.summary['automation_rate']}")
    print(f"  AI ROI: {report.summary['ai_roi']}")
    print(f"  Human ROI: {report.summary['human_roi']}")
    print(f"  ROI lift: {report.summary['roi_lift']}")

    kpi_passed = all(check["passed"] for check in report.kpi_check)
    print(f"  KPI check: {'PASS' if kpi_passed else 'FAIL'}")

    return 0 if kpi_passed else 1


if __name__ == "__main__":
    sys.exit(main())
