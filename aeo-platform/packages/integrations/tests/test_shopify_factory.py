"""Tests for Shopify factory and fallback integration."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from aeo_integrations.amazon.fallback import FallbackWrapper
from aeo_integrations.shopify import store as store_mod
from aeo_integrations.shopify.config import ShopifySettings
from aeo_integrations.shopify.store import MockStoreAdapter, get_store_client


@pytest.fixture(autouse=True)
def _reset_client() -> Generator[None, None, None]:
    store_mod._client = None
    yield
    store_mod._client = None


class TestShopifyFactory:
    def test_mock_by_default(self) -> None:
        client = get_store_client()
        assert isinstance(client, MockStoreAdapter)
        assert client.data_source == "mock"

    def test_mock_explicit(self) -> None:
        settings = ShopifySettings(SHOPIFY_DATA_SOURCE="mock")  # type: ignore[arg-type]
        client = get_store_client(settings)
        assert isinstance(client, MockStoreAdapter)

    def test_shopify_no_fallback(self) -> None:
        settings = ShopifySettings(
            SHOPIFY_DATA_SOURCE="shopify",  # type: ignore[arg-type]
            SHOPIFY_STORE_URL="https://test.myshopify.com",
            SHOPIFY_ACCESS_TOKEN="tok",
            SHOPIFY_FALLBACK_ENABLED="false",  # type: ignore[arg-type]
        )
        mock_adapter = MagicMock()
        mock_adapter.data_source = "shopify"
        with patch(
            "aeo_integrations.shopify.shopify_adapter.ShopifyApiAdapter", return_value=mock_adapter
        ):
            client = get_store_client(settings)
        assert not isinstance(client, FallbackWrapper)
        assert not isinstance(client, MockStoreAdapter)

    def test_shopify_with_fallback(self) -> None:
        settings = ShopifySettings(
            SHOPIFY_DATA_SOURCE="shopify",  # type: ignore[arg-type]
            SHOPIFY_STORE_URL="https://test.myshopify.com",
            SHOPIFY_ACCESS_TOKEN="tok",
            SHOPIFY_FALLBACK_ENABLED="true",  # type: ignore[arg-type]
        )
        mock_adapter = MagicMock()
        mock_adapter.data_source = "shopify"
        with patch(
            "aeo_integrations.shopify.shopify_adapter.ShopifyApiAdapter", return_value=mock_adapter
        ):
            client = get_store_client(settings)
        assert isinstance(client, FallbackWrapper)
        assert client.data_source == "shopify"

    def test_singleton(self) -> None:
        c1 = get_store_client()
        c2 = get_store_client()
        assert c1 is c2
