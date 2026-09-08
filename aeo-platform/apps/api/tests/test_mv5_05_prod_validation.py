"""MV5-05: production deployment validation tests.

Verifies that the production deployment infrastructure is correctly configured
for 7x24 trial operation.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROD_COMPOSE = ROOT / "infra" / "compose" / "docker-compose.prod.yml"


def test_prod_compose_exists() -> None:
    assert PROD_COMPOSE.is_file(), "docker-compose.prod.yml must exist"


def test_prod_scripts_exist() -> None:
    assert (ROOT / "scripts" / "prod-up.ps1").is_file()
    assert (ROOT / "scripts" / "prod-down.ps1").is_file()


def test_trial_run_script_exists() -> None:
    assert (ROOT / "scripts" / "mv5_05_trial_run.py").is_file()


def test_trial_report_script_exists() -> None:
    assert (ROOT / "scripts" / "mv5_05_trial_report.py").is_file()


def test_trial_run_dry_run_produces_output(tmp_path: Path) -> None:
    import subprocess
    import sys

    output_file = tmp_path / "trial-output.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "mv5_05_trial_run.py"),
            "--dry-run",
            "--output",
            str(output_file),
        ],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=60,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert output_file.is_file(), "Dry run should produce output JSON"

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert "total_runs" in data
    assert "availability" in data
    assert "records" in data
    assert data["trial_config"]["dry_run"] is True


def test_trial_report_generates_from_dry_run(tmp_path: Path) -> None:
    import subprocess
    import sys

    trial_output = tmp_path / "trial-output.json"
    report_output = tmp_path / "trial-report.json"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "mv5_05_trial_run.py"),
            "--dry-run",
            "--output",
            str(trial_output),
        ],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=60,
    )
    assert trial_output.is_file()

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "mv5_05_trial_report.py"),
            str(trial_output),
            "--output",
            str(report_output),
        ],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=60,
    )
    assert result.returncode == 0, f"Report script failed: {result.stderr}"
    assert report_output.is_file()

    report = json.loads(report_output.read_text(encoding="utf-8"))
    assert report["milestone"] == "MV5"
    assert report["task"] == "MV5-05"
    assert "kpi_check" in report
    assert "summary" in report


def test_prod_compose_has_required_services() -> None:
    compose_text = PROD_COMPOSE.read_text(encoding="utf-8")
    assert "postgres:" in compose_text
    assert "redis:" in compose_text
    assert "api:" in compose_text
    assert "web:" in compose_text


def test_prod_compose_has_healthchecks() -> None:
    compose_text = PROD_COMPOSE.read_text(encoding="utf-8")
    assert "healthcheck:" in compose_text


def test_prod_compose_has_restart_policy() -> None:
    compose_text = PROD_COMPOSE.read_text(encoding="utf-8")
    assert "restart:" in compose_text
    assert "unless-stopped" in compose_text


def test_env_prod_example_exists() -> None:
    assert (ROOT / ".env.prod.example").is_file()


def test_dockerfiles_exist() -> None:
    assert (ROOT / "infra" / "docker" / "Dockerfile.api").is_file()
    assert (ROOT / "infra" / "docker" / "Dockerfile.web").is_file()


def test_50sku_testset_exists() -> None:
    testset_path = ROOT / "pilot" / "mv5-50sku-testset.json"
    assert testset_path.is_file()

    data = json.loads(testset_path.read_text(encoding="utf-8"))
    items = data.get("items", data) if isinstance(data, dict) else data
    assert len(items) >= 50, "Test set must have at least 50 SKUs"


def test_batch_runner_script_exists() -> None:
    assert (ROOT / "scripts" / "batch_mv5_pilot.py").is_file()
