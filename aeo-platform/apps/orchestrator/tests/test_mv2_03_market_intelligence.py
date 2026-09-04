"""MV2-03 — market intelligence service tests."""

from __future__ import annotations

from aeo_orchestrator.nodes.market_intelligence import (
    MarketIntelReport,
    MarketIntelService,
    ScanInput,
)
from aeo_shared.competitor_monitor import ListingSnapshot


def _snap(
    asin: str,
    price: float | None = None,
    rating: float | None = None,
    review_count: int | None = None,
) -> ListingSnapshot:
    return ListingSnapshot(asin=asin, price=price, rating=rating, review_count=review_count)


class TestMarketIntelServiceScan:
    def test_scan_produces_report(self) -> None:
        service = MarketIntelService()
        prev = [_snap("B001", price=20.0, rating=4.0, review_count=100)]
        curr = [_snap("B001", price=21.0, rating=4.0, review_count=110)]
        inp = ScanInput(
            sku="SKU1",
            platform="amazon",
            marketplace="US",
            price=19.99,
            rating=4.2,
            review_count=50,
            has_title=True,
            has_bullets=True,
            has_keywords=True,
            has_images=True,
            previous_competitors=prev,
            current_competitors=curr,
        )
        report = service.scan(inp)
        assert isinstance(report, MarketIntelReport)
        assert report.sku == "SKU1"
        assert report.diff is not None
        assert report.selection_result is not None
        assert report.selection_result.total_score > 0

    def test_scan_detects_price_change(self) -> None:
        service = MarketIntelService()
        prev = [_snap("B001", price=100.0)]
        curr = [_snap("B001", price=120.0)]
        inp = ScanInput(
            sku="SKU1",
            current_competitors=curr,
            previous_competitors=prev,
        )
        report = service.scan(inp)
        assert report.diff.has_significant_change
        assert len(report.diff.changes) == 1

    def test_scan_with_no_previous(self) -> None:
        service = MarketIntelService()
        curr = [_snap("B001", price=15.0, rating=4.0, review_count=50)]
        inp = ScanInput(
            sku="SKU1",
            current_competitors=curr,
        )
        report = service.scan(inp)
        assert len(report.diff.new_listings) == 1
        assert report.selection_result is not None

    def test_scan_with_no_competitors(self) -> None:
        service = MarketIntelService()
        inp = ScanInput(
            sku="SKU1",
            price=19.99,
            has_title=True,
            has_bullets=True,
            has_keywords=False,
            has_images=True,
        )
        report = service.scan(inp)
        assert report.diff.changes == []
        assert report.selection_result is not None
        assert report.selection_result.competitor_count == 0

    def test_scan_suggests_actions(self) -> None:
        service = MarketIntelService()
        prev = [_snap("B001", price=100.0)]
        curr = [_snap("B001", price=130.0)]
        inp = ScanInput(
            sku="SKU1",
            price=95.0,
            has_title=True,
            has_bullets=True,
            has_keywords=True,
            has_images=True,
            previous_competitors=prev,
            current_competitors=curr,
        )
        report = service.scan(inp)
        assert len(report.suggested_actions) > 0

    def test_scan_no_action_when_stable(self) -> None:
        service = MarketIntelService()
        competitors = [_snap("B001", price=20.0, rating=4.0, review_count=100)]
        inp = ScanInput(
            sku="SKU1",
            price=19.99,
            has_title=True,
            has_bullets=True,
            has_keywords=True,
            has_images=True,
            previous_competitors=competitors,
            current_competitors=competitors,
        )
        report = service.scan(inp)
        assert not report.diff.has_significant_change
        assert len(report.suggested_actions) == 0


class TestMarketIntelReportToDict:
    def test_to_dict_structure(self) -> None:
        service = MarketIntelService()
        curr = [_snap("B001", price=15.0)]
        inp = ScanInput(sku="SKU1", current_competitors=curr)
        report = service.scan(inp)
        d = report.to_dict()
        assert "sku" in d
        assert "diff" in d
        assert "selection" in d
        assert "suggested_actions" in d
        assert "scanned_at" in d
