"""Tests for MV1-07 business metrics SDK."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from aeo_shared.metrics_sdk import (
    AdSpendMetricRecord,
    BusinessMetricsSnapshot,
    OrderMetricRecord,
    build_daily_snapshot,
    compute_gmv,
    compute_roi,
    parse_money,
)


def test_parse_money_handles_string_and_decimal() -> None:
    assert parse_money("19.99") == Decimal("19.99")
    assert parse_money(Decimal("10.50")) == Decimal("10.50")
    assert parse_money(None) == Decimal("0")
    assert parse_money("") == Decimal("0")


def test_compute_gmv_sums_order_lines() -> None:
    orders = (
        OrderMetricRecord(sku="A", quantity=2, item_price="10.00"),
        OrderMetricRecord(sku="B", quantity=1, item_price="5.50"),
    )
    assert compute_gmv(orders) == Decimal("25.50")


def test_compute_roi_returns_none_when_no_spend() -> None:
    assert compute_roi(gmv=Decimal("100"), ad_spend=Decimal("0")) is None


def test_compute_roi_divides_gmv_by_spend() -> None:
    roi = compute_roi(gmv=Decimal("300"), ad_spend=Decimal("100"))
    assert roi == Decimal("3")


def test_build_daily_snapshot_aggregates_orders_and_ad_spend() -> None:
    snapshot_date = date(2026, 9, 1)
    orders = (
        OrderMetricRecord(
            sku="SKU-1",
            quantity=1,
            item_price="49.99",
            platform="amazon",
            marketplace="US",
            purchase_date=datetime(2026, 9, 1, 12, 0, tzinfo=UTC),
        ),
        OrderMetricRecord(
            sku="SKU-2",
            quantity=2,
            item_price="10.00",
            platform="amazon",
            marketplace="US",
            purchase_date=datetime(2026, 9, 1, 15, 0, tzinfo=UTC),
        ),
    )
    ad_spends = (
        AdSpendMetricRecord(
            spend="20.00",
            attributed_gmv="69.99",
            snapshot_date=datetime(2026, 9, 1, 0, 0, tzinfo=UTC),
            platform="amazon",
        ),
    )

    snapshot = build_daily_snapshot(
        orders,
        ad_spends,
        snapshot_date=snapshot_date,
        platform="amazon",
        marketplace="US",
    )

    assert snapshot.gmv == Decimal("69.99")
    assert snapshot.ad_spend == Decimal("20.00")
    assert snapshot.roi == Decimal("3.4995")
    assert snapshot.order_count == 2
    assert snapshot.unique_skus == 2
    assert snapshot.data_source == "mock"


def test_build_daily_snapshot_filters_by_date() -> None:
    orders = (
        OrderMetricRecord(
            sku="SKU-1",
            quantity=1,
            item_price="10.00",
            purchase_date=datetime(2026, 8, 31, 23, 0, tzinfo=UTC),
        ),
        OrderMetricRecord(
            sku="SKU-2",
            quantity=1,
            item_price="20.00",
            purchase_date=datetime(2026, 9, 1, 1, 0, tzinfo=UTC),
        ),
    )
    snapshot = build_daily_snapshot(
        orders,
        (),
        snapshot_date=date(2026, 9, 1),
        platform="amazon",
        marketplace="US",
    )
    assert snapshot.gmv == Decimal("20.00")
    assert snapshot.order_count == 1


def test_build_daily_snapshot_ignores_other_platforms() -> None:
    orders = (
        OrderMetricRecord(
            sku="SKU-1",
            quantity=1,
            item_price="10.00",
            platform="tiktok",
            purchase_date=datetime(2026, 9, 1, 1, 0, tzinfo=UTC),
        ),
    )
    snapshot = build_daily_snapshot(
        orders,
        (),
        snapshot_date=date(2026, 9, 1),
        platform="amazon",
        marketplace="US",
    )
    assert snapshot.order_count == 0
    assert snapshot.gmv == Decimal("0")


def test_business_metrics_snapshot_round_trip_dict() -> None:
    snapshot = BusinessMetricsSnapshot(
        snapshot_date=date(2026, 9, 1),
        platform="amazon",
        marketplace="US",
        gmv=Decimal("100"),
        ad_spend=Decimal("25"),
        roi=Decimal("4"),
        order_count=3,
        unique_skus=2,
    )
    payload = snapshot.to_dict()
    restored = BusinessMetricsSnapshot.from_dict(payload)
    assert restored == snapshot
