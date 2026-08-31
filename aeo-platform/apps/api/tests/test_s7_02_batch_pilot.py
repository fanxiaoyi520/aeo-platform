"""S7-02 — batch pilot script acceptance."""

from __future__ import annotations

import csv
import importlib.util
import json
import types
from pathlib import Path
from unittest.mock import AsyncMock, patch

from aeo_llm.provider import LLMResponse

_ROOT = Path(__file__).resolve().parents[3]
_TESTSET = _ROOT / "pilot" / "sample-sku-testset.json"
_BATCH_SCRIPT = _ROOT / "scripts" / "batch_pilot.py"
_BATCH_PS1 = _ROOT / "scripts" / "batch_pilot.ps1"

_LLM_PATCH = "aeo_orchestrator.nodes.generate.get_llm_provider"
_VALID_JSON = """{
  "title": "Acme Wireless Earbuds Pro Bluetooth 5.3 Noise Cancelling TWS",
  "bullets": [
    "ACTIVE NOISE CANCELLING for commute and office use",
    "BLUETOOTH 5.3 with low latency game mode",
    "32H TOTAL PLAYTIME with compact charging case",
    "IPX5 WATER RESISTANT for workouts and daily use",
    "COMFORT FIT with three ear tip sizes included"
  ],
  "search_terms": "wireless earbuds bluetooth noise cancelling",
  "description": "Premium wireless earbuds with hybrid ANC."
}"""


def _load_batch_pilot_module() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("batch_pilot", _BATCH_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load batch_pilot module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_s7_02_batch_pilot_script_exists() -> None:
    assert _BATCH_SCRIPT.is_file()
    assert _BATCH_PS1.is_file()
    text = _BATCH_SCRIPT.read_text(encoding="utf-8")
    assert "load_pilot_testset" in text
    assert "--dry-run" in text
    assert "--auto-approve" in text


def test_s7_02_batch_pilot_dry_run_writes_csv(tmp_path: Path) -> None:
    batch_pilot = _load_batch_pilot_module()

    output = tmp_path / "dry-run.csv"
    exit_code = batch_pilot.main(
        [
            "--testset",
            str(_TESTSET),
            "--output",
            str(output),
            "--dry-run",
        ]
    )
    assert exit_code == 0
    assert output.is_file()
    with output.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 20
    assert rows[0]["status"] == "planned"

    summary_path = output.with_suffix(".summary.json")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["mode"] == "dry_run"
    assert summary["total"] == 20


def test_s7_02_batch_pilot_live_limit_one(tmp_path: Path) -> None:
    batch_pilot = _load_batch_pilot_module()

    mock = AsyncMock()
    mock.chat.return_value = LLMResponse(content=_VALID_JSON, model="test")
    output = tmp_path / "live.csv"

    with patch(_LLM_PATCH, return_value=mock):
        exit_code = batch_pilot.main(
            [
                "--testset",
                str(_TESTSET),
                "--output",
                str(output),
                "--limit",
                "1",
                "--auto-approve",
            ]
        )

    assert exit_code == 0
    with output.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["status"] == "completed"
    assert int(rows[0]["duration_ms"]) >= 0
