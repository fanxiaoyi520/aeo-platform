"""Tests for MV1-07 Prometheus export adapter."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from aeo_shared.metrics_prometheus import publish_snapshot
from aeo_shared.metrics_sdk import BusinessMetricsSnapshot
from prometheus_client import REGISTRY, generate_latest


def test_publish_snapshot_exposes_prometheus_gauges() -> None:
    snapshot = BusinessMetricsSnapshot(
        snapshot_date=date(2026, 9, 1),
        platform="amazon",
        marketplace="US",
        gmv=Decimal("150.00"),
        ad_spend=Decimal("50.00"),
        roi=Decimal("3"),
        order_count=4,
        unique_skus=2,
    )
    publish_snapshot(snapshot)
    output = generate_latest(REGISTRY).decode("utf-8")
    assert "aeo_biz_gmv" in output
    assert 'platform="amazon"' in output
    assert "aeo_biz_ad_spend" in output
    assert "aeo_biz_roi" in output
