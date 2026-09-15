"""Tests for Facebook Ads factory and fallback integration."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from aeo_integrations.amazon.fallback import FallbackWrapper
from aeo_integrations.facebook_ads import client as client_mod
from aeo_integrations.facebook_ads.client import MockFacebookAdsAdapter, get_facebook_ads_client
from aeo_integrations.facebook_ads.config import FacebookAdsSettings


@pytest.fixture(autouse=True)
def _reset_client() -> Generator[None, None, None]:
    client_mod._client = None
    yield
    client_mod._client = None


class TestFacebookAdsFactory:
    def test_mock_by_default(self) -> None:
        client = get_facebook_ads_client()
        assert isinstance(client, MockFacebookAdsAdapter)
        assert client.data_source == "mock"

    def test_mock_explicit(self) -> None:
        settings = FacebookAdsSettings(FACEBOOK_ADS_DATA_SOURCE="mock")  # type: ignore[arg-type]
        client = get_facebook_ads_client(settings)
        assert isinstance(client, MockFacebookAdsAdapter)

    def test_facebook_no_fallback(self) -> None:
        settings = FacebookAdsSettings(
            FACEBOOK_ADS_DATA_SOURCE="facebook",  # type: ignore[arg-type]
            FACEBOOK_ADS_ACCESS_TOKEN="tok",
            FACEBOOK_ADS_AD_ACCOUNT_ID="123",
            FACEBOOK_ADS_FALLBACK_ENABLED="false",  # type: ignore[arg-type]
        )
        mock_adapter = MagicMock()
        mock_adapter.data_source = "facebook"
        with patch(
            "aeo_integrations.facebook_ads.adapter.FacebookAdsApiAdapter", return_value=mock_adapter
        ):
            client = get_facebook_ads_client(settings)
        assert not isinstance(client, FallbackWrapper)
        assert not isinstance(client, MockFacebookAdsAdapter)

    def test_facebook_with_fallback(self) -> None:
        settings = FacebookAdsSettings(
            FACEBOOK_ADS_DATA_SOURCE="facebook",  # type: ignore[arg-type]
            FACEBOOK_ADS_ACCESS_TOKEN="tok",
            FACEBOOK_ADS_AD_ACCOUNT_ID="123",
            FACEBOOK_ADS_FALLBACK_ENABLED="true",  # type: ignore[arg-type]
        )
        mock_adapter = MagicMock()
        mock_adapter.data_source = "facebook"
        with patch(
            "aeo_integrations.facebook_ads.adapter.FacebookAdsApiAdapter", return_value=mock_adapter
        ):
            client = get_facebook_ads_client(settings)
        assert isinstance(client, FallbackWrapper)
        assert client.data_source == "facebook"

    def test_singleton(self) -> None:
        c1 = get_facebook_ads_client()
        c2 = get_facebook_ads_client()
        assert c1 is c2
