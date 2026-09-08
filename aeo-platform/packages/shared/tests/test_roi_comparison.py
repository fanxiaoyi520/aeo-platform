"""Tests for MV5-03 ROI comparison report SDK."""

from __future__ import annotations

from decimal import Decimal

import pytest
from aeo_shared.batch_metrics import AgentExecRecord, SkuBatchResult
from aeo_shared.roi_comparison import (
    CostBaseline,
    PlatformReport,
    RoiComparisonReport,
    build_full_report,
    build_platform_report,
    compute_automation_rate,
    compute_roi_comparison,
)


@pytest.fixture()
def sample_results() -> list[SkuBatchResult]:
    return [
        SkuBatchResult(
            sku_id="MV5-001",
            sku="SKU-A",
            platform="amazon",
            market="US",
            agents=[
                AgentExecRecord(
                    agent="selection",
                    status="completed",
                    duration_ms=100,
                    platform="amazon",
                    degraded=False,
                ),
                AgentExecRecord(
                    agent="ads",
                    status="completed",
                    duration_ms=200,
                    platform="amazon",
                    degraded=False,
                ),
            ],
        ),
        SkuBatchResult(
            sku_id="MV5-026",
            sku="SKU-B",
            platform="tiktok",
            market="US",
            agents=[
                AgentExecRecord(
                    agent="selection",
                    status="completed",
                    duration_ms=150,
                    platform="tiktok",
                    degraded=False,
                ),
                AgentExecRecord(
                    agent="ads",
                    status="failed",
                    duration_ms=50,
                    platform="tiktok",
                    degraded=True,
                    error="mock error",
                ),
            ],
        ),
        SkuBatchResult(
            sku_id="MV5-040",
            sku="SKU-C",
            platform="shopify",
            market="US",
            agents=[
                AgentExecRecord(
                    agent="selection",
                    status="completed",
                    duration_ms=120,
                    platform="shopify",
                    degraded=False,
                ),
            ],
        ),
    ]


@pytest.fixture()
def cost_baseline() -> CostBaseline:
    return CostBaseline(
        ai_cost_per_task=Decimal("0.001"),
        human_cost_per_task=Decimal("0.05"),
        avg_monthly_sales_per_sku=Decimal("1000.00"),
    )


def test_compute_automation_rate_all_completed(sample_results: list[SkuBatchResult]) -> None:
    rate = compute_automation_rate(sample_results)
    assert isinstance(rate, Decimal)
    assert Decimal("0") <= rate <= Decimal("1")


def test_compute_automation_rate_empty() -> None:
    rate = compute_automation_rate([])
    assert rate == Decimal("0")


def test_compute_automation_rate_mixed() -> None:
    results = [
        SkuBatchResult(
            sku_id="T1",
            sku="S1",
            platform="amazon",
            market="US",
            agents=[
                AgentExecRecord(
                    agent="selection", status="completed", duration_ms=100, platform="amazon"
                ),
                AgentExecRecord(agent="ads", status="failed", duration_ms=50, platform="amazon"),
            ],
        ),
    ]
    rate = compute_automation_rate(results)
    assert rate == Decimal("0.5")


def test_compute_roi_comparison(cost_baseline: CostBaseline) -> None:
    results = [
        SkuBatchResult(
            sku_id="T1",
            sku="S1",
            platform="amazon",
            market="US",
            agents=[
                AgentExecRecord(
                    agent="selection", status="completed", duration_ms=100, platform="amazon"
                ),
            ],
        ),
    ]
    comparison = compute_roi_comparison(results, cost_baseline)
    assert "ai_roi" in comparison
    assert "human_roi" in comparison
    assert "roi_lift" in comparison
    assert isinstance(comparison["ai_roi"], Decimal)
    assert isinstance(comparison["human_roi"], Decimal)


def test_compute_roi_comparison_zero_tasks(cost_baseline: CostBaseline) -> None:
    comparison = compute_roi_comparison([], cost_baseline)
    assert comparison["ai_roi"] == Decimal("0")
    assert comparison["human_roi"] == Decimal("0")
    assert comparison["roi_lift"] == Decimal("0")


def test_build_platform_report(
    sample_results: list[SkuBatchResult], cost_baseline: CostBaseline
) -> None:
    report = build_platform_report(sample_results, cost_baseline)
    assert isinstance(report, dict)
    assert "amazon" in report
    assert "tiktok" in report
    assert "shopify" in report
    assert isinstance(report["amazon"], PlatformReport)
    assert report["amazon"].automation_rate >= Decimal("0")


def test_build_full_report(
    sample_results: list[SkuBatchResult], cost_baseline: CostBaseline
) -> None:
    report = build_full_report(sample_results, cost_baseline, testset_path="test.json")
    assert isinstance(report, RoiComparisonReport)
    assert report.summary["total_skus"] == 3
    assert "automation_rate" in report.summary
    assert "ai_roi" in report.summary
    assert "human_roi" in report.summary
    assert len(report.per_platform) == 3
    assert len(report.kpi_check) > 0


def test_kpi_check_automation_rate_pass(cost_baseline: CostBaseline) -> None:
    results = [
        SkuBatchResult(
            sku_id=f"T{i}",
            sku=f"S{i}",
            platform="amazon",
            market="US",
            agents=[
                AgentExecRecord(
                    agent="selection", status="completed", duration_ms=100, platform="amazon"
                ),
            ],
        )
        for i in range(10)
    ]
    report = build_full_report(results, cost_baseline, testset_path="test.json")
    auto_check = next((c for c in report.kpi_check if c["metric"] == "automation_rate"), None)
    assert auto_check is not None
    assert auto_check["passed"] is True


def test_to_dict_serialization(
    sample_results: list[SkuBatchResult], cost_baseline: CostBaseline
) -> None:
    report = build_full_report(sample_results, cost_baseline, testset_path="test.json")
    data = report.to_dict()
    assert isinstance(data, dict)
    assert "milestone" in data
    assert "task" in data
    assert "summary" in data
    assert "per_platform" in data
    assert "kpi_check" in data
