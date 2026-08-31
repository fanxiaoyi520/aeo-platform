"""MS7 acceptance — pilot deliverables per M07 §5 and master plan §1.4."""

from __future__ import annotations

from pathlib import Path

from aeo_shared.pilot_metrics import (
    PILOT_CSV_FIELDS,
    evaluate_pilot_targets,
    load_pilot_testset,
)

_AEO_PLATFORM_ROOT = Path(__file__).resolve().parents[3]
_REPO_ROOT = _AEO_PLATFORM_ROOT.parent

_REQUIRED_MS7_ARTIFACTS = [
    "pilot/sample-sku-testset.json",
    "scripts/batch_pilot.py",
    "scripts/batch_pilot.ps1",
    "scripts/generate_pilot_report.py",
    "scripts/generate_pilot_report.ps1",
    "packages/shared/src/aeo_shared/pilot_metrics.py",
    "pilot/ms7-reference.summary.json",
]

_MS7_DOC_ARTIFACTS = [
    "docs/pilot/sample-sku-testset.md",
    "docs/pilot/demo-video-script.md",
    "docs/templates/PILOT_REPORT.md",
    "docs/reports/ms7-pilot-report.md",
]


def test_ms7_required_code_artifacts_exist() -> None:
    for relative_path in _REQUIRED_MS7_ARTIFACTS:
        path = _AEO_PLATFORM_ROOT / relative_path
        assert path.is_file(), f"missing MS7 artifact: {relative_path}"


def test_ms7_required_doc_artifacts_exist() -> None:
    for relative_path in _MS7_DOC_ARTIFACTS:
        path = _REPO_ROOT / relative_path
        assert path.is_file(), f"missing MS7 doc: {relative_path}"


def test_ms7_testset_has_20_sample_skus() -> None:
    items = load_pilot_testset(_AEO_PLATFORM_ROOT / "pilot" / "sample-sku-testset.json")
    assert len(items) == 20


def test_ms7_batch_pilot_csv_schema_matches_m07() -> None:
    required = {
        "pilot_id",
        "sku",
        "platform",
        "duration_ms",
        "hitl_required",
        "hitl_approved_first_try",
        "compliance_retries",
        "degraded_mode",
        "adoption_score",
    }
    assert required.issubset(set(PILOT_CSV_FIELDS))


def test_ms7_pilot_report_covers_master_plan_metrics() -> None:
    report = (_REPO_ROOT / "docs" / "reports" / "ms7-pilot-report.md").read_text(encoding="utf-8")
    for metric in (
        "一次通过率",
        "平均耗时",
        "采纳率",
        "P-BIZ-01",
        "batch_pilot",
        "demo-video-script",
    ):
        assert metric in report, f"missing metric in pilot report: {metric}"


def test_ms7_demo_script_covers_e2e_flow() -> None:
    script = (_REPO_ROOT / "docs" / "pilot" / "demo-video-script.md").read_text(encoding="utf-8")
    for step in ("/tasks/new", "/review", "/result", "batch_pilot"):
        assert step in script


def test_ms7_target_evaluation_supports_success_criteria() -> None:
    passing = {
        "total": 20,
        "completed": 20,
        "failed": 0,
        "first_pass_rate": 0.65,
        "adoption_rate": 0.7,
        "p95_duration_ms": 120_000,
    }
    targets = evaluate_pilot_targets(passing)
    assert targets["p95_duration"]["passed"] is True
    assert targets["first_pass_rate"]["passed"] is True
    assert targets["adoption_rate"]["passed"] is True


def test_ms7_s7_deliverable_tests_present() -> None:
    tests_dir = _AEO_PLATFORM_ROOT / "apps" / "api" / "tests"
    for name in (
        "test_s7_01_testset.py",
        "test_s7_02_batch_pilot.py",
        "test_s7_03_pilot_report.py",
    ):
        assert (tests_dir / name).is_file(), f"missing {name}"


def test_ms7_acceptance_report_exists() -> None:
    report = _REPO_ROOT / "docs" / "reports" / "ms7-pilot-acceptance.md"
    assert report.is_file(), "missing MS7 acceptance report"
