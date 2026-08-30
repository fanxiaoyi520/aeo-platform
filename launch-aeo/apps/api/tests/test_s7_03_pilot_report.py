"""S7-03 — pilot report and demo video script acceptance."""

from __future__ import annotations

import importlib.util
import json
import types
from pathlib import Path

from aeo_shared.pilot_metrics import (
    evaluate_pilot_targets,
    load_pilot_summary,
    render_pilot_report_markdown,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_LAUNCH_AEO_ROOT = _REPO_ROOT / "launch-aeo"
_TEMPLATE = _REPO_ROOT / "docs" / "templates" / "PILOT_REPORT.md"
_REPORT = _REPO_ROOT / "docs" / "reports" / "ms7-pilot-report.md"
_DEMO_SCRIPT = _REPO_ROOT / "docs" / "pilot" / "demo-video-script.md"
_GENERATE_SCRIPT = _LAUNCH_AEO_ROOT / "scripts" / "generate_pilot_report.py"
_REFERENCE_SUMMARY = _LAUNCH_AEO_ROOT / "pilot" / "ms7-reference.summary.json"


def test_s7_03_pilot_report_template_exists() -> None:
    assert _TEMPLATE.is_file()
    text = _TEMPLATE.read_text(encoding="utf-8")
    for token in ("P-BIZ-01", "first_pass_rate", "batch_pilot"):
        assert token in text


def test_s7_03_demo_video_script_exists() -> None:
    assert _DEMO_SCRIPT.is_file()
    text = _DEMO_SCRIPT.read_text(encoding="utf-8")
    assert "10 分钟" in text or "10:00" in text
    assert "/tasks/new" in text
    assert "batch_pilot" in text


def test_s7_03_generate_pilot_report_script_exists() -> None:
    assert _GENERATE_SCRIPT.is_file()
    assert (_LAUNCH_AEO_ROOT / "scripts" / "generate_pilot_report.ps1").is_file()


def test_s7_03_evaluate_pilot_targets_live_sample() -> None:
    summary = {
        "total": 20,
        "completed": 19,
        "failed": 1,
        "hitl_rate": 0.95,
        "first_pass_rate": 0.65,
        "adoption_rate": 0.72,
        "avg_duration_ms": 85000,
        "p95_duration_ms": 120000,
        "mode": "live",
    }
    targets = evaluate_pilot_targets(summary)
    assert targets["p95_duration"]["passed"] is True
    assert targets["first_pass_rate"]["passed"] is True
    assert targets["adoption_rate"]["passed"] is True


def test_s7_03_render_pilot_report_markdown() -> None:
    summary = {"total": 20, "completed": 0, "failed": 0, "mode": "dry_run", "hitl_rate": 0}
    text = render_pilot_report_markdown(
        summary,
        title="Test Report",
        testset_path="launch-aeo/pilot/yuanzheng-sku-testset.json",
        batch_csv_path="launch-aeo/pilot/reports/batch.csv",
        generated_at="2026-08-30",
    )
    assert "P-BIZ-01" in text
    assert "待 live 批跑" in text


def test_s7_03_reference_summary_and_report_exist() -> None:
    assert _REFERENCE_SUMMARY.is_file()
    summary = load_pilot_summary(_REFERENCE_SUMMARY)
    assert summary["total"] == 20
    assert _REPORT.is_file()
    report_text = _REPORT.read_text(encoding="utf-8")
    assert "MS7" in report_text
    assert "demo-video-script.md" in report_text


def test_s7_03_generate_pilot_report_cli(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location("generate_pilot_report", _GENERATE_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert isinstance(module, types.ModuleType)

    summary_path = tmp_path / "batch.summary.json"
    csv_path = tmp_path / "batch.csv"
    csv_path.write_text("pilot_id,sku\nYZ-001,X431-PRO\n", encoding="utf-8")
    summary_path.write_text(
        json.dumps({"total": 1, "completed": 1, "failed": 0, "mode": "live", "hitl_rate": 1.0}),
        encoding="utf-8",
    )
    output = tmp_path / "report.md"
    exit_code = module.main(
        [
            "--summary",
            str(summary_path),
            "--csv",
            str(csv_path),
            "--output",
            str(output),
        ]
    )
    assert exit_code == 0
    assert "执行摘要" in output.read_text(encoding="utf-8")
