#!/usr/bin/env python3
"""MV5-05 — Trial report generator.

Reads trial run data and produces structured JSON + text summary report
with availability, success rate, P95 latency, and recovery time metrics.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aeo_shared.trial_monitor import (
    TrialMonitor,
    TrialRecord,
    TrialStatus,
    HealthStatus,
    compute_availability,
    compute_p95_latency,
    compute_recovery_time,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "pilot" / "reports"

AVAILABILITY_TARGET = 0.995
SUCCESS_RATE_TARGET = 0.90
P95_LATENCY_TARGET_MS = 5000


def load_trial_data(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data


def parse_records(data: dict[str, Any]) -> list[TrialRecord]:
    records: list[TrialRecord] = []
    for r in data.get("records", []):
        records.append(
            TrialRecord(
                run_id=r["run_id"],
                started_at=datetime.fromisoformat(r["started_at"]),
                status=TrialStatus(r["status"]),
                duration_ms=r["duration_ms"],
                skus_processed=r["skus_processed"],
                health_status=HealthStatus(r["health_status"]),
                error=r.get("error"),
            )
        )
    return records


def build_trial_report(
    trial_data: dict[str, Any],
    *,
    trial_path: str,
) -> dict[str, Any]:
    records = parse_records(trial_data)
    monitor = TrialMonitor()
    for r in records:
        monitor.add(r)

    summary = monitor.build_summary()
    config = trial_data.get("trial_config", {})

    availability = summary["availability"]
    success_rate = summary["success_rate"]
    p95_latency = summary["p95_latency_ms"]

    kpi_check = [
        {
            "metric": "availability",
            "target": AVAILABILITY_TARGET,
            "actual": availability,
            "passed": availability >= AVAILABILITY_TARGET,
        },
        {
            "metric": "success_rate",
            "target": SUCCESS_RATE_TARGET,
            "actual": success_rate,
            "passed": success_rate >= SUCCESS_RATE_TARGET,
        },
        {
            "metric": "p95_latency_ms",
            "target": P95_LATENCY_TARGET_MS,
            "actual": p95_latency,
            "passed": p95_latency <= P95_LATENCY_TARGET_MS,
        },
    ]

    report = {
        "milestone": "MV5",
        "task": "MV5-05",
        "generated_at": datetime.now(UTC).isoformat(),
        "trial_path": trial_path,
        "trial_config": config,
        "summary": {
            "total_runs": summary["total_runs"],
            "success_count": summary["success_count"],
            "failure_count": summary["failure_count"],
            "success_rate": success_rate,
            "availability": availability,
            "avg_duration_ms": summary["avg_duration_ms"],
            "p95_latency_ms": p95_latency,
            "recovery_time_seconds": summary["recovery_time_seconds"],
            "total_skus_processed": summary["total_skus_processed"],
        },
        "kpi_check": kpi_check,
        "records": [r.to_dict() for r in records],
    }

    return report


def format_text_report(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("MV5-05 生产部署 7x24 试运行报告")
    lines.append("=" * 60)
    lines.append("")

    config = report.get("trial_config", {})
    lines.append(f"试运行周期: {config.get('duration_hours', '?')}h (间隔 {config.get('interval_hours', '?')}h)")
    lines.append(f"开始时间: {config.get('started_at', 'N/A')}")
    lines.append(f"结束时间: {config.get('ended_at', 'N/A')}")
    lines.append(f"模式: {'模拟' if config.get('dry_run') else '实际'}")
    lines.append("")

    summary = report["summary"]
    lines.append("-" * 40)
    lines.append("运行统计")
    lines.append("-" * 40)
    lines.append(f"总运行次数: {summary['total_runs']}")
    lines.append(f"成功次数: {summary['success_count']}")
    lines.append(f"失败次数: {summary['failure_count']}")
    lines.append(f"成功率: {summary['success_rate']:.2%}")
    lines.append(f"处理 SKU 总数: {summary['total_skus_processed']}")
    lines.append("")

    lines.append("-" * 40)
    lines.append("性能指标")
    lines.append("-" * 40)
    lines.append(f"可用性: {summary['availability']:.2%} (目标 ≥{AVAILABILITY_TARGET:.1%})")
    lines.append(f"平均延迟: {summary['avg_duration_ms']:.0f}ms")
    lines.append(f"P95 延迟: {summary['p95_latency_ms']}ms (目标 ≤{P95_LATENCY_TARGET_MS}ms)")
    lines.append(f"故障恢复时间: {summary['recovery_time_seconds']:.0f}s")
    lines.append("")

    lines.append("-" * 40)
    lines.append("KPI 检查")
    lines.append("-" * 40)
    passed_count = 0
    for kpi in report["kpi_check"]:
        status = "PASS" if kpi["passed"] else "FAIL"
        if kpi["passed"]:
            passed_count += 1
        lines.append(f"  {kpi['metric']}: {kpi['actual']:.4f} (目标 {kpi['target']}) [{status}]")
    lines.append("")
    lines.append(f"KPI 通过: {passed_count}/{len(report['kpi_check'])}")
    lines.append("")

    all_passed = all(k["passed"] for k in report["kpi_check"])
    if all_passed:
        lines.append("结论: 试运行通过，满足生产部署要求")
    else:
        lines.append("结论: 试运行未通过，需调优后重试")
    lines.append("=" * 60)

    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MV5-05 trial report generator.")
    parser.add_argument("trial_data", type=Path, help="Path to trial run JSON output")
    parser.add_argument("--output", type=Path, default=None, help="Output report path (JSON)")
    parser.add_argument("--text", action="store_true", help="Also output text report")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    trial_path = args.trial_data
    if not trial_path.is_absolute():
        trial_path = ROOT / trial_path

    if not trial_path.is_file():
        print(f"Error: trial data not found: {trial_path}", file=sys.stderr)
        return 1

    trial_data = load_trial_data(trial_path)
    report = build_trial_report(trial_data, trial_path=str(trial_path))

    output_path = args.output
    if output_path is None:
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        output_path = DEFAULT_OUTPUT_DIR / f"mv5-trial-report-{stamp}.json"
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Report saved: {output_path}")

    if args.text:
        text_report = format_text_report(report)
        text_path = output_path.with_suffix(".txt")
        text_path.write_text(text_report, encoding="utf-8")
        print(f"Text report saved: {text_path}")
        print()
        print(text_report)

    passed_kpis = sum(1 for k in report["kpi_check"] if k["passed"])
    total_kpis = len(report["kpi_check"])
    print(f"\nKPI: {passed_kpis}/{total_kpis} passed")

    return 0 if all(k["passed"] for k in report["kpi_check"]) else 1


if __name__ == "__main__":
    sys.exit(main())
