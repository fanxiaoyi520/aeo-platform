"""MV5-02: batch metrics aggregation tests."""

from __future__ import annotations

from decimal import Decimal

from aeo_shared.batch_metrics import (
    AgentExecRecord,
    BatchMetricsAggregator,
    KpiTarget,
    SkuBatchResult,
)


def _ok_record(
    agent: str,
    *,
    duration_ms: int = 100,
    platform: str = "amazon",
    degraded: bool = False,
) -> AgentExecRecord:
    return AgentExecRecord(
        agent=agent,
        status="completed",
        duration_ms=duration_ms,
        platform=platform,
        degraded=degraded,
    )


def _fail_record(agent: str, *, platform: str = "amazon") -> AgentExecRecord:
    return AgentExecRecord(
        agent=agent,
        status="failed",
        duration_ms=50,
        platform=platform,
        error="mock error",
    )


def test_aggregator_empty() -> None:
    agg = BatchMetricsAggregator()
    summary = agg.build_summary()
    assert summary["total_skus"] == 0
    assert summary["total_agent_runs"] == 0
    assert summary["completed"] == 0
    assert summary["failed"] == 0


def test_aggregator_single_sku_all_agents() -> None:
    agg = BatchMetricsAggregator()
    sku_result = SkuBatchResult(
        sku_id="MV5-001",
        sku="ACME-EARBUDS-PRO",
        platform="amazon",
        market="US",
        agents=[
            _ok_record("selection"),
            _ok_record("ads"),
            _ok_record("image_copy"),
            _ok_record("operations"),
            _ok_record("support"),
            _ok_record("analytics"),
        ],
    )
    agg.add(sku_result)
    summary = agg.build_summary()

    assert summary["total_skus"] == 1
    assert summary["total_agent_runs"] == 6
    assert summary["completed"] == 6
    assert summary["failed"] == 0
    assert summary["avg_duration_ms"] == 100


def test_aggregator_mixed_results() -> None:
    agg = BatchMetricsAggregator()
    sku_result = SkuBatchResult(
        sku_id="MV5-002",
        sku="ACME-EARBUDS-LITE",
        platform="amazon",
        market="US",
        agents=[
            _ok_record("selection"),
            _ok_record("ads"),
            _fail_record("image_copy"),
            _ok_record("operations"),
            _ok_record("support"),
            _ok_record("analytics"),
        ],
    )
    agg.add(sku_result)
    summary = agg.build_summary()

    assert summary["completed"] == 5
    assert summary["failed"] == 1
    assert summary["total_agent_runs"] == 6


def test_aggregator_per_platform() -> None:
    agg = BatchMetricsAggregator()
    agg.add(
        SkuBatchResult(
            sku_id="MV5-001",
            sku="A",
            platform="amazon",
            market="US",
            agents=[_ok_record("selection", platform="amazon")],
        )
    )
    agg.add(
        SkuBatchResult(
            sku_id="MV5-026",
            sku="B",
            platform="tiktok",
            market="US",
            agents=[_ok_record("selection", platform="tiktok")],
        )
    )
    agg.add(
        SkuBatchResult(
            sku_id="MV5-040",
            sku="C",
            platform="shopify",
            market="US",
            agents=[_ok_record("selection", platform="shopify")],
        )
    )
    summary = agg.build_summary()

    per_platform = summary["per_platform"]
    assert per_platform["amazon"]["total_skus"] == 1
    assert per_platform["tiktok"]["total_skus"] == 1
    assert per_platform["shopify"]["total_skus"] == 1


def test_aggregator_degradation_tracking() -> None:
    agg = BatchMetricsAggregator()
    agg.add(
        SkuBatchResult(
            sku_id="MV5-014",
            sku="D",
            platform="amazon",
            market="US",
            agents=[
                _ok_record("selection", degraded=True),
                _ok_record("ads"),
            ],
        )
    )
    agg.add(
        SkuBatchResult(
            sku_id="MV5-009",
            sku="E",
            platform="amazon",
            market="US",
            agents=[
                _ok_record("selection"),
                _ok_record("ads", degraded=True),
            ],
        )
    )
    summary = agg.build_summary()

    assert summary["degraded_runs"] == 2
    assert summary["total_agent_runs"] == 4


def test_automation_rate_calculation() -> None:
    agg = BatchMetricsAggregator()
    for i in range(10):
        agents = [_ok_record("selection"), _ok_record("ads")]
        if i < 3:
            agents.append(_fail_record("image_copy"))
        else:
            agents.append(_ok_record("image_copy"))
        agg.add(
            SkuBatchResult(
                sku_id=f"MV5-{i:03d}",
                sku=f"SKU-{i}",
                platform="amazon",
                market="US",
                agents=agents,
            )
        )
    summary = agg.build_summary()

    total = summary["total_agent_runs"]
    completed = summary["completed"]
    assert total == 30
    assert completed == 27
    rate = Decimal(str(completed)) / Decimal(str(total))
    assert rate > Decimal("0.8")


def test_kpi_check_all_pass() -> None:
    kpis = {
        "automation_rate": KpiTarget(target=Decimal("0.40"), operator="gte"),
        "avg_duration_ms": KpiTarget(target=Decimal("5000"), operator="lte"),
    }
    values = {
        "automation_rate": Decimal("0.85"),
        "avg_duration_ms": Decimal("200"),
    }
    agg = BatchMetricsAggregator()
    checks = agg.check_kpis(kpis, values)
    assert all(c["passed"] for c in checks)


def test_kpi_check_some_fail() -> None:
    kpis = {
        "automation_rate": KpiTarget(target=Decimal("0.40"), operator="gte"),
        "avg_duration_ms": KpiTarget(target=Decimal("100"), operator="lte"),
    }
    values = {
        "automation_rate": Decimal("0.85"),
        "avg_duration_ms": Decimal("500"),
    }
    agg = BatchMetricsAggregator()
    checks = agg.check_kpis(kpis, values)

    passed = [c for c in checks if c["passed"]]
    failed = [c for c in checks if not c["passed"]]
    assert len(passed) == 1
    assert len(failed) == 1
    assert failed[0]["metric"] == "avg_duration_ms"


def test_kpi_check_zero_division_safe() -> None:
    kpis = {
        "automation_rate": KpiTarget(target=Decimal("0.40"), operator="gte"),
    }
    values: dict[str, Decimal] = {}
    agg = BatchMetricsAggregator()
    checks = agg.check_kpis(kpis, values)
    assert len(checks) == 1
    assert not checks[0]["passed"]
