"""Facebook Ads integration."""

from aeo_integrations.facebook_ads.client import (
    FacebookAdsClient,
    MockFacebookAdsAdapter,
    get_facebook_ads_client,
)
from aeo_integrations.facebook_ads.models import FacebookAdCampaign, FacebookAdSpendSnapshot

__all__ = [
    "FacebookAdCampaign",
    "FacebookAdSpendSnapshot",
    "FacebookAdsClient",
    "MockFacebookAdsAdapter",
    "get_facebook_ads_client",
]
