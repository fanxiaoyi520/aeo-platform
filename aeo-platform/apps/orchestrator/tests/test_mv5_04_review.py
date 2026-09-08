"""MV5-04: risk review script tests."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "mv5_04_risk_review.py"


@pytest.fixture(scope="module")
def review_mod() -> Any:
    spec = importlib.util.spec_from_file_location("mv5_04_risk_review", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["mv5_04_risk_review"] = mod
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
                        "degraded": True,
                        "error": "mock timeout",
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
                        "degraded": True,
                    },
                ],
            },
        ],
    }


def test_load_batch_results(
    review_mod: Any,
    sample_batch_results: dict[str, Any],
    tmp_path: Path,
) -> None:
    p = tmp_path / "batch.json"
    p.write_text(json.dumps(sample_batch_results), encoding="utf-8")

    results = review_mod.load_batch_results(p)
    assert len(results) == 3
    assert results[0].sku_id == "MV5-001"
    assert results[0].platform == "amazon"
    assert len(results[0].agents) == 2


def test_main_generates_report(
    review_mod: Any,
    sample_batch_results: dict[str, Any],
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "batch.json"
    input_path.write_text(json.dumps(sample_batch_results), encoding="utf-8")

    output_path = tmp_path / "review.json"
    rc = review_mod.main(["--input", str(input_path), "--output", str(output_path)])
    assert rc == 0
    assert output_path.exists()

    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["milestone"] == "MV5"
    assert report["task"] == "MV5-04"
    assert "summary" in report
    assert "incidents" in report
    assert "tuning_suggestions" in report
    assert "kpi_check" in report


def test_main_missing_input(review_mod: Any, tmp_path: Path) -> None:
    input_path = tmp_path / "nonexistent.json"
    output_path = tmp_path / "review.json"
    rc = review_mod.main(["--input", str(input_path), "--output", str(output_path)])
    assert rc == 1


def test_report_structure(
    review_mod: Any,
    sample_batch_results: dict[str, Any],
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "batch.json"
    input_path.write_text(json.dumps(sample_batch_results), encoding="utf-8")

    output_path = tmp_path / "review.json"
    review_mod.main(["--input", str(input_path), "--output", str(output_path)])

    report = json.loads(output_path.read_text(encoding="utf-8"))

    assert "total_tasks" in report["summary"]
    assert "total_incidents" in report["summary"]
    assert "incident_rate" in report["summary"]
    assert "critical_incidents" in report["summary"]
    assert "by_type" in report["summary"]
    assert "by_agent" in report["summary"]
    assert "by_platform" in report["summary"]

    assert isinstance(report["incidents"], list)
    assert isinstance(report["tuning_suggestions"], list)

    assert len(report["kpi_check"]) >= 2
    for check in report["kpi_check"]:
        assert "metric" in check
        assert "target" in check
        assert "actual" in check
        assert "passed" in check
