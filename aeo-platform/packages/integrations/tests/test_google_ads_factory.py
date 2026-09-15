"""Tests for Google Ads factory and fallback integration."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from aeo_integrations.amazon.fallback import FallbackWrapper
from aeo_integrations.google_ads import client as client_mod
from aeo_integrations.google_ads.client import MockGoogleAdsAdapter, get_google_ads_client
from aeo_integrations.google_ads.config import GoogleAdsSettings


@pytest.fixture(autouse=True)
def _reset_client() -> Generator[None, None, None]:
    client_mod._client = None
    yield
    client_mod._client = None


class TestGoogleAdsFactory:
    def test_mock_by_default(self) -> None:
        client = get_google_ads_client()
        assert isinstance(client, MockGoogleAdsAdapter)
        assert client.data_source == "mock"

    def test_mock_explicit(self) -> None:
        settings = GoogleAdsSettings(GOOGLE_ADS_DATA_SOURCE="mock")  # type: ignore[arg-type]
        client = get_google_ads_client(settings)
        assert isinstance(client, MockGoogleAdsAdapter)

    def test_google_no_fallback(self) -> None:
        settings = GoogleAdsSettings(
            GOOGLE_ADS_DATA_SOURCE="google",  # type: ignore[arg-type]
            GOOGLE_ADS_DEVELOPER_TOKEN="dev",
            GOOGLE_ADS_CLIENT_ID="cid",
            GOOGLE_ADS_CLIENT_SECRET="sec",
            GOOGLE_ADS_REFRESH_TOKEN="rt",
            GOOGLE_ADS_CUSTOMER_ID="123-456-7890",
            GOOGLE_ADS_FALLBACK_ENABLED="false",  # type: ignore[arg-type]
        )
        mock_adapter = MagicMock()
        mock_adapter.data_source = "google"
        with patch(
            "aeo_integrations.google_ads.adapter.GoogleAdsApiAdapter", return_value=mock_adapter
        ):
            client = get_google_ads_client(settings)
        assert not isinstance(client, FallbackWrapper)
        assert not isinstance(client, MockGoogleAdsAdapter)

    def test_google_with_fallback(self) -> None:
        settings = GoogleAdsSettings(
            GOOGLE_ADS_DATA_SOURCE="google",  # type: ignore[arg-type]
            GOOGLE_ADS_DEVELOPER_TOKEN="dev",
            GOOGLE_ADS_CLIENT_ID="cid",
            GOOGLE_ADS_CLIENT_SECRET="sec",
            GOOGLE_ADS_REFRESH_TOKEN="rt",
            GOOGLE_ADS_CUSTOMER_ID="123-456-7890",
            GOOGLE_ADS_FALLBACK_ENABLED="true",  # type: ignore[arg-type]
        )
        mock_adapter = MagicMock()
        mock_adapter.data_source = "google"
        with patch(
            "aeo_integrations.google_ads.adapter.GoogleAdsApiAdapter", return_value=mock_adapter
        ):
            client = get_google_ads_client(settings)
        assert isinstance(client, FallbackWrapper)
        assert client.data_source == "google"

    def test_singleton(self) -> None:
        c1 = get_google_ads_client()
        c2 = get_google_ads_client()
        assert c1 is c2

    def test_clean_customer_id(self) -> None:
        settings = GoogleAdsSettings(GOOGLE_ADS_CUSTOMER_ID="123-456-7890")
        assert settings.clean_customer_id == "1234567890"
