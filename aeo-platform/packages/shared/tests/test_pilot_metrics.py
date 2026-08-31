"""Unit tests for pilot batch metrics."""

from __future__ import annotations

from pathlib import Path

from aeo_shared.pilot_metrics import (
    compute_adoption_score,
    extract_pilot_record,
    load_pilot_testset,
    summarize_pilot_runs,
    write_pilot_csv,
)

_ROOT = Path(__file__).resolve().parents[3]
_TESTSET = _ROOT / "pilot" / "sample-sku-testset.json"


def test_load_pilot_testset_returns_20_items() -> None:
    items = load_pilot_testset(_TESTSET)
    assert len(items) == 20


def test_compute_adoption_score_exact_match() -> None:
    generated = {"title": "Acme Wireless Earbuds Pro"}
    final_output = {"title": "Acme Wireless Earbuds Pro"}
    assert compute_adoption_score(generated, final_output) == 1.0


def test_extract_pilot_record_hitl_first_try() -> None:
    item = {"id": "SMP-001", "sku": "ACME-EARBUDS-PRO", "platform": "amazon", "market": "US"}
    record = extract_pilot_record(
        item,
        duration_ms=1200,
        status="completed",
        hitl_required=True,
        auto_approved=True,
        degraded_mode=False,
        compliance_retries=1,
        generated={"title": "A"},
        final_output={"title": "A"},
    )
    assert record.hitl_approved_first_try is True
    assert record.compliance_retries == 1


def test_summarize_pilot_runs_rates() -> None:
    item = {"id": "SMP-001", "sku": "ACME-EARBUDS-PRO", "platform": "amazon", "market": "US"}
    records = [
        extract_pilot_record(
            item,
            duration_ms=1000,
            status="completed",
            hitl_required=True,
            auto_approved=True,
            degraded_mode=False,
            compliance_retries=0,
            generated={"title": "A"},
            final_output={"title": "A"},
        ),
        extract_pilot_record(
            {**item, "id": "SMP-002", "sku": "ACME-EARBUDS-LITE"},
            duration_ms=2000,
            status="failed",
            hitl_required=False,
            auto_approved=False,
            degraded_mode=True,
            compliance_retries=2,
            generated=None,
            final_output=None,
            error="timeout",
        ),
    ]
    summary = summarize_pilot_runs(records)
    assert summary["total"] == 2
    assert summary["completed"] == 1
    assert summary["failed"] == 1
    assert summary["hitl_rate"] == 0.5
    assert summary["avg_duration_ms"] == 1000


def test_write_pilot_csv(tmp_path: Path) -> None:
    item = {"id": "SMP-001", "sku": "ACME-EARBUDS-PRO", "platform": "amazon", "market": "US"}
    record = extract_pilot_record(
        item,
        duration_ms=500,
        status="planned",
        hitl_required=False,
        auto_approved=False,
        degraded_mode=False,
        compliance_retries=0,
        generated=None,
        final_output=None,
    )
    output = tmp_path / "batch.csv"
    write_pilot_csv([record], output)
    text = output.read_text(encoding="utf-8")
    assert "pilot_id,sku,platform" in text
    assert "SMP-001" in text
