"""MV5-03: report generator script tests."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "mv5_03_roi_report.py"


@pytest.fixture(scope="module")
def report_mod() -> Any:
    spec = importlib.util.spec_from_file_location("mv5_03_roi_report", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["mv5_03_roi_report"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def sample_batch_results() -> dict[str, Any]:
    return {
        "summary": {"total": 3, "completed": 2, "failed": 1},
        "results": [
            {
                "sku_id": "MV5-001",
                "sku": "SKU-A",
                "platform": "amazon",
                "market": "US",
                "agents": [
                    {
                        "agent": "selection",
                        "status": "completed",
                        "duration_ms": 100,
                        "platform": "amazon",
                    },
                    {
                        "agent": "ads",
                        "status": "completed",
                        "duration_ms": 200,
                        "platform": "amazon",
                    },
                ],
            },
            {
                "sku_id": "MV5-026",
                "sku": "SKU-B",
                "platform": "tiktok",
                "market": "US",
                "agents": [
                    {
                        "agent": "selection",
                        "status": "completed",
                        "duration_ms": 150,
                        "platform": "tiktok",
                    },
                    {
                        "agent": "ads",
                        "status": "failed",
                        "duration_ms": 50,
                        "platform": "tiktok",
                        "error": "err",
                    },
                ],
            },
            {
                "sku_id": "MV5-040",
                "sku": "SKU-C",
                "platform": "shopify",
                "market": "US",
                "agents": [
                    {
                        "agent": "selection",
                        "status": "completed",
                        "duration_ms": 120,
                        "platform": "shopify",
                    },
                ],
            },
        ],
    }


def test_load_batch_results(
    report_mod: Any,
    sample_batch_results: dict[str, Any],
    tmp_path: Path,
) -> None:
    p = tmp_path / "batch.json"
    p.write_text(json.dumps(sample_batch_results), encoding="utf-8")

    results = report_mod.load_batch_results(p)
    assert len(results) == 3
    assert results[0].sku_id == "MV5-001"
    assert results[0].platform == "amazon"
    assert len(results[0].agents) == 2


def test_main_generates_report(
    report_mod: Any,
    sample_batch_results: dict[str, Any],
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "batch.json"
    input_path.write_text(json.dumps(sample_batch_results), encoding="utf-8")

    output_path = tmp_path / "report.json"
    rc = report_mod.main(["--input", str(input_path), "--output", str(output_path)])
    assert rc == 0
    assert output_path.exists()

    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["milestone"] == "MV5"
    assert report["task"] == "MV5-03"
    assert "summary" in report
    assert "per_platform" in report
    assert "kpi_check" in report


def test_main_with_custom_costs(
    report_mod: Any,
    sample_batch_results: dict[str, Any],
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "batch.json"
    input_path.write_text(json.dumps(sample_batch_results), encoding="utf-8")

    output_path = tmp_path / "report.json"
    rc = report_mod.main(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--ai-cost",
            "0.002",
            "--human-cost",
            "0.06",
        ]
    )
    assert rc == 0


def test_main_missing_input(report_mod: Any, tmp_path: Path) -> None:
    input_path = tmp_path / "nonexistent.json"
    output_path = tmp_path / "report.json"
    rc = report_mod.main(["--input", str(input_path), "--output", str(output_path)])
    assert rc == 1


def test_report_structure(
    report_mod: Any,
    sample_batch_results: dict[str, Any],
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "batch.json"
    input_path.write_text(json.dumps(sample_batch_results), encoding="utf-8")

    output_path = tmp_path / "report.json"
    report_mod.main(["--input", str(input_path), "--output", str(output_path)])

    report = json.loads(output_path.read_text(encoding="utf-8"))

    assert "total_skus" in report["summary"]
    assert "automation_rate" in report["summary"]
    assert "ai_roi" in report["summary"]
    assert "human_roi" in report["summary"]
    assert "roi_lift" in report["summary"]

    assert "amazon" in report["per_platform"]
    assert "tiktok" in report["per_platform"]
    assert "shopify" in report["per_platform"]

    assert len(report["kpi_check"]) >= 2
    for check in report["kpi_check"]:
        assert "metric" in check
        assert "target" in check
        assert "actual" in check
        assert "passed" in check
