"""Tests for P6-22: SP-API degradation / fallback strategy."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
import requests
from aeo_integrations.amazon.auth import AmazonCredentialError
from aeo_integrations.amazon.config import AmazonDataSource, AmazonSettings
from aeo_integrations.amazon.fallback import FallbackWrapper, _is_fallback_error


@pytest.fixture
def settings() -> AmazonSettings:
    return AmazonSettings(
        AMAZON_DATA_SOURCE=AmazonDataSource.SPAPI,
        AMAZON_MARKETPLACE_ID="ATVPDKIKX0DER",
        SP_API_CLIENT_ID="test-id",
        SP_API_CLIENT_SECRET="test-secret",
        SP_API_REFRESH_TOKEN="test-refresh",
        AMAZON_FALLBACK_ENABLED=True,
    )


@pytest.fixture
def settings_no_fallback() -> AmazonSettings:
    return AmazonSettings(
        AMAZON_DATA_SOURCE=AmazonDataSource.SPAPI,
        AMAZON_MARKETPLACE_ID="ATVPDKIKX0DER",
        SP_API_CLIENT_ID="test-id",
        SP_API_CLIENT_SECRET="test-secret",
        SP_API_REFRESH_TOKEN="test-refresh",
        AMAZON_FALLBACK_ENABLED=False,
    )


class TestIsFallbackError:
    def test_connection_error(self) -> None:
        assert _is_fallback_error(requests.exceptions.ConnectionError())

    def test_timeout(self) -> None:
        assert _is_fallback_error(requests.exceptions.Timeout())

    def test_http_error(self) -> None:
        assert _is_fallback_error(requests.exceptions.HTTPError())

    def test_credential_error(self) -> None:
        assert _is_fallback_error(AmazonCredentialError("test"))

    def test_key_error_not_fallback(self) -> None:
        assert not _is_fallback_error(KeyError("not found"))

    def test_value_error_not_fallback(self) -> None:
        assert not _is_fallback_error(ValueError("bad value"))


class TestFallbackWrapper:
    def test_primary_success(self, settings: AmazonSettings) -> None:
        primary = MagicMock()
        primary.data_source = "spapi"
        primary.get_listing.return_value = "spapi-result"
        fallback = MagicMock()
        fallback.data_source = "mock"

        wrapper = FallbackWrapper(primary, fallback)
        result = wrapper.get_listing("SKU-1")

        assert result == "spapi-result"
        assert wrapper.data_source == "spapi"
        primary.get_listing.assert_called_once()
        fallback.get_listing.assert_not_called()

    def test_primary_failure_falls_back(self) -> None:
        primary = MagicMock()
        primary.data_source = "spapi"
        primary.get_listing.side_effect = requests.exceptions.ConnectionError("fail")
        fallback = MagicMock()
        fallback.data_source = "mock"
        fallback.get_listing.return_value = "mock-result"

        wrapper = FallbackWrapper(primary, fallback, max_retries=1, backoff_base=0.01)
        result = wrapper.get_listing("SKU-1")

        assert result == "mock-result"
        assert wrapper.data_source == "spapi-degraded"
        assert primary.get_listing.call_count == 2
        fallback.get_listing.assert_called_once()

    def test_retry_then_succeeds(self) -> None:
        primary = MagicMock()
        primary.data_source = "spapi"
        primary.get_listing.side_effect = [
            requests.exceptions.HTTPError("500"),
            requests.exceptions.HTTPError("500"),
            "spapi-result",
        ]
        fallback = MagicMock()

        wrapper = FallbackWrapper(primary, fallback, max_retries=2, backoff_base=0.01)
        result = wrapper.get_listing("SKU-1")

        assert result == "spapi-result"
        assert wrapper.data_source == "spapi"
        assert primary.get_listing.call_count == 3
        fallback.get_listing.assert_not_called()

    def test_key_error_not_caught(self) -> None:
        primary = MagicMock()
        primary.get_listing.side_effect = KeyError("not found")
        fallback = MagicMock()

        wrapper = FallbackWrapper(primary, fallback, max_retries=2, backoff_base=0.01)

        with pytest.raises(KeyError, match="not found"):
            wrapper.get_listing("SKU-1")

        fallback.get_listing.assert_not_called()

    def test_value_error_not_caught(self) -> None:
        primary = MagicMock()
        primary.get_listing.side_effect = ValueError("bad")
        fallback = MagicMock()

        wrapper = FallbackWrapper(primary, fallback)

        with pytest.raises(ValueError, match="bad"):
            wrapper.get_listing("SKU-1")

        fallback.get_listing.assert_not_called()

    def test_credential_error_falls_back(self) -> None:
        primary = MagicMock()
        primary.get_listing.side_effect = AmazonCredentialError("no token")
        fallback = MagicMock()
        fallback.get_listing.return_value = "mock-result"

        wrapper = FallbackWrapper(primary, fallback, max_retries=0, backoff_base=0.01)
        result = wrapper.get_listing("SKU-1")

        assert result == "mock-result"
        assert wrapper.data_source == "spapi-degraded"

    def test_recovery_from_degradation(self) -> None:
        primary = MagicMock()
        primary.get_listing.side_effect = [
            requests.exceptions.ConnectionError("fail"),
            "recovered-result",
        ]
        fallback = MagicMock()
        fallback.get_listing.return_value = "mock-result"

        wrapper = FallbackWrapper(primary, fallback, max_retries=0, backoff_base=0.01)

        result1 = wrapper.get_listing("SKU-1")
        assert result1 == "mock-result"
        assert wrapper.data_source == "spapi-degraded"

        result2 = wrapper.get_listing("SKU-2")
        assert result2 == "recovered-result"
        assert wrapper.data_source == "spapi"

    def test_degradation_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        primary = MagicMock()
        primary.get_listing.side_effect = requests.exceptions.ConnectionError("fail")
        fallback = MagicMock()
        fallback.get_listing.return_value = "mock-result"

        wrapper = FallbackWrapper(primary, fallback, max_retries=0, backoff_base=0.01)

        with caplog.at_level(logging.WARNING, logger="aeo_integrations.amazon.fallback"):
            wrapper.get_listing("SKU-1")

        assert any("falling back to mock" in record.message for record in caplog.records)


class TestFactoryWithFallback:
    def test_listings_factory_returns_wrapper(self, settings: AmazonSettings) -> None:
        from aeo_integrations.amazon.listings import get_listings_client

        with patch("aeo_integrations.amazon.listings.SpApiListingsAdapter"):
            client = get_listings_client(settings)
        assert isinstance(client, FallbackWrapper)
        assert client.data_source == "spapi"

    def test_listings_factory_no_fallback(self, settings_no_fallback: AmazonSettings) -> None:
        from aeo_integrations.amazon.listings import get_listings_client
        from aeo_integrations.amazon.spapi_adapter import SpApiListingsAdapter

        with patch.object(SpApiListingsAdapter, "__init__", return_value=None):
            client = get_listings_client(settings_no_fallback)
        assert isinstance(client, SpApiListingsAdapter)

    def test_orders_factory_returns_wrapper(self, settings: AmazonSettings) -> None:
        from aeo_integrations.amazon.orders import get_orders_client

        with patch("aeo_integrations.amazon.orders.SpApiOrdersAdapter"):
            client = get_orders_client(settings)
        assert isinstance(client, FallbackWrapper)

    def test_advertising_factory_returns_wrapper(self, settings: AmazonSettings) -> None:
        from aeo_integrations.amazon.advertising import get_advertising_client

        with patch("aeo_integrations.amazon.advertising.SpApiAdvertisingAdapter"):
            client = get_advertising_client(settings)
        assert isinstance(client, FallbackWrapper)

    def test_inventory_factory_returns_wrapper(self, settings: AmazonSettings) -> None:
        from aeo_integrations.amazon.inventory import get_inventory_client

        with patch("aeo_integrations.amazon.inventory.SpApiInventoryAdapter"):
            client = get_inventory_client(settings)
        assert isinstance(client, FallbackWrapper)

    def test_mock_mode_no_wrapper(self) -> None:
        from aeo_integrations.amazon.listings import MockListingsAdapter, get_listings_client

        mock_settings = AmazonSettings(AMAZON_DATA_SOURCE=AmazonDataSource.MOCK)
        client = get_listings_client(mock_settings)
        assert isinstance(client, MockListingsAdapter)
        assert client.data_source == "mock"


class TestDataSourceProperty:
    def test_spapi_adapter_data_source(self) -> None:
        from aeo_integrations.amazon.spapi_adapter import SpApiListingsAdapter

        settings = AmazonSettings(
            AMAZON_DATA_SOURCE=AmazonDataSource.SPAPI,
            SP_API_CLIENT_ID="id",
            SP_API_CLIENT_SECRET="secret",
            SP_API_REFRESH_TOKEN="token",
        )
        adapter = SpApiListingsAdapter(settings)
        assert adapter.data_source == "spapi"

    def test_mock_adapter_data_source(self) -> None:
        from aeo_integrations.amazon.listings import MockListingsAdapter

        adapter = MockListingsAdapter()
        assert adapter.data_source == "mock"
