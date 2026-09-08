"""MV5-06: final acceptance — six commercial KPI validation for pilot milestone."""

from __future__ import annotations

from decimal import Decimal

from aeo_shared.final_acceptance import (
    AcceptanceResult,
    BizKpi,
    FinalAcceptanceReport,
    compute_final_acceptance,
)


def test_biz_kpi_values() -> None:
    kpi = BizKpi(
        automation_rate=Decimal("0.85"),
        ai_roi_vs_human=True,
        gmv_traceability=Decimal("1.0"),
        critical_incidents=0,
        support_quality=Decimal("0.92"),
        first_pass_rate=Decimal("0.75"),
    )
    assert kpi.automation_rate == Decimal("0.85")
    assert kpi.ai_roi_vs_human is True
    assert kpi.gmv_traceability == Decimal("1.0")
    assert kpi.critical_incidents == 0
    assert kpi.support_quality == Decimal("0.92")
    assert kpi.first_pass_rate == Decimal("0.75")


def test_biz_kpi_all_pass() -> None:
    kpi = BizKpi(
        automation_rate=Decimal("0.85"),
        ai_roi_vs_human=True,
        gmv_traceability=Decimal("1.0"),
        critical_incidents=0,
        support_quality=Decimal("0.92"),
        first_pass_rate=Decimal("0.75"),
    )
    checks = kpi.check_targets()
    assert all(c["passed"] for c in checks)


def test_biz_kpi_some_fail() -> None:
    kpi = BizKpi(
        automation_rate=Decimal("0.30"),
        ai_roi_vs_human=False,
        gmv_traceability=Decimal("0.95"),
        critical_incidents=2,
        support_quality=Decimal("0.80"),
        first_pass_rate=Decimal("0.50"),
    )
    checks = kpi.check_targets()
    passed = [c for c in checks if c["passed"]]
    failed = [c for c in checks if not c["passed"]]
    assert len(passed) == 0
    assert len(failed) == 6


def test_acceptance_result_pass() -> None:
    result = AcceptanceResult(
        all_passed=True,
        passed_count=6,
        total_count=6,
        details={},
    )
    assert result.all_passed is True
    assert result.passed_count == 6


def test_acceptance_result_fail() -> None:
    result = AcceptanceResult(
        all_passed=False,
        passed_count=4,
        total_count=6,
        details={},
    )
    assert result.all_passed is False
    assert result.passed_count == 4


def test_final_report_structure() -> None:
    report = FinalAcceptanceReport(
        milestone="MV5",
        task="MV5-06",
        generated_at="2026-09-08T00:00:00Z",
        kpi_values={
            "automation_rate": "0.85",
            "ai_roi_vs_human": "True",
            "gmv_traceability": "1.0",
            "critical_incidents": "0",
            "support_quality": "0.92",
            "first_pass_rate": "0.75",
        },
        kpi_check=[
            {"metric": "automation_rate", "target": 0.40, "actual": 0.85, "passed": True},
        ],
        overall_result=AcceptanceResult(
            all_passed=True,
            passed_count=6,
            total_count=6,
            details={},
        ),
    )
    d = report.to_dict()
    assert d["milestone"] == "MV5"
    assert d["task"] == "MV5-06"
    assert "kpi_values" in d
    assert "kpi_check" in d
    assert "overall_result" in d


def test_compute_final_acceptance_all_pass() -> None:
    from datetime import UTC, datetime

    from aeo_shared.batch_metrics import AgentExecRecord, SkuBatchResult
    from aeo_shared.risk_review import classify_incidents
    from aeo_shared.roi_comparison import CostBaseline, build_full_report
    from aeo_shared.trial_monitor import HealthStatus, TrialRecord, TrialStatus

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

    roi_report = build_full_report(batch_results, CostBaseline(), testset_path="test.json")

    incidents = classify_incidents(batch_results)

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

    support_quality = Decimal("0.92")
    first_pass_rate = Decimal("0.75")

    report = compute_final_acceptance(
        batch_results=batch_results,
        roi_report=roi_report,
        incidents=incidents,
        trial_records=trial_records,
        support_quality=support_quality,
        first_pass_rate=first_pass_rate,
    )

    assert report.milestone == "MV5"
    assert report.task == "MV5-06"
    assert report.overall_result.all_passed is True
    assert report.overall_result.passed_count == 6


def test_compute_final_acceptance_some_fail() -> None:
    from datetime import UTC, datetime

    from aeo_shared.batch_metrics import AgentExecRecord, SkuBatchResult
    from aeo_shared.risk_review import IncidentRecord, IncidentType
    from aeo_shared.roi_comparison import CostBaseline, build_full_report
    from aeo_shared.trial_monitor import HealthStatus, TrialRecord, TrialStatus

    batch_results = [
        SkuBatchResult(
            sku_id=f"SKU-{i}",
            sku=f"TEST-{i}",
            platform="amazon",
            market="US",
            agents=[
                AgentExecRecord(agent="selection", status="failed", duration_ms=100, error="err"),
            ],
        )
        for i in range(5)
    ]

    roi_report = build_full_report(batch_results, CostBaseline(), testset_path="test.json")

    incidents = [
        IncidentRecord(
            sku_id="SKU-0",
            agent="selection",
            platform="amazon",
            type=IncidentType.RULE_VIOLATION,
            risk_level="L2",
            timestamp=datetime.now(UTC).isoformat(),
        ),
    ]

    trial_records = [
        TrialRecord(
            run_id=f"run-{i}",
            started_at=datetime(2026, 9, 8, i, 0, 0, tzinfo=UTC),
            status=TrialStatus.FAILED,
            duration_ms=5000,
            skus_processed=0,
            health_status=HealthStatus.DOWN,
            error="timeout",
        )
        for i in range(5)
    ]

    support_quality = Decimal("0.70")
    first_pass_rate = Decimal("0.40")

    report = compute_final_acceptance(
        batch_results=batch_results,
        roi_report=roi_report,
        incidents=incidents,
        trial_records=trial_records,
        support_quality=support_quality,
        first_pass_rate=first_pass_rate,
    )

    assert report.overall_result.all_passed is False
    assert report.overall_result.passed_count < 6


def test_automation_rate_target() -> None:
    kpi = BizKpi(
        automation_rate=Decimal("0.40"),
        ai_roi_vs_human=True,
        gmv_traceability=Decimal("1.0"),
        critical_incidents=0,
        support_quality=Decimal("0.85"),
        first_pass_rate=Decimal("0.60"),
    )
    checks = kpi.check_targets()
    auto_check = next(c for c in checks if c["metric"] == "automation_rate")
    assert auto_check["passed"] is True


def test_automation_rate_below_target() -> None:
    kpi = BizKpi(
        automation_rate=Decimal("0.39"),
        ai_roi_vs_human=True,
        gmv_traceability=Decimal("1.0"),
        critical_incidents=0,
        support_quality=Decimal("0.85"),
        first_pass_rate=Decimal("0.60"),
    )
    checks = kpi.check_targets()
    auto_check = next(c for c in checks if c["metric"] == "automation_rate")
    assert auto_check["passed"] is False


def test_critical_incidents_zero_pass() -> None:
    kpi = BizKpi(
        automation_rate=Decimal("0.85"),
        ai_roi_vs_human=True,
        gmv_traceability=Decimal("1.0"),
        critical_incidents=0,
        support_quality=Decimal("0.85"),
        first_pass_rate=Decimal("0.60"),
    )
    checks = kpi.check_targets()
    incident_check = next(c for c in checks if c["metric"] == "critical_incidents")
    assert incident_check["passed"] is True


def test_critical_incidents_nonzero_fail() -> None:
    kpi = BizKpi(
        automation_rate=Decimal("0.85"),
        ai_roi_vs_human=True,
        gmv_traceability=Decimal("1.0"),
        critical_incidents=1,
        support_quality=Decimal("0.85"),
        first_pass_rate=Decimal("0.60"),
    )
    checks = kpi.check_targets()
    incident_check = next(c for c in checks if c["metric"] == "critical_incidents")
    assert incident_check["passed"] is False
