"""MV4-06 — BusinessMetricsSnapshot automation_rate field tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from aeo_shared.metrics_sdk import BusinessMetricsSnapshot


def test_snapshot_has_automation_rate_field() -> None:
    snapshot = BusinessMetricsSnapshot(
        snapshot_date=date.today(),
        platform="amazon",
        marketplace="US",
        gmv=Decimal("1000"),
        ad_spend=Decimal("200"),
        roi=Decimal("5.0"),
        order_count=50,
        unique_skus=10,
        automation_rate=Decimal("0.45"),
    )
    assert snapshot.automation_rate == Decimal("0.45")


def test_snapshot_automation_rate_defaults_none() -> None:
    snapshot = BusinessMetricsSnapshot(
        snapshot_date=date.today(),
        platform="amazon",
        marketplace="US",
        gmv=Decimal("500"),
        ad_spend=Decimal("100"),
        roi=Decimal("5.0"),
        order_count=20,
        unique_skus=5,
    )
    assert snapshot.automation_rate is None


def test_snapshot_to_dict_includes_automation_rate() -> None:
    snapshot = BusinessMetricsSnapshot(
        snapshot_date=date(2026, 9, 7),
        platform="amazon",
        marketplace="US",
        gmv=Decimal("800"),
        ad_spend=Decimal("200"),
        roi=Decimal("4.0"),
        order_count=30,
        unique_skus=8,
        automation_rate=Decimal("0.55"),
    )
    d = snapshot.to_dict()
    assert "automation_rate" in d
    assert d["automation_rate"] == "0.55"


def test_snapshot_from_dict_includes_automation_rate() -> None:
    payload = {
        "snapshot_date": "2026-09-07",
        "platform": "amazon",
        "marketplace": "US",
        "gmv": "800",
        "ad_spend": "200",
        "roi": "4.0",
        "order_count": 30,
        "unique_skus": 8,
        "automation_rate": "0.55",
        "data_source": "mock",
    }
    snapshot = BusinessMetricsSnapshot.from_dict(payload)
    assert snapshot.automation_rate == Decimal("0.55")
