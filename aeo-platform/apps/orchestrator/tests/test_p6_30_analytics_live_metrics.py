"""P6-30: Analytics node live metrics fetch tests."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_fetch_live_metrics_returns_none_without_db() -> None:
    """When DB is unavailable, _fetch_live_metrics_from_db returns None."""
    import os

    from aeo_orchestrator.nodes.analytics import _fetch_live_metrics_from_db

    db_url = os.environ.pop("DB_URL_SYNC", None)
    db_url_async = os.environ.pop("DB_URL", None)
    try:
        result = await _fetch_live_metrics_from_db(
            platform="amazon",
            marketplace="US",
            days=7,
        )
        assert result is None
    finally:
        if db_url:
            os.environ["DB_URL_SYNC"] = db_url
        if db_url_async:
            os.environ["DB_URL"] = db_url_async


def test_generate_mock_metrics_still_works() -> None:
    """Mock metrics fallback should still generate valid snapshots."""
    from aeo_orchestrator.nodes.analytics import _generate_mock_metrics

    snapshots = _generate_mock_metrics(platform="amazon", marketplace="US", days=7)
    assert len(snapshots) == 7
    assert all(s.data_source == "mock" for s in snapshots)
    assert all(s.gmv > 0 for s in snapshots)
