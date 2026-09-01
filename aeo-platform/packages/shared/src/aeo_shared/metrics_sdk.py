"""MV1-07 — GMV/ROI business metrics SDK (mock / MV1-06 aligned)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True)
class OrderMetricRecord:
    sku: str
    quantity: int = 1
    item_price: str | Decimal | None = None
    platform: str = "amazon"
    marketplace: str = "US"
    purchase_date: datetime | None = None
    data_source: str = "mock"


@dataclass(frozen=True)
class AdSpendMetricRecord:
    spend: str | Decimal | None = None
    attributed_gmv: str | Decimal | None = None
    snapshot_date: datetime | None = None
    platform: str = "amazon"
    data_source: str = "mock"


@dataclass(frozen=True)
class BusinessMetricsSnapshot:
    snapshot_date: date
    platform: str
    marketplace: str
    gmv: Decimal
    ad_spend: Decimal
    roi: Decimal | None
    order_count: int
    unique_skus: int
    data_source: str = "mock"

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_date": self.snapshot_date.isoformat(),
            "platform": self.platform,
            "marketplace": self.marketplace,
            "gmv": str(self.gmv),
            "ad_spend": str(self.ad_spend),
            "roi": str(self.roi) if self.roi is not None else None,
            "order_count": self.order_count,
            "unique_skus": self.unique_skus,
            "data_source": self.data_source,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> BusinessMetricsSnapshot:
        roi_raw = payload.get("roi")
        return cls(
            snapshot_date=date.fromisoformat(str(payload["snapshot_date"])),
            platform=str(payload["platform"]),
            marketplace=str(payload["marketplace"]),
            gmv=Decimal(str(payload["gmv"])),
            ad_spend=Decimal(str(payload["ad_spend"])),
            roi=Decimal(str(roi_raw)) if roi_raw is not None else None,
            order_count=int(payload["order_count"]),
            unique_skus=int(payload["unique_skus"]),
            data_source=str(payload.get("data_source", "mock")),
        )


def parse_money(value: str | Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    text = str(value).strip()
    if not text:
        return Decimal("0")
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        msg = f"invalid money value: {value!r}"
        raise ValueError(msg) from exc


def compute_gmv(orders: Iterable[OrderMetricRecord]) -> Decimal:
    total = Decimal("0")
    for order in orders:
        line_total = parse_money(order.item_price) * order.quantity
        total += line_total
    return total


def compute_roi(*, gmv: Decimal, ad_spend: Decimal) -> Decimal | None:
    if ad_spend <= 0:
        return None
    return (gmv / ad_spend).quantize(Decimal("0.0001"))


def _matches_snapshot_day(value: datetime | None, snapshot_date: date) -> bool:
    if value is None:
        return False
    return value.date() == snapshot_date


def build_daily_snapshot(
    orders: Iterable[OrderMetricRecord],
    ad_spends: Iterable[AdSpendMetricRecord],
    *,
    snapshot_date: date,
    platform: str,
    marketplace: str,
) -> BusinessMetricsSnapshot:
    day_orders = [
        order
        for order in orders
        if order.platform == platform
        and order.marketplace == marketplace
        and _matches_snapshot_day(order.purchase_date, snapshot_date)
    ]

    day_ad_spends = [
        item
        for item in ad_spends
        if item.platform == platform and _matches_snapshot_day(item.snapshot_date, snapshot_date)
    ]

    gmv = compute_gmv(day_orders)
    ad_spend = Decimal("0")
    attributed = Decimal("0")
    for item in day_ad_spends:
        ad_spend += parse_money(item.spend)
        attributed += parse_money(item.attributed_gmv)
    roi_basis = attributed if attributed > 0 else gmv
    unique_skus = len({order.sku for order in day_orders})

    return BusinessMetricsSnapshot(
        snapshot_date=snapshot_date,
        platform=platform,
        marketplace=marketplace,
        gmv=gmv,
        ad_spend=ad_spend,
        roi=compute_roi(gmv=roi_basis, ad_spend=ad_spend),
        order_count=len(day_orders),
        unique_skus=unique_skus,
        data_source="mock",
    )
