"""MV5-03 — ROI comparison report SDK."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from aeo_shared.batch_metrics import SkuBatchResult


@dataclass(frozen=True)
class CostBaseline:
    ai_cost_per_task: Decimal = Decimal("0.001")
    human_cost_per_task: Decimal = Decimal("0.05")
    avg_monthly_sales_per_sku: Decimal = Decimal("1000.00")


@dataclass(frozen=True)
class PlatformReport:
    platform: str
    total_skus: int
    total_tasks: int
    automated_tasks: int
    automation_rate: Decimal
    ai_roi: Decimal
    human_roi: Decimal
    roi_lift: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "total_skus": self.total_skus,
            "total_tasks": self.total_tasks,
            "automated_tasks": self.automated_tasks,
            "automation_rate": str(self.automation_rate),
            "ai_roi": str(self.ai_roi),
            "human_roi": str(self.human_roi),
            "roi_lift": str(self.roi_lift),
        }


@dataclass(frozen=True)
class RoiComparisonReport:
    milestone: str
    task: str
    generated_at: str
    testset_path: str
    summary: dict[str, Any]
    per_platform: dict[str, PlatformReport]
    kpi_check: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "milestone": self.milestone,
            "task": self.task,
            "generated_at": self.generated_at,
            "testset_path": self.testset_path,
            "summary": self.summary,
            "per_platform": {k: v.to_dict() for k, v in self.per_platform.items()},
            "kpi_check": self.kpi_check,
        }


def compute_automation_rate(results: list[SkuBatchResult]) -> Decimal:
    if not results:
        return Decimal("0")

    total_tasks = 0
    automated_tasks = 0

    for result in results:
        for agent in result.agents:
            total_tasks += 1
            if agent.status == "completed" and not agent.degraded:
                automated_tasks += 1

    if total_tasks == 0:
        return Decimal("0")

    return (Decimal(automated_tasks) / Decimal(total_tasks)).quantize(Decimal("0.0001"))


def compute_roi_comparison(
    results: list[SkuBatchResult],
    baseline: CostBaseline,
) -> dict[str, Decimal]:
    if not results:
        return {
            "ai_roi": Decimal("0"),
            "human_roi": Decimal("0"),
            "roi_lift": Decimal("0"),
        }

    total_tasks = sum(len(r.agents) for r in results)
    total_skus = len(results)

    ai_cost = baseline.ai_cost_per_task * total_tasks
    human_cost = baseline.human_cost_per_task * total_tasks

    gmv = baseline.avg_monthly_sales_per_sku * total_skus

    ai_roi = (gmv / ai_cost).quantize(Decimal("0.0001")) if ai_cost > 0 else Decimal("0")
    human_roi = (gmv / human_cost).quantize(Decimal("0.0001")) if human_cost > 0 else Decimal("0")

    if human_roi > 0:
        roi_lift = ((ai_roi - human_roi) / human_roi).quantize(Decimal("0.0001"))
    else:
        roi_lift = Decimal("0")

    return {
        "ai_roi": ai_roi,
        "human_roi": human_roi,
        "roi_lift": roi_lift,
    }


def build_platform_report(
    results: list[SkuBatchResult],
    baseline: CostBaseline,
) -> dict[str, PlatformReport]:
    platform_results: dict[str, list[SkuBatchResult]] = {}
    for result in results:
        platform_results.setdefault(result.platform, []).append(result)

    reports: dict[str, PlatformReport] = {}
    for platform, platform_data in platform_results.items():
        total_skus = len(platform_data)
        total_tasks = sum(len(r.agents) for r in platform_data)
        automated_tasks = sum(
            1
            for r in platform_data
            for agent in r.agents
            if agent.status == "completed" and not agent.degraded
        )

        automation_rate = (
            (Decimal(automated_tasks) / Decimal(total_tasks)).quantize(Decimal("0.0001"))
            if total_tasks > 0
            else Decimal("0")
        )

        ai_cost = baseline.ai_cost_per_task * total_tasks
        human_cost = baseline.human_cost_per_task * total_tasks
        gmv = baseline.avg_monthly_sales_per_sku * total_skus

        ai_roi = (gmv / ai_cost).quantize(Decimal("0.0001")) if ai_cost > 0 else Decimal("0")
        human_roi = (
            (gmv / human_cost).quantize(Decimal("0.0001")) if human_cost > 0 else Decimal("0")
        )
        roi_lift = (
            ((ai_roi - human_roi) / human_roi).quantize(Decimal("0.0001"))
            if human_roi > 0
            else Decimal("0")
        )

        reports[platform] = PlatformReport(
            platform=platform,
            total_skus=total_skus,
            total_tasks=total_tasks,
            automated_tasks=automated_tasks,
            automation_rate=automation_rate,
            ai_roi=ai_roi,
            human_roi=human_roi,
            roi_lift=roi_lift,
        )

    return reports


def build_full_report(
    results: list[SkuBatchResult],
    baseline: CostBaseline,
    *,
    testset_path: str,
) -> RoiComparisonReport:
    total_skus = len(results)
    total_tasks = sum(len(r.agents) for r in results)
    automated_tasks = sum(
        1
        for r in results
        for agent in r.agents
        if agent.status == "completed" and not agent.degraded
    )

    automation_rate = compute_automation_rate(results)
    roi_comparison = compute_roi_comparison(results, baseline)
    per_platform = build_platform_report(results, baseline)

    summary = {
        "total_skus": total_skus,
        "total_tasks": total_tasks,
        "automated_tasks": automated_tasks,
        "automation_rate": str(automation_rate),
        "ai_roi": str(roi_comparison["ai_roi"]),
        "human_roi": str(roi_comparison["human_roi"]),
        "roi_lift": str(roi_comparison["roi_lift"]),
    }

    kpi_check = [
        {
            "metric": "automation_rate",
            "target": 0.40,
            "actual": float(automation_rate),
            "passed": automation_rate >= Decimal("0.40"),
        },
        {
            "metric": "roi_vs_human",
            "target": "gte_p50",
            "actual": float(roi_comparison["ai_roi"]),
            "passed": roi_comparison["ai_roi"] >= roi_comparison["human_roi"],
        },
    ]

    return RoiComparisonReport(
        milestone="MV5",
        task="MV5-03",
        generated_at=datetime.now(UTC).isoformat(),
        testset_path=testset_path,
        summary=summary,
        per_platform=per_platform,
        kpi_check=kpi_check,
    )
