from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from aeo_integrations.amazon.config import AmazonDataSource, AmazonSettings, get_amazon_settings
from aeo_integrations.amazon.models import AmazonAdCampaign, AmazonAdSpendSnapshot
from aeo_integrations.amazon.spapi_adapter import SpApiAdvertisingAdapter

_MOCK_DIR = Path(__file__).resolve().parent / "mock"
_DEFAULT_FIXTURE = _MOCK_DIR / "sample_advertising.json"


class AdvertisingClient(Protocol):
    def get_campaign(self, campaign_id: str) -> AmazonAdCampaign: ...

    def list_campaigns(
        self,
        *,
        status: str | None = None,
        limit: int = 20,
    ) -> list[AmazonAdCampaign]: ...

    def list_spend_snapshots(
        self,
        *,
        campaign_id: str | None = None,
        limit: int = 50,
    ) -> list[AmazonAdSpendSnapshot]: ...


class MockAdvertisingAdapter:
    def __init__(self, fixture_path: Path | None = None) -> None:
        self._fixture_path = fixture_path or _DEFAULT_FIXTURE
        self._campaign_cache: dict[str, AmazonAdCampaign] | None = None
        self._snapshot_cache: list[AmazonAdSpendSnapshot] | None = None

    def _load_campaigns(self) -> dict[str, AmazonAdCampaign]:
        if self._campaign_cache is not None:
            return self._campaign_cache
        raw = json.loads(self._fixture_path.read_text(encoding="utf-8"))
        campaigns = [AmazonAdCampaign.model_validate(c) for c in raw["campaigns"]]
        self._campaign_cache = {c.campaign_id.upper(): c for c in campaigns}
        return self._campaign_cache

    def _load_snapshots(self) -> list[AmazonAdSpendSnapshot]:
        if self._snapshot_cache is not None:
            return self._snapshot_cache
        raw = json.loads(self._fixture_path.read_text(encoding="utf-8"))
        self._snapshot_cache = [
            AmazonAdSpendSnapshot.model_validate(s) for s in raw["spend_snapshots"]
        ]
        return self._snapshot_cache

    def get_campaign(self, campaign_id: str) -> AmazonAdCampaign:
        key = campaign_id.strip().upper()
        campaign = self._load_campaigns().get(key)
        if campaign is None:
            msg = f"Campaign not found: {campaign_id}"
            raise KeyError(msg)
        return campaign

    def list_campaigns(
        self,
        *,
        status: str | None = None,
        limit: int = 20,
    ) -> list[AmazonAdCampaign]:
        items = list(self._load_campaigns().values())
        if status:
            items = [c for c in items if c.status == status]
        return items[:limit]

    def list_spend_snapshots(
        self,
        *,
        campaign_id: str | None = None,
        limit: int = 50,
    ) -> list[AmazonAdSpendSnapshot]:
        items = self._load_snapshots()
        if campaign_id:
            key = campaign_id.strip().upper()
            items = [s for s in items if s.campaign_id.upper() == key]
        return items[:limit]


def get_advertising_client(
    settings: AmazonSettings | None = None,
) -> AdvertisingClient:
    resolved = settings or get_amazon_settings()
    if resolved.data_source == AmazonDataSource.MOCK:
        return MockAdvertisingAdapter()
    return SpApiAdvertisingAdapter(settings=resolved)
