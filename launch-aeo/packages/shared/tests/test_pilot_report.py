"""Unit tests for pilot report rendering."""

from __future__ import annotations

from aeo_shared.pilot_metrics import evaluate_pilot_targets, render_pilot_report_markdown


def test_render_pilot_report_includes_success_criteria() -> None:
    summary = {
        "total": 20,
        "completed": 18,
        "failed": 2,
        "hitl_rate": 0.9,
        "first_pass_rate": 0.65,
        "adoption_rate": 0.7,
        "avg_duration_ms": 90000,
        "p95_duration_ms": 150000,
        "mode": "live",
    }
    text = render_pilot_report_markdown(
        summary,
        title="MS7 Pilot",
        testset_path="launch-aeo/pilot/yuanzheng-sku-testset.json",
        batch_csv_path="launch-aeo/pilot/reports/batch.csv",
        generated_at="2026-08-30",
    )
    assert "人工审核一次通过率" in text
    assert "✅ 达标" in text


def test_evaluate_pilot_targets_pending_when_no_completions() -> None:
    targets = evaluate_pilot_targets({"total": 20, "completed": 0})
    assert targets["p95_duration"]["passed"] is None
