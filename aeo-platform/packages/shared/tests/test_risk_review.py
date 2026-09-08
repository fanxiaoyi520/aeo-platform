"""Tests for MV5-04 risk review SDK."""

from __future__ import annotations

import pytest
from aeo_shared.batch_metrics import AgentExecRecord, SkuBatchResult
from aeo_shared.risk_review import (
    IncidentRecord,
    IncidentType,
    RiskReviewReport,
    TuningSuggestion,
    analyze_incidents,
    build_review_report,
    classify_incidents,
    generate_tuning_suggestions,
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
                    error="mock timeout error",
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
                    degraded=True,
                ),
            ],
        ),
    ]


def test_classify_incidents_empty() -> None:
    incidents = classify_incidents([])
    assert incidents == []


def test_classify_incidents_failed(sample_results: list[SkuBatchResult]) -> None:
    incidents = classify_incidents(sample_results)
    assert len(incidents) > 0
    failed_incidents = [i for i in incidents if i.type == IncidentType.TASK_FAILED]
    assert len(failed_incidents) >= 1


def test_classify_incidents_degraded(sample_results: list[SkuBatchResult]) -> None:
    incidents = classify_incidents(sample_results)
    degraded_incidents = [i for i in incidents if i.type == IncidentType.DEGRADED_MODE]
    assert len(degraded_incidents) >= 1


def test_analyze_incidents(sample_results: list[SkuBatchResult]) -> None:
    incidents = classify_incidents(sample_results)
    analysis = analyze_incidents(incidents)

    assert "total_incidents" in analysis
    assert "incident_rate" in analysis
    assert "by_type" in analysis
    assert "by_agent" in analysis
    assert "by_platform" in analysis

    assert analysis["total_incidents"] == len(incidents)
    assert isinstance(analysis["incident_rate"], float)
    assert 0 <= analysis["incident_rate"] <= 1


def test_analyze_incidents_empty() -> None:
    analysis = analyze_incidents([])
    assert analysis["total_incidents"] == 0
    assert analysis["incident_rate"] == 0.0


def test_generate_tuning_suggestions(sample_results: list[SkuBatchResult]) -> None:
    incidents = classify_incidents(sample_results)
    suggestions = generate_tuning_suggestions(incidents)

    assert isinstance(suggestions, list)
    for suggestion in suggestions:
        assert isinstance(suggestion, TuningSuggestion)
        assert suggestion.rule_id
        assert suggestion.current_effect
        assert suggestion.suggested_effect
        assert suggestion.reason
        assert 0 <= suggestion.confidence <= 1


def test_generate_tuning_suggestions_empty() -> None:
    suggestions = generate_tuning_suggestions([])
    assert suggestions == []


def test_build_review_report(sample_results: list[SkuBatchResult]) -> None:
    report = build_review_report(sample_results, testset_path="test.json")

    assert isinstance(report, RiskReviewReport)
    assert report.milestone == "MV5"
    assert report.task == "MV5-04"
    assert report.generated_at
    assert report.testset_path == "test.json"

    assert "total_tasks" in report.summary
    assert "total_incidents" in report.summary
    assert "incident_rate" in report.summary
    assert "by_type" in report.summary
    assert "by_agent" in report.summary
    assert "by_platform" in report.summary

    assert isinstance(report.incidents, list)
    assert isinstance(report.tuning_suggestions, list)
    assert isinstance(report.kpi_check, list)


def test_build_review_report_kpi_check(sample_results: list[SkuBatchResult]) -> None:
    report = build_review_report(sample_results, testset_path="test.json")

    critical_check = next(
        (c for c in report.kpi_check if c["metric"] == "critical_incidents"),
        None,
    )
    assert critical_check is not None
    assert critical_check["target"] == 0
    assert critical_check["passed"] is True

    rate_check = next(
        (c for c in report.kpi_check if c["metric"] == "incident_rate"),
        None,
    )
    assert rate_check is not None
    assert rate_check["target"] == 0.10
    assert isinstance(rate_check["actual"], float)


def test_review_report_to_dict(sample_results: list[SkuBatchResult]) -> None:
    report = build_review_report(sample_results, testset_path="test.json")
    data = report.to_dict()

    assert isinstance(data, dict)
    assert "milestone" in data
    assert "task" in data
    assert "summary" in data
    assert "incidents" in data
    assert "tuning_suggestions" in data
    assert "kpi_check" in data


def test_incident_record_structure() -> None:
    incident = IncidentRecord(
        sku_id="MV5-001",
        agent="ads",
        platform="amazon",
        type=IncidentType.TASK_FAILED,
        error="mock error",
        risk_level="L1",
        timestamp="2026-09-08T14:30:00Z",
    )
    assert incident.sku_id == "MV5-001"
    assert incident.agent == "ads"
    assert incident.type == IncidentType.TASK_FAILED


def test_tuning_suggestion_structure() -> None:
    suggestion = TuningSuggestion(
        rule_id="ads.budget_change.tiktok",
        current_effect="require_hitl",
        suggested_effect="allow",
        reason="Test reason",
        confidence=0.75,
    )
    assert suggestion.rule_id == "ads.budget_change.tiktok"
    assert suggestion.confidence == 0.75
