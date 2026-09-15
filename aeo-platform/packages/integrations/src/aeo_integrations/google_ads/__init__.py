"""Google Ads integration."""

from aeo_integrations.google_ads.client import (
    GoogleAdsClient,
    MockGoogleAdsAdapter,
    get_google_ads_client,
)
from aeo_integrations.google_ads.config import (
    GoogleAdsDataSource,
    GoogleAdsSettings,
    get_google_ads_settings,
)
from aeo_integrations.google_ads.models import GoogleAdCampaign, GoogleAdSpendSnapshot

__all__ = [
    "GoogleAdsDataSource",
    "GoogleAdsSettings",
    "get_google_ads_settings",
    "GoogleAdCampaign",
    "GoogleAdSpendSnapshot",
    "GoogleAdsClient",
    "MockGoogleAdsAdapter",
    "get_google_ads_client",
]
