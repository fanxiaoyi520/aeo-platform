"""P6-29: Live metrics aggregation from OrderRecord + AdSpendSnapshot."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import structlog
from aeo_shared.metrics_sdk import (
    AdSpendMetricRecord,
    BusinessMetricsSnapshot,
    OrderMetricRecord,
    build_daily_snapshot,
)
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.db.models import AdCampaign, AdSpendSnapshot, OrderRecord

logger = structlog.get_logger()


class MetricsAggregationService:
    """Aggregate live metrics from DB order records and ad spend snapshots."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def build_live_snapshots(
        self,
        *,
        days: int = 30,
        platform: str = "amazon",
        marketplace: str = "US",
    ) -> list[BusinessMetricsSnapshot]:
        """Build daily snapshots from real DB data for the last N days."""
        today = date.today()
        start_date = today - timedelta(days=days - 1)
        start_dt = datetime(start_date.year, start_date.month, start_date.day, tzinfo=UTC)

        orders = await self._fetch_orders(start_dt, platform, marketplace)
        ad_spends = await self._fetch_ad_spends(start_dt, platform)

        if not orders and not ad_spends:
            return []

        snapshots = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            snapshot = build_daily_snapshot(
                orders=orders,
                ad_spends=ad_spends,
                snapshot_date=day,
                platform=platform,
                marketplace=marketplace,
            )
            snapshots.append(
                BusinessMetricsSnapshot(
                    snapshot_date=snapshot.snapshot_date,
                    platform=snapshot.platform,
                    marketplace=snapshot.marketplace,
                    gmv=snapshot.gmv,
                    ad_spend=snapshot.ad_spend,
                    roi=snapshot.roi,
                    order_count=snapshot.order_count,
                    unique_skus=snapshot.unique_skus,
                    automation_rate=snapshot.automation_rate,
                    data_source="live",
                )
            )

        return snapshots

    async def _fetch_orders(
        self,
        start_dt: datetime,
        platform: str,
        marketplace: str,
    ) -> list[OrderMetricRecord]:
        """Fetch order records from DB since start_dt."""
        result = await self._db.execute(
            select(OrderRecord).where(
                and_(
                    OrderRecord.platform == platform,
                    OrderRecord.marketplace == marketplace,
                    OrderRecord.purchase_date >= start_dt,
                )
            )
        )
        rows = result.scalars().all()
        return [
            OrderMetricRecord(
                sku=row.sku,
                quantity=row.quantity,
                item_price=row.item_price,
                platform=row.platform,
                marketplace=row.marketplace,
                purchase_date=row.purchase_date,
                data_source=row.data_source,
            )
            for row in rows
        ]

    async def _fetch_ad_spends(
        self,
        start_dt: datetime,
        platform: str,
    ) -> list[AdSpendMetricRecord]:
        """Fetch ad spend snapshots from DB since start_dt for the given platform."""
        campaign_result = await self._db.execute(
            select(AdCampaign.id).where(AdCampaign.platform == platform)
        )
        campaign_ids = list(campaign_result.scalars().all())

        if not campaign_ids:
            return []

        spend_result = await self._db.execute(
            select(AdSpendSnapshot).where(
                and_(
                    AdSpendSnapshot.campaign_id.in_(campaign_ids),
                    AdSpendSnapshot.snapshot_date >= start_dt,
                )
            )
        )
        rows = spend_result.scalars().all()

        campaign_platform = {cid: platform for cid in campaign_ids}
        return [
            AdSpendMetricRecord(
                spend=row.spend,
                attributed_gmv=row.attributed_gmv,
                snapshot_date=row.snapshot_date,
                platform=campaign_platform.get(row.campaign_id, platform),
                data_source=row.data_source,
            )
            for row in rows
        ]


def has_live_data(snapshots: list[BusinessMetricsSnapshot]) -> bool:
    """Check if any snapshot has non-zero GMV or order count."""
    return any(s.gmv > 0 or s.order_count > 0 for s in snapshots)
