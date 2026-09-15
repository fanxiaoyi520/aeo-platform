"""Tests for P6-17: SpApiListingsAdapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from aeo_integrations.amazon.config import AmazonDataSource, AmazonSettings
from aeo_integrations.amazon.spapi_adapter import SpApiListingsAdapter


@pytest.fixture
def settings() -> AmazonSettings:
    return AmazonSettings(
        AMAZON_DATA_SOURCE=AmazonDataSource.SPAPI,
        AMAZON_MARKETPLACE_ID="ATVPDKIKX0DER",
        SP_API_CLIENT_ID="test-id",
        SP_API_CLIENT_SECRET="test-secret",
        SP_API_REFRESH_TOKEN="test-refresh",
    )


def test_get_listing_success(settings: AmazonSettings) -> None:
    adapter = SpApiListingsAdapter(settings)
    mock_response = MagicMock()
    mock_response.payload = {
        "items": [
            {
                "asin": "B001234567",
                "summaries": [
                    {
                        "itemName": "Test Product",
                        "brand": "TestBrand",
                        "listPrice": {"Amount": "29.99", "CurrencyCode": "USD"},
                    }
                ],
                "identifiers": [
                    {
                        "identifier": {"skuIdentifier": "TEST-SKU-001"},
                    }
                ],
            }
        ]
    }

    with patch.object(adapter, "_get_client") as mock_client:
        client = MagicMock()
        client.search_catalog_items.return_value = mock_response
        mock_client.return_value = client

        listing = adapter.get_listing("TEST-SKU-001")

    assert listing.sku == "TEST-SKU-001"
    assert listing.asin == "B001234567"
    assert listing.title == "Test Product"
    assert listing.brand == "TestBrand"
    assert listing.price is not None
    assert str(listing.price) == "29.99"


def test_get_listing_not_found(settings: AmazonSettings) -> None:
    adapter = SpApiListingsAdapter(settings)
    mock_response = MagicMock()
    mock_response.payload = {"items": []}

    with patch.object(adapter, "_get_client") as mock_client:
        client = MagicMock()
        client.search_catalog_items.return_value = mock_response
        mock_client.return_value = client

        with pytest.raises(KeyError, match="UNKNOWN-SKU"):
            adapter.get_listing("UNKNOWN-SKU")


def test_list_listings_success(settings: AmazonSettings) -> None:
    adapter = SpApiListingsAdapter(settings)
    mock_response = MagicMock()
    mock_response.payload = {
        "items": [
            {
                "asin": "B001",
                "summaries": [{"itemName": "Product 1", "brand": "Brand1"}],
                "identifiers": [{"identifier": {"skuIdentifier": "SKU-1"}}],
            },
            {
                "asin": "B002",
                "summaries": [{"itemName": "Product 2", "brand": "Brand2"}],
                "identifiers": [{"identifier": {"skuIdentifier": "SKU-2"}}],
            },
        ]
    }

    with patch.object(adapter, "_get_client") as mock_client:
        client = MagicMock()
        client.search_catalog_items.return_value = mock_response
        mock_client.return_value = client

        listings = adapter.list_listings(limit=10)

    assert len(listings) == 2
    assert listings[0].sku == "SKU-1"
    assert listings[1].sku == "SKU-2"
