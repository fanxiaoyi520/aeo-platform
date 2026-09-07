"""MV4-06 — business metrics dashboard aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from aeo_shared.metrics_sdk import BusinessMetricsSnapshot


def compute_automation_rate(*, auto_completed: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return (Decimal(str(auto_completed)) / Decimal(str(total))).quantize(Decimal("0.0001"))


def _generate_mock_snapshots(days: int = 30) -> list[BusinessMetricsSnapshot]:
    today = date.today()
    snapshots = []
    for i in range(days):
        day = today - timedelta(days=i)
        gmv = Decimal(str(800 + (i * 20)))
        ad_spend = Decimal(str(200 + (i * 5)))
        roi = (gmv / ad_spend).quantize(Decimal("0.01")) if ad_spend > 0 else None
        auto_rate = Decimal("0.45") if i % 3 != 0 else Decimal("0.38")
        snapshots.append(
            BusinessMetricsSnapshot(
                snapshot_date=day,
                platform="amazon",
                marketplace="US",
                gmv=gmv,
                ad_spend=ad_spend,
                roi=roi,
                order_count=20 + i * 2,
                unique_skus=5 + i // 3,
                automation_rate=auto_rate,
                data_source="mock",
            )
        )
    return snapshots


@dataclass
class DashboardService:
    """Aggregate business metrics into a dashboard payload."""

    def build(
        self,
        *,
        snapshots: list[BusinessMetricsSnapshot],
        auto_completed: int,
        total: int,
    ) -> dict[str, Any]:
        if not snapshots:
            return {
                "gmv": "0",
                "roi": None,
                "ad_spend": "0",
                "order_count": 0,
                "automation_rate": None,
                "trend": [],
                "period_days": 0,
            }

        total_gmv = sum(s.gmv for s in snapshots)
        total_ad_spend = sum(s.ad_spend for s in snapshots)
        total_orders = sum(s.order_count for s in snapshots)
        rois = [s.roi for s in snapshots if s.roi is not None]
        avg_roi: Decimal | None = (
            Decimal(str(sum(rois) / len(rois))).quantize(Decimal("0.01"))
            if rois
            else None
        )
        automation_rate = compute_automation_rate(auto_completed=auto_completed, total=total)

        trend = [
            {
                "date": s.snapshot_date.isoformat(),
                "gmv": str(s.gmv),
                "roi": str(s.roi) if s.roi is not None else None,
                "order_count": s.order_count,
                "automation_rate": str(s.automation_rate)
                if s.automation_rate is not None
                else None,
            }
            for s in snapshots
        ]

        return {
            "gmv": str(total_gmv),
            "roi": str(avg_roi) if avg_roi is not None else None,
            "ad_spend": str(total_ad_spend),
            "order_count": total_orders,
            "automation_rate": str(automation_rate) if automation_rate is not None else None,
            "trend": trend,
            "period_days": len(snapshots),
        }


def get_dashboard_service() -> DashboardService:
    return DashboardService()
