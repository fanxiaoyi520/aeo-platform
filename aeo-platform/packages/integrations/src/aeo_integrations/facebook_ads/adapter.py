"""Facebook Ads API adapter — stub for production use."""

from __future__ import annotations

from aeo_integrations.facebook_ads.models import FacebookAdCampaign, FacebookAdSpendSnapshot


class FacebookAdsApiAdapter:
    """Production Facebook Ads API adapter (not yet implemented)."""

    def __init__(self, access_token: str, ad_account_id: str) -> None:
        self._access_token = access_token
        self._ad_account_id = ad_account_id

    def get_campaign(self, campaign_id: str) -> FacebookAdCampaign:
        raise NotImplementedError("Facebook Ads API integration pending")

    def list_campaigns(
        self, *, status: str | None = None, limit: int = 20
    ) -> list[FacebookAdCampaign]:
        raise NotImplementedError("Facebook Ads API integration pending")

    def list_spend_snapshots(
        self, *, campaign_id: str | None = None, limit: int = 50
    ) -> list[FacebookAdSpendSnapshot]:
        raise NotImplementedError("Facebook Ads API integration pending")
