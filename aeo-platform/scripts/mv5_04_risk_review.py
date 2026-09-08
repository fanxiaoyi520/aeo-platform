#!/usr/bin/env python3
"""MV5-04 risk review generator — read batch results and produce incident review report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from aeo_shared.batch_metrics import AgentExecRecord, SkuBatchResult
from aeo_shared.risk_review import build_review_report

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
    parser = argparse.ArgumentParser(description="MV5-04 risk review report generator.")
    parser.add_argument("--input", type=Path, required=True, help="Batch results JSON from MV5-02")
    parser.add_argument("--output", type=Path, default=None, help="Output report path")
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

    report = build_review_report(results, testset_path=str(input_path))

    output_path = args.output or (DEFAULT_OUTPUT_DIR / "mv5-04-risk-review.json")
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Risk review report generated: {output_path}")
    print(f"  Total tasks: {report.summary['total_tasks']}")
    print(f"  Total incidents: {report.summary['total_incidents']}")
    print(f"  Incident rate: {report.summary['incident_rate']:.2%}")
    print(f"  Critical incidents: {report.summary['critical_incidents']}")
    print(f"  Tuning suggestions: {len(report.tuning_suggestions)}")

    kpi_passed = all(check["passed"] for check in report.kpi_check)
    print(f"  KPI check: {'PASS' if kpi_passed else 'FAIL'}")

    return 0 if kpi_passed else 1


if __name__ == "__main__":
    sys.exit(main())
