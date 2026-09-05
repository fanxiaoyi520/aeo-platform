"""MV2-03 acceptance — market intelligence API and artifacts."""

from __future__ import annotations

from pathlib import Path

import pytest

_AEO_PLATFORM_ROOT = Path(__file__).resolve().parents[3]

_ARTIFACTS = [
    "packages/shared/src/aeo_shared/cron_parser.py",
    "packages/shared/src/aeo_shared/cron_scheduler.py",
    "packages/shared/src/aeo_shared/competitor_monitor.py",
    "apps/orchestrator/src/aeo_orchestrator/nodes/market_intelligence.py",
    "apps/api/src/aeo_api/routers/intelligence.py",
    "apps/api/src/aeo_api/schemas/intelligence.py",
    "apps/api/alembic/versions/0004_intelligence_schedules.py",
]


@pytest.mark.parametrize("relative_path", _ARTIFACTS)
def test_mv2_03_artifacts_exist(relative_path: str) -> None:
    path = _AEO_PLATFORM_ROOT / relative_path
    assert path.is_file(), f"missing MV2-03 artifact: {relative_path}"


def test_mv2_03_intelligence_router_registered() -> None:
    main_source = (_AEO_PLATFORM_ROOT / "apps" / "api" / "src" / "aeo_api" / "main.py").read_text(
        encoding="utf-8"
    )
    assert "intelligence" in main_source


def test_mv2_03_db_model_exists() -> None:
    models_source = (
        _AEO_PLATFORM_ROOT / "apps" / "api" / "src" / "aeo_api" / "db" / "models.py"
    ).read_text(encoding="utf-8")
    assert "IntelligenceSchedule" in models_source
    assert "intelligence_schedules" in models_source


def test_mv2_03_migration_exists() -> None:
    migration = (
        _AEO_PLATFORM_ROOT
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0004_intelligence_schedules.py"
    ).read_text(encoding="utf-8")
    assert "intelligence_schedules" in migration
    assert "down_revision" in migration
    assert '"0003"' in migration


def test_mv2_03_cron_scheduler_importable() -> None:
    from aeo_shared.cron_scheduler import CronJob, CronScheduler, CronSchedulerConfig

    scheduler = CronScheduler()
    job = scheduler.register(job_id="test", cron_expression="0 9 * * *")
    assert isinstance(job, CronJob)
    assert isinstance(scheduler.config, CronSchedulerConfig)


def test_mv2_03_market_intelligence_service_importable() -> None:
    from aeo_orchestrator.nodes.market_intelligence import (
        MarketIntelReport,
        MarketIntelService,
        ScanInput,
    )

    service = MarketIntelService()
    report = service.scan(ScanInput(sku="TEST-SKU"))
    assert isinstance(report, MarketIntelReport)
    assert report.sku == "TEST-SKU"


def test_mv2_03_competitor_monitor_importable() -> None:
    from aeo_shared.competitor_monitor import (
        ListingSnapshot,
        MonitorDiff,
        compute_diff,
    )

    diff = compute_diff("SKU1", [], [ListingSnapshot(asin="B001", price=10.0)])
    assert isinstance(diff, MonitorDiff)
    assert len(diff.new_listings) == 1


def test_mv2_03_scan_endpoint_logic() -> None:
    from aeo_orchestrator.nodes.market_intelligence import MarketIntelService, ScanInput
    from aeo_shared.competitor_monitor import ListingSnapshot

    service = MarketIntelService()
    prev = [ListingSnapshot(asin="B001", price=100.0)]
    curr = [ListingSnapshot(asin="B001", price=120.0)]
    report = service.scan(
        ScanInput(
            sku="SKU1",
            price=95.0,
            has_title=True,
            has_bullets=True,
            has_keywords=True,
            has_images=True,
            previous_competitors=prev,
            current_competitors=curr,
        )
    )
    assert report.diff.has_significant_change
    assert report.selection_result.total_score > 0
    d = report.to_dict()
    assert "diff" in d
    assert "selection" in d
    assert "suggested_actions" in d
