"""Google Ads — Protocol + MockAdapter + Factory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from aeo_integrations.google_ads.models import GoogleAdCampaign, GoogleAdSpendSnapshot

_MOCK_DIR = Path(__file__).resolve().parent / "mock"
_DEFAULT_FIXTURE = _MOCK_DIR / "sample_google_ads.json"


class GoogleAdsClient(Protocol):
    """Read-only Google Ads API client."""

    def get_campaign(self, campaign_id: str) -> GoogleAdCampaign: ...

    def list_campaigns(
        self, *, status: str | None = None, limit: int = 20
    ) -> list[GoogleAdCampaign]: ...

    def list_spend_snapshots(
        self, *, campaign_id: str | None = None, limit: int = 50
    ) -> list[GoogleAdSpendSnapshot]: ...


class MockGoogleAdsAdapter:
    """Mock Google Ads adapter using local JSON fixtures."""

    def __init__(self, fixture_path: Path | None = None) -> None:
        self._fixture_path = fixture_path or _DEFAULT_FIXTURE
        self._campaign_cache: dict[str, GoogleAdCampaign] | None = None
        self._snapshot_cache: list[GoogleAdSpendSnapshot] | None = None

    def _load_campaigns(self) -> dict[str, GoogleAdCampaign]:
        if self._campaign_cache is not None:
            return self._campaign_cache
        raw = json.loads(self._fixture_path.read_text(encoding="utf-8"))
        campaigns = [GoogleAdCampaign.model_validate(c) for c in raw["campaigns"]]
        self._campaign_cache = {c.campaign_id.upper(): c for c in campaigns}
        return self._campaign_cache

    def _load_snapshots(self) -> list[GoogleAdSpendSnapshot]:
        if self._snapshot_cache is not None:
            return self._snapshot_cache
        raw = json.loads(self._fixture_path.read_text(encoding="utf-8"))
        self._snapshot_cache = [
            GoogleAdSpendSnapshot.model_validate(s) for s in raw["spend_snapshots"]
        ]
        return self._snapshot_cache

    def get_campaign(self, campaign_id: str) -> GoogleAdCampaign:
        key = campaign_id.strip().upper()
        campaign = self._load_campaigns().get(key)
        if campaign is None:
            msg = f"Campaign not found: {campaign_id}"
            raise KeyError(msg)
        return campaign

    def list_campaigns(
        self, *, status: str | None = None, limit: int = 20
    ) -> list[GoogleAdCampaign]:
        items = list(self._load_campaigns().values())
        if status:
            items = [c for c in items if c.status == status]
        return items[:limit]

    def list_spend_snapshots(
        self, *, campaign_id: str | None = None, limit: int = 50
    ) -> list[GoogleAdSpendSnapshot]:
        items = self._load_snapshots()
        if campaign_id:
            key = campaign_id.strip().upper()
            items = [s for s in items if s.campaign_id.upper() == key]
        return items[:limit]


_client: MockGoogleAdsAdapter | None = None


def get_google_ads_client() -> MockGoogleAdsAdapter:
    """Return the singleton mock Google Ads client."""
    global _client
    if _client is None:
        _client = MockGoogleAdsAdapter()
    return _client
