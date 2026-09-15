"""Facebook Ads integration."""

from aeo_integrations.facebook_ads.client import (
    FacebookAdsClient,
    MockFacebookAdsAdapter,
    get_facebook_ads_client,
)
from aeo_integrations.facebook_ads.config import (
    FacebookAdsDataSource,
    FacebookAdsSettings,
    get_facebook_ads_settings,
)
from aeo_integrations.facebook_ads.models import FacebookAdCampaign, FacebookAdSpendSnapshot

__all__ = [
    "FacebookAdsDataSource",
    "FacebookAdsSettings",
    "get_facebook_ads_settings",
    "FacebookAdCampaign",
    "FacebookAdSpendSnapshot",
    "FacebookAdsClient",
    "MockFacebookAdsAdapter",
    "get_facebook_ads_client",
]
