from __future__ import annotations

import time

from aeo_integrations.amazon.config import AmazonDataSource, AmazonSettings, get_amazon_settings
from aeo_integrations.amazon.models import AmazonAccessToken


class AmazonCredentialError(Exception):
    """Raised when SP-API credentials are missing or invalid."""


_token_cache: AmazonAccessToken | None = None
_token_expires_at: float = 0.0


def _build_sp_api_credentials(settings: AmazonSettings) -> dict[str, str]:
    return {
        "lwa_app_id": settings.sp_api_client_id,
        "lwa_client_secret": settings.sp_api_client_secret,
    }


def get_access_token() -> AmazonAccessToken:
    global _token_cache, _token_expires_at  # noqa: PLW0603

    settings = get_amazon_settings()
    if settings.data_source == AmazonDataSource.MOCK:
        return AmazonAccessToken(access_token="mock-access-token", expires_in=3600)

    if _token_cache is not None and time.monotonic() < _token_expires_at:
        return _token_cache

    if not settings.sp_api_refresh_token:
        msg = "SP_API_REFRESH_TOKEN is required when AMAZON_DATA_SOURCE=spapi"
        raise AmazonCredentialError(msg)
    if not settings.sp_api_client_id or not settings.sp_api_client_secret:
        msg = "SP_API_CLIENT_ID and SP_API_CLIENT_SECRET are required when AMAZON_DATA_SOURCE=spapi"
        raise AmazonCredentialError(msg)

    from sp_api.auth import AccessTokenClient  # type: ignore[import-untyped]

    credentials = _build_sp_api_credentials(settings)
    client = AccessTokenClient(
        refresh_token=settings.sp_api_refresh_token,
        credentials=credentials,
    )
    response = client.get_auth()

    token = AmazonAccessToken(
        access_token=response.access_token,
        expires_in=response.expires_in,
        token_type=response.token_type or "bearer",
    )

    _token_cache = token
    _token_expires_at = time.monotonic() + max(token.expires_in - 60, 60)

    return token


def clear_token_cache() -> None:
    global _token_cache, _token_expires_at  # noqa: PLW0603
    _token_cache = None
    _token_expires_at = 0.0
