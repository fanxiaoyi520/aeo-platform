#!/usr/bin/env python3
"""MV5-06 — Final acceptance report generator.

Reads MV5-02~05 output data and produces a structured JSON + text summary
validating all six commercial KPIs (MV-BIZ-01 through MV-BIZ-06).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from aeo_shared.batch_metrics import SkuBatchResult, AgentExecRecord
from aeo_shared.roi_comparison import RoiComparisonReport, CostBaseline, build_full_report
from aeo_shared.risk_review import IncidentRecord, classify_incidents
from aeo_shared.trial_monitor import TrialRecord, TrialStatus, HealthStatus
from aeo_shared.final_acceptance import compute_final_acceptance

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "pilot" / "reports"


def load_batch_results(path: Path) -> list[SkuBatchResult]:
    data = json.loads(path.read_text(encoding="utf-8"))
    results: list[SkuBatchResult] = []
    for sku_data in data.get("per_sku", []):
        agents = [
            AgentExecRecord(
                agent=a["agent"],
                status=a["status"],
                duration_ms=a["duration_ms"],
                platform=a.get("platform", "amazon"),
                degraded=a.get("degraded", False),
                error=a.get("error"),
            )
            for a in sku_data.get("agents", [])
        ]
        results.append(
            SkuBatchResult(
                sku_id=sku_data["sku_id"],
                sku=sku_data["sku"],
                platform=sku_data["platform"],
                market=sku_data.get("market", "US"),
                agents=agents,
            )
        )
    return results


def load_trial_records(path: Path) -> list[TrialRecord]:
    data = json.loads(path.read_text(encoding="utf-8"))
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


def format_text_report(report_dict: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("MV5-06 商业终验报告")
    lines.append("=" * 60)
    lines.append("")

    overall = report_dict["overall_result"]
    lines.append(f"里程碑: {report_dict['milestone']}")
    lines.append(f"任务: {report_dict['task']}")
    lines.append(f"生成时间: {report_dict['generated_at']}")
    lines.append("")

    lines.append("-" * 40)
    lines.append("KPI 值")
    lines.append("-" * 40)
    kpi_values = report_dict["kpi_values"]
    lines.append(f"人工替代率: {kpi_values.get('automation_rate', 'N/A')}")
    lines.append(f"AI ROI ≥ 人工: {kpi_values.get('ai_roi_vs_human', 'N/A')}")
    lines.append(f"GMV 可追溯性: {kpi_values.get('gmv_traceability', 'N/A')}")
    lines.append(f"关键风控事故: {kpi_values.get('critical_incidents', 'N/A')}")
    lines.append(f"客服质量: {kpi_values.get('support_quality', 'N/A')}")
    lines.append(f"首审通过率: {kpi_values.get('first_pass_rate', 'N/A')}")
    lines.append("")

    lines.append("-" * 40)
    lines.append("KPI 检查")
    lines.append("-" * 40)
    passed_count = 0
    for kpi in report_dict["kpi_check"]:
        status = "PASS" if kpi["passed"] else "FAIL"
        if kpi["passed"]:
            passed_count += 1
        lines.append(f"  {kpi['metric']}: {kpi['actual']} (目标 {kpi['target']}) [{status}]")
    lines.append("")
    lines.append(f"KPI 通过: {passed_count}/{len(report_dict['kpi_check'])}")
    lines.append("")

    lines.append("-" * 40)
    lines.append("总体结果")
    lines.append("-" * 40)
    lines.append(f"全部通过: {'是' if overall['all_passed'] else '否'}")
    lines.append(f"通过数: {overall['passed_count']}/{overall['total_count']}")
    lines.append("")

    if overall["all_passed"]:
        lines.append("结论: MV5 商业终验通过，满足试点验收标准")
    else:
        lines.append("结论: MV5 商业终验未通过，需调优后重试")
    lines.append("=" * 60)

    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MV5-06 final acceptance report generator.")
    parser.add_argument("--batch-results", type=Path, default=None, help="MV5-02 batch results JSON")
    parser.add_argument("--trial-data", type=Path, default=None, help="MV5-05 trial data JSON")
    parser.add_argument("--support-quality", type=float, default=0.92, help="Support quality score (0-1)")
    parser.add_argument("--first-pass-rate", type=float, default=0.75, help="First-pass approval rate (0-1)")
    parser.add_argument("--output", type=Path, default=None, help="Output report path (JSON)")
    parser.add_argument("--text", action="store_true", help="Also output text report")
    parser.add_argument("--dry-run", action="store_true", help="Use simulated data for testing")
    return parser.parse_args(argv)


def generate_dry_run_data() -> tuple[list[SkuBatchResult], list[TrialRecord]]:
    batch_results = [
        SkuBatchResult(
            sku_id=f"SKU-{i}",
            sku=f"TEST-{i}",
            platform="amazon",
            market="US",
            agents=[
                AgentExecRecord(agent="selection", status="completed", duration_ms=100),
                AgentExecRecord(agent="ads", status="completed", duration_ms=100),
                AgentExecRecord(agent="content", status="completed", duration_ms=100),
            ],
        )
        for i in range(10)
    ]

    trial_records = [
        TrialRecord(
            run_id=f"run-{i}",
            started_at=datetime(2026, 9, 8, i, 0, 0, tzinfo=UTC),
            status=TrialStatus.SUCCESS,
            duration_ms=200,
            skus_processed=50,
            health_status=HealthStatus.HEALTHY,
        )
        for i in range(10)
    ]

    return batch_results, trial_records


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.dry_run:
        batch_results, trial_records = generate_dry_run_data()
    else:
        if not args.batch_results or not args.trial_data:
            print("Error: --batch-results and --trial-data required (or use --dry-run)", file=sys.stderr)
            return 1

        batch_results = load_batch_results(args.batch_results)
        trial_records = load_trial_records(args.trial_data)

    roi_report = build_full_report(batch_results, CostBaseline(), testset_path="test.json")
    incidents = classify_incidents(batch_results)

    support_quality = Decimal(str(args.support_quality))
    first_pass_rate = Decimal(str(args.first_pass_rate))

    report = compute_final_acceptance(
        batch_results=batch_results,
        roi_report=roi_report,
        incidents=incidents,
        trial_records=trial_records,
        support_quality=support_quality,
        first_pass_rate=first_pass_rate,
    )

    report_dict = report.to_dict()

    output_path = args.output
    if output_path is None:
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        output_path = DEFAULT_OUTPUT_DIR / f"mv5-final-report-{stamp}.json"
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(report_dict, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Report saved: {output_path}")

    if args.text:
        text_report = format_text_report(report_dict)
        text_path = output_path.with_suffix(".txt")
        text_path.write_text(text_report, encoding="utf-8")
        print(f"Text report saved: {text_path}")
        print()
        print(text_report)

    passed_kpis = sum(1 for k in report_dict["kpi_check"] if k["passed"])
    total_kpis = len(report_dict["kpi_check"])
    print(f"\nKPI: {passed_kpis}/{total_kpis} passed")

    return 0 if report.overall_result.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
