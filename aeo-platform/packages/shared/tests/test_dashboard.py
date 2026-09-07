"""MV4-06 — DashboardService + compute_automation_rate tests."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from aeo_shared.dashboard import DashboardService, compute_automation_rate
from aeo_shared.metrics_sdk import BusinessMetricsSnapshot


def _make_snapshots(days: int = 7) -> list[BusinessMetricsSnapshot]:
    today = date.today()
    return [
        BusinessMetricsSnapshot(
            snapshot_date=today - timedelta(days=i),
            platform="amazon",
            marketplace="US",
            gmv=Decimal(str(800 + i * 50)),
            ad_spend=Decimal(str(200 + i * 10)),
            roi=Decimal(str(3.5 + i * 0.1)),
            order_count=20 + i * 3,
            unique_skus=5 + i,
            automation_rate=Decimal("0.45"),
            data_source="mock",
        )
        for i in range(days)
    ]


class TestComputeAutomationRate:
    def test_returns_decimal_between_0_and_1(self) -> None:
        rate = compute_automation_rate(auto_completed=45, total=100)
        assert isinstance(rate, Decimal)
        assert Decimal("0") <= rate <= Decimal("1")

    def test_correct_calculation(self) -> None:
        rate = compute_automation_rate(auto_completed=40, total=100)
        assert rate == Decimal("0.4")

    def test_zero_total_returns_none(self) -> None:
        rate = compute_automation_rate(auto_completed=0, total=0)
        assert rate is None

    def test_zero_auto_returns_zero(self) -> None:
        rate = compute_automation_rate(auto_completed=0, total=100)
        assert rate == Decimal("0")


class TestDashboardService:
    def test_build_returns_required_keys(self) -> None:
        snapshots = _make_snapshots()
        service = DashboardService()
        dashboard = service.build(snapshots=snapshots, auto_completed=45, total=100)

        assert "gmv" in dashboard
        assert "roi" in dashboard
        assert "ad_spend" in dashboard
        assert "order_count" in dashboard
        assert "automation_rate" in dashboard
        assert "trend" in dashboard
        assert "period_days" in dashboard

    def test_gmv_is_aggregated(self) -> None:
        snapshots = _make_snapshots(3)
        service = DashboardService()
        dashboard = service.build(snapshots=snapshots, auto_completed=30, total=100)

        expected_gmv = sum(s.gmv for s in snapshots)
        assert dashboard["gmv"] == str(expected_gmv)

    def test_automation_rate_from_input(self) -> None:
        snapshots = _make_snapshots()
        service = DashboardService()
        dashboard = service.build(snapshots=snapshots, auto_completed=50, total=100)

        assert dashboard["automation_rate"] == "0.5000"

    def test_trend_has_daily_entries(self) -> None:
        snapshots = _make_snapshots(5)
        service = DashboardService()
        dashboard = service.build(snapshots=snapshots, auto_completed=40, total=80)

        assert len(dashboard["trend"]) == 5
        for entry in dashboard["trend"]:
            assert "date" in entry
            assert "gmv" in entry
            assert "roi" in entry

    def test_empty_snapshots_returns_zero_dashboard(self) -> None:
        service = DashboardService()
        dashboard = service.build(snapshots=[], auto_completed=0, total=0)

        assert dashboard["gmv"] == "0"
        assert dashboard["order_count"] == 0
        assert dashboard["automation_rate"] is None
