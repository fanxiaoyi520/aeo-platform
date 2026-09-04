"""MV2-03 — competitor monitor diff detection tests."""

from __future__ import annotations

from aeo_shared.competitor_monitor import (
    ListingChange,
    ListingSnapshot,
    MonitorDiff,
    compute_diff,
)


def _snap(
    asin: str,
    price: float | None = None,
    rating: float | None = None,
    review_count: int | None = None,
) -> ListingSnapshot:
    return ListingSnapshot(asin=asin, price=price, rating=rating, review_count=review_count)


class TestComputeDiffChanges:
    def test_no_changes(self) -> None:
        prev = [_snap("B001", price=19.99, rating=4.5, review_count=100)]
        curr = [_snap("B001", price=19.99, rating=4.5, review_count=100)]
        diff = compute_diff("SKU1", prev, curr)
        assert diff.changes == []
        assert diff.new_listings == []
        assert diff.removed_listings == []
        assert not diff.has_significant_change

    def test_price_change(self) -> None:
        prev = [_snap("B001", price=20.0)]
        curr = [_snap("B001", price=21.0)]
        diff = compute_diff("SKU1", prev, curr)
        assert len(diff.changes) == 1
        c = diff.changes[0]
        assert c.asin == "B001"
        assert c.field == "price"
        assert c.old_value == 20.0
        assert c.new_value == 21.0
        assert c.delta == 1.0

    def test_rating_change(self) -> None:
        prev = [_snap("B001", rating=4.0)]
        curr = [_snap("B001", rating=4.5)]
        diff = compute_diff("SKU1", prev, curr)
        assert len(diff.changes) == 1
        c = diff.changes[0]
        assert c.field == "rating"
        assert c.delta == 0.5

    def test_review_count_change(self) -> None:
        prev = [_snap("B001", review_count=50)]
        curr = [_snap("B001", review_count=60)]
        diff = compute_diff("SKU1", prev, curr)
        assert len(diff.changes) == 1
        c = diff.changes[0]
        assert c.field == "review_count"
        assert c.delta == 10

    def test_multiple_field_changes(self) -> None:
        prev = [_snap("B001", price=10.0, rating=3.0, review_count=10)]
        curr = [_snap("B001", price=12.0, rating=4.0, review_count=20)]
        diff = compute_diff("SKU1", prev, curr)
        fields = {c.field for c in diff.changes}
        assert fields == {"price", "rating", "review_count"}

    def test_multiple_listings(self) -> None:
        prev = [
            _snap("B001", price=10.0),
            _snap("B002", price=20.0),
        ]
        curr = [
            _snap("B001", price=11.0),
            _snap("B002", price=20.0),
        ]
        diff = compute_diff("SKU1", prev, curr)
        assert len(diff.changes) == 1
        assert diff.changes[0].asin == "B001"


class TestNewAndRemovedListings:
    def test_new_listing_detected(self) -> None:
        prev = [_snap("B001", price=10.0)]
        curr = [
            _snap("B001", price=10.0),
            _snap("B002", price=15.0),
        ]
        diff = compute_diff("SKU1", prev, curr)
        assert len(diff.new_listings) == 1
        assert diff.new_listings[0].asin == "B002"
        assert diff.has_significant_change

    def test_removed_listing_detected(self) -> None:
        prev = [
            _snap("B001", price=10.0),
            _snap("B002", price=15.0),
        ]
        curr = [_snap("B001", price=10.0)]
        diff = compute_diff("SKU1", prev, curr)
        assert len(diff.removed_listings) == 1
        assert diff.removed_listings[0].asin == "B002"
        assert diff.has_significant_change

    def test_both_new_and_removed(self) -> None:
        prev = [_snap("B001", price=10.0)]
        curr = [_snap("B002", price=20.0)]
        diff = compute_diff("SKU1", prev, curr)
        assert len(diff.new_listings) == 1
        assert len(diff.removed_listings) == 1


class TestSignificanceThreshold:
    def test_price_change_below_threshold_not_significant(self) -> None:
        prev = [_snap("B001", price=100.0)]
        curr = [_snap("B001", price=104.0)]
        diff = compute_diff("SKU1", prev, curr, price_change_threshold=0.05)
        assert len(diff.changes) == 1
        assert not diff.has_significant_change

    def test_price_change_above_threshold_is_significant(self) -> None:
        prev = [_snap("B001", price=100.0)]
        curr = [_snap("B001", price=106.0)]
        diff = compute_diff("SKU1", prev, curr, price_change_threshold=0.05)
        assert diff.has_significant_change

    def test_custom_threshold(self) -> None:
        prev = [_snap("B001", price=100.0)]
        curr = [_snap("B001", price=110.0)]
        diff_strict = compute_diff("SKU1", prev, curr, price_change_threshold=0.05)
        diff_loose = compute_diff("SKU1", prev, curr, price_change_threshold=0.15)
        assert diff_strict.has_significant_change
        assert not diff_loose.has_significant_change

    def test_price_from_none_is_significant(self) -> None:
        prev = [_snap("B001", price=None)]
        curr = [_snap("B001", price=10.0)]
        diff = compute_diff("SKU1", prev, curr)
        assert diff.has_significant_change

    def test_price_to_none_is_significant(self) -> None:
        prev = [_snap("B001", price=10.0)]
        curr = [_snap("B001", price=None)]
        diff = compute_diff("SKU1", prev, curr)
        assert diff.has_significant_change

    def test_price_from_zero_to_nonzero_is_significant(self) -> None:
        prev = [_snap("B001", price=0.0)]
        curr = [_snap("B001", price=10.0)]
        diff = compute_diff("SKU1", prev, curr)
        assert diff.has_significant_change

    def test_rating_change_not_price_significant(self) -> None:
        prev = [_snap("B001", rating=3.0)]
        curr = [_snap("B001", rating=5.0)]
        diff = compute_diff("SKU1", prev, curr)
        assert len(diff.changes) == 1
        assert not diff.has_significant_change


class TestEmptySnapshots:
    def test_both_empty(self) -> None:
        diff = compute_diff("SKU1", [], [])
        assert diff.changes == []
        assert diff.new_listings == []
        assert diff.removed_listings == []
        assert not diff.has_significant_change

    def test_previous_empty_all_new(self) -> None:
        curr = [_snap("B001", price=10.0), _snap("B002", price=20.0)]
        diff = compute_diff("SKU1", [], curr)
        assert len(diff.new_listings) == 2
        assert diff.has_significant_change

    def test_current_empty_all_removed(self) -> None:
        prev = [_snap("B001", price=10.0)]
        diff = compute_diff("SKU1", prev, [])
        assert len(diff.removed_listings) == 1
        assert diff.has_significant_change


class TestMonitorDiffToDict:
    def test_to_dict_structure(self) -> None:
        diff = MonitorDiff(
            sku="SKU1",
            changes=[
                ListingChange(
                    asin="B001", field="price", old_value=10.0, new_value=12.0, delta=2.0
                ),
            ],
            new_listings=[_snap("B002", price=15.0)],
            removed_listings=[_snap("B003", price=8.0)],
            has_significant_change=True,
        )
        d = diff.to_dict()
        assert d["sku"] == "SKU1"
        assert len(d["changes"]) == 1
        assert d["changes"][0]["asin"] == "B001"
        assert d["changes"][0]["delta"] == 2.0
        assert len(d["new_listings"]) == 1
        assert d["new_listings"][0]["asin"] == "B002"
        assert len(d["removed_listings"]) == 1
        assert d["has_significant_change"] is True

    def test_to_dict_empty_diff(self) -> None:
        diff = MonitorDiff(sku="SKU1")
        d = diff.to_dict()
        assert d["changes"] == []
        assert d["new_listings"] == []
        assert d["removed_listings"] == []
        assert not d["has_significant_change"]
