"""P6-29: Metrics aggregation service tests."""

import os
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")

import pytest
from aeo_api.services.metrics_aggregation import MetricsAggregationService, has_live_data
from aeo_shared.metrics_sdk import BusinessMetricsSnapshot


def test_has_live_data_with_zero_values() -> None:
    snapshots = [
        BusinessMetricsSnapshot(
            snapshot_date=date.today(),
            platform="amazon",
            marketplace="US",
            gmv=Decimal("0"),
            ad_spend=Decimal("0"),
            roi=None,
            order_count=0,
            unique_skus=0,
            data_source="live",
        )
    ]
    assert has_live_data(snapshots) is False


def test_has_live_data_with_gmv() -> None:
    snapshots = [
        BusinessMetricsSnapshot(
            snapshot_date=date.today(),
            platform="amazon",
            marketplace="US",
            gmv=Decimal("100.50"),
            ad_spend=Decimal("0"),
            roi=None,
            order_count=0,
            unique_skus=0,
            data_source="live",
        )
    ]
    assert has_live_data(snapshots) is True


def test_has_live_data_with_orders() -> None:
    snapshots = [
        BusinessMetricsSnapshot(
            snapshot_date=date.today(),
            platform="amazon",
            marketplace="US",
            gmv=Decimal("0"),
            ad_spend=Decimal("0"),
            roi=None,
            order_count=5,
            unique_skus=2,
            data_source="live",
        )
    ]
    assert has_live_data(snapshots) is True


def test_has_live_data_empty_list() -> None:
    assert has_live_data([]) is False


@pytest.mark.asyncio
async def test_build_live_snapshots_empty_db() -> None:
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    service = MetricsAggregationService(mock_db)
    snapshots = await service.build_live_snapshots(days=7)

    assert snapshots == []


@pytest.mark.asyncio
async def test_build_live_snapshots_with_orders() -> None:
    mock_db = AsyncMock()

    order_row = MagicMock()
    order_row.sku = "SKU-001"
    order_row.quantity = 2
    order_row.item_price = "25.00"
    order_row.platform = "amazon"
    order_row.marketplace = "US"
    order_row.purchase_date = datetime.now(UTC)
    order_row.data_source = "spapi"

    order_result = MagicMock()
    order_result.scalars.return_value.all.return_value = [order_row]

    campaign_result = MagicMock()
    campaign_result.scalars.return_value.all.return_value = []

    mock_db.execute.side_effect = [order_result, campaign_result]

    service = MetricsAggregationService(mock_db)
    snapshots = await service.build_live_snapshots(days=7, platform="amazon", marketplace="US")

    assert len(snapshots) == 7
    for s in snapshots:
        assert s.data_source == "live"
        assert s.platform == "amazon"
        assert s.marketplace == "US"

    today = date.today()
    today_snapshot = next((s for s in snapshots if s.snapshot_date == today), None)
    assert today_snapshot is not None
    assert today_snapshot.gmv == Decimal("50.00")
    assert today_snapshot.order_count == 1
    assert today_snapshot.unique_skus == 1
