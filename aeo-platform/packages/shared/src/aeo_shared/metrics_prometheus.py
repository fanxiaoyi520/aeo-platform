"""MV1-07 — Prometheus export adapter (thin wrapper over prometheus_client)."""

from __future__ import annotations

from prometheus_client import Gauge

from aeo_shared.metrics_sdk import BusinessMetricsSnapshot

_LABELS = ("platform", "marketplace", "snapshot_date")
_gauges: dict[str, Gauge] = {}


def _gauge(name: str, documentation: str) -> Gauge:
    if name not in _gauges:
        _gauges[name] = Gauge(name, documentation, _LABELS)
    return _gauges[name]


def publish_snapshot(snapshot: BusinessMetricsSnapshot) -> None:
    labels = {
        "platform": snapshot.platform,
        "marketplace": snapshot.marketplace,
        "snapshot_date": snapshot.snapshot_date.isoformat(),
    }
    _gauge("aeo_biz_gmv", "Daily GMV in currency units.").labels(**labels).set(float(snapshot.gmv))
    _gauge("aeo_biz_ad_spend", "Daily ad spend in currency units.").labels(**labels).set(
        float(snapshot.ad_spend)
    )
    roi_value = float(snapshot.roi) if snapshot.roi is not None else 0.0
    _gauge("aeo_biz_roi", "Daily ROI ratio (GMV basis / ad spend).").labels(**labels).set(roi_value)
    _gauge("aeo_biz_order_count", "Daily order count.").labels(**labels).set(snapshot.order_count)
