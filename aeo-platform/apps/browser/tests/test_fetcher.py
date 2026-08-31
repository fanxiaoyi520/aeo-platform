"""Tests for aeo_browser — MS4."""

from __future__ import annotations

import pytest
from aeo_browser.config import is_browser_enabled
from aeo_browser.models import ListingSnapshot


def test_is_browser_enabled_default_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BROWSER_ENABLED", raising=False)
    assert is_browser_enabled() is False


def test_is_browser_enabled_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BROWSER_ENABLED", "true")
    assert is_browser_enabled() is True


def test_listing_snapshot_roundtrip() -> None:
    snapshot = ListingSnapshot(
        asin="B07JFSRMBH",
        title="Test Scanner",
        bullets=("Bullet 1", "Bullet 2"),
        price="$99.99",
        rating=4.5,
        review_count=1200,
        screenshot_path="data/screenshots/B07_test.png",
        fetched_at="2026-08-30T00:00:00+00:00",
    )
    restored = ListingSnapshot.from_dict(snapshot.to_dict())
    assert restored.asin == snapshot.asin
    assert restored.title == snapshot.title
    assert restored.bullets == snapshot.bullets


@pytest.mark.asyncio
async def test_fetch_listing_invalid_asin() -> None:
    from aeo_browser.fetcher import fetch_listing

    with pytest.raises(ValueError, match="invalid ASIN"):
        await fetch_listing("bad-asin")
