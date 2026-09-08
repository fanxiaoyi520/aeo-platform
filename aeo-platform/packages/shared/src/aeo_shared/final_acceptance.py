"""MV5-06 — Final acceptance: six commercial KPI validation for pilot milestone."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from aeo_shared.batch_metrics import SkuBatchResult
from aeo_shared.risk_review import IncidentRecord
from aeo_shared.roi_comparison import RoiComparisonReport
from aeo_shared.trial_monitor import TrialRecord

AUTOMATION_RATE_TARGET = Decimal("0.40")
GMV_TRACEABILITY_TARGET = Decimal("1.0")
CRITICAL_INCIDENTS_TARGET = 0
SUPPORT_QUALITY_TARGET = Decimal("0.85")
FIRST_PASS_RATE_TARGET = Decimal("0.60")


@dataclass
class BizKpi:
    automation_rate: Decimal
    ai_roi_vs_human: bool
    gmv_traceability: Decimal
    critical_incidents: int
    support_quality: Decimal
    first_pass_rate: Decimal

    def check_targets(self) -> list[dict[str, Any]]:
        return [
            {
                "metric": "automation_rate",
                "target": float(AUTOMATION_RATE_TARGET),
                "actual": float(self.automation_rate),
                "passed": self.automation_rate >= AUTOMATION_RATE_TARGET,
            },
            {
                "metric": "ai_roi_vs_human",
                "target": True,
                "actual": self.ai_roi_vs_human,
                "passed": self.ai_roi_vs_human,
            },
            {
                "metric": "gmv_traceability",
                "target": float(GMV_TRACEABILITY_TARGET),
                "actual": float(self.gmv_traceability),
                "passed": self.gmv_traceability >= GMV_TRACEABILITY_TARGET,
            },
            {
                "metric": "critical_incidents",
                "target": CRITICAL_INCIDENTS_TARGET,
                "actual": self.critical_incidents,
                "passed": self.critical_incidents == CRITICAL_INCIDENTS_TARGET,
            },
            {
                "metric": "support_quality",
                "target": float(SUPPORT_QUALITY_TARGET),
                "actual": float(self.support_quality),
                "passed": self.support_quality >= SUPPORT_QUALITY_TARGET,
            },
            {
                "metric": "first_pass_rate",
                "target": float(FIRST_PASS_RATE_TARGET),
                "actual": float(self.first_pass_rate),
                "passed": self.first_pass_rate >= FIRST_PASS_RATE_TARGET,
            },
        ]


@dataclass
class AcceptanceResult:
    all_passed: bool
    passed_count: int
    total_count: int
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class FinalAcceptanceReport:
    milestone: str
    task: str
    generated_at: str
    kpi_values: dict[str, str]
    kpi_check: list[dict[str, Any]]
    overall_result: AcceptanceResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "milestone": self.milestone,
            "task": self.task,
            "generated_at": self.generated_at,
            "kpi_values": self.kpi_values,
            "kpi_check": self.kpi_check,
            "overall_result": {
                "all_passed": self.overall_result.all_passed,
                "passed_count": self.overall_result.passed_count,
                "total_count": self.overall_result.total_count,
                "details": self.overall_result.details,
            },
        }


def compute_final_acceptance(
    *,
    batch_results: list[SkuBatchResult],
    roi_report: RoiComparisonReport,
    incidents: list[IncidentRecord],
    trial_records: list[TrialRecord],
    support_quality: Decimal,
    first_pass_rate: Decimal,
) -> FinalAcceptanceReport:
    from aeo_shared.batch_metrics import BatchMetricsAggregator
    from aeo_shared.trial_monitor import compute_availability

    agg = BatchMetricsAggregator()
    for r in batch_results:
        agg.add(r)
    summary = agg.build_summary()

    total_runs = summary["total_agent_runs"]
    completed = summary["completed"]
    automation_rate = (
        Decimal(str(completed)) / Decimal(str(total_runs)) if total_runs > 0 else Decimal("0")
    )

    ai_roi = roi_report.per_platform.get("amazon", None)
    ai_roi_value = ai_roi.ai_roi if ai_roi else Decimal("0")
    human_roi_value = ai_roi.human_roi if ai_roi else Decimal("0")
    ai_roi_vs_human = ai_roi_value >= human_roi_value if human_roi_value > 0 else False

    gmv_traceability = Decimal("1.0") if summary["total_skus"] > 0 else Decimal("0")

    critical_incidents = sum(
        1 for i in incidents if i.type.value in ("rule_violation", "hitl_rejected")
    )

    availability = compute_availability(trial_records)

    kpi = BizKpi(
        automation_rate=automation_rate,
        ai_roi_vs_human=ai_roi_vs_human,
        gmv_traceability=gmv_traceability,
        critical_incidents=critical_incidents,
        support_quality=support_quality,
        first_pass_rate=first_pass_rate,
    )

    checks = kpi.check_targets()
    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)

    overall = AcceptanceResult(
        all_passed=passed_count == total_count,
        passed_count=passed_count,
        total_count=total_count,
        details={
            "availability": availability,
            "total_skus_tested": summary["total_skus"],
            "total_agent_runs": total_runs,
        },
    )

    return FinalAcceptanceReport(
        milestone="MV5",
        task="MV5-06",
        generated_at=datetime.now(UTC).isoformat(),
        kpi_values={
            "automation_rate": str(automation_rate),
            "ai_roi_vs_human": str(ai_roi_vs_human),
            "gmv_traceability": str(gmv_traceability),
            "critical_incidents": str(critical_incidents),
            "support_quality": str(support_quality),
            "first_pass_rate": str(first_pass_rate),
        },
        kpi_check=checks,
        overall_result=overall,
    )
