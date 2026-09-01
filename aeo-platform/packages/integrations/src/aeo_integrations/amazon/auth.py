from __future__ import annotations

from aeo_integrations.amazon.config import AmazonDataSource, get_amazon_settings
from aeo_integrations.amazon.models import AmazonAccessToken


def get_access_token() -> AmazonAccessToken:
    settings = get_amazon_settings()
    if settings.data_source == AmazonDataSource.MOCK:
        return AmazonAccessToken(access_token="mock-access-token", expires_in=3600)
    if not settings.sp_api_refresh_token:
        msg = "SP_API_REFRESH_TOKEN is required when AMAZON_DATA_SOURCE=spapi"
        raise NotImplementedError(msg)
    msg = "SP-API OAuth token refresh is not implemented yet (P1-03 / MV0-02)"
    raise NotImplementedError(msg)
