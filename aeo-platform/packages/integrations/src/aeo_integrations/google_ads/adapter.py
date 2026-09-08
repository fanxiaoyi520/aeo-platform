"""Google Ads API adapter — stub for production use."""

from __future__ import annotations

from aeo_integrations.google_ads.models import GoogleAdCampaign, GoogleAdSpendSnapshot


class GoogleAdsApiAdapter:
    """Production Google Ads API adapter (not yet implemented)."""

    def __init__(self, developer_token: str, customer_id: str) -> None:
        self._developer_token = developer_token
        self._customer_id = customer_id

    def get_campaign(self, campaign_id: str) -> GoogleAdCampaign:
        raise NotImplementedError("Google Ads API integration pending")

    def list_campaigns(
        self, *, status: str | None = None, limit: int = 20
    ) -> list[GoogleAdCampaign]:
        raise NotImplementedError("Google Ads API integration pending")

    def list_spend_snapshots(
        self, *, campaign_id: str | None = None, limit: int = 50
    ) -> list[GoogleAdSpendSnapshot]:
        raise NotImplementedError("Google Ads API integration pending")
