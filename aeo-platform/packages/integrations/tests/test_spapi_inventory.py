"""Tests for P6-20: SpApiInventoryAdapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from aeo_integrations.amazon.config import AmazonDataSource, AmazonSettings
from aeo_integrations.amazon.spapi_adapter import SpApiInventoryAdapter


@pytest.fixture
def settings() -> AmazonSettings:
    return AmazonSettings(
        AMAZON_DATA_SOURCE=AmazonDataSource.SPAPI,
        AMAZON_MARKETPLACE_ID="ATVPDKIKX0DER",
        SP_API_CLIENT_ID="test-id",
        SP_API_CLIENT_SECRET="test-secret",
        SP_API_REFRESH_TOKEN="test-refresh",
    )


def test_get_inventory_success(settings: AmazonSettings) -> None:
    adapter = SpApiInventoryAdapter(settings)
    mock_response = MagicMock()
    mock_response.payload = {
        "inventorySummaries": [
            {
                "sellerSku": "TEST-SKU-001",
                "fnSku": "FN-001",
                "inventoryDetails": {
                    "totalQuantity": {
                        "availableQuantity": 100,
                        "inboundWorkingQuantity": 20,
                        "reservedQuantity": 5,
                    }
                },
                "lastUpdatedTime": "2026-09-15T00:00:00Z",
            }
        ]
    }

    with patch.object(adapter, "_get_client") as mock_client:
        client = MagicMock()
        client.get_inventory_summary_marketplace.return_value = mock_response
        mock_client.return_value = client

        item = adapter.get_inventory("TEST-SKU-001")

    assert item.sku == "TEST-SKU-001"
    assert item.available_quantity == 100
    assert item.inbound_quantity == 20
    assert item.reserved_quantity == 5
    assert item.fulfillment_channel == "AFN"


def test_get_inventory_not_found(settings: AmazonSettings) -> None:
    adapter = SpApiInventoryAdapter(settings)
    mock_response = MagicMock()
    mock_response.payload = {"inventorySummaries": []}

    with patch.object(adapter, "_get_client") as mock_client:
        client = MagicMock()
        client.get_inventory_summary_marketplace.return_value = mock_response
        mock_client.return_value = client

        with pytest.raises(KeyError, match="UNKNOWN-SKU"):
            adapter.get_inventory("UNKNOWN-SKU")


def test_list_inventory_success(settings: AmazonSettings) -> None:
    adapter = SpApiInventoryAdapter(settings)
    mock_response = MagicMock()
    mock_response.payload = {
        "inventorySummaries": [
            {
                "sellerSku": "SKU-1",
                "fnSku": "FN-1",
                "inventoryDetails": {
                    "totalQuantity": {
                        "availableQuantity": 50,
                        "inboundWorkingQuantity": 0,
                        "reservedQuantity": 0,
                    }
                },
                "lastUpdatedTime": "2026-09-15T00:00:00Z",
            },
            {
                "sellerSku": "SKU-2",
                "fnSku": "FN-2",
                "inventoryDetails": {
                    "totalQuantity": {
                        "availableQuantity": 30,
                        "inboundWorkingQuantity": 10,
                        "reservedQuantity": 2,
                    }
                },
                "lastUpdatedTime": "2026-09-15T00:00:00Z",
            },
        ]
    }

    with patch.object(adapter, "_get_client") as mock_client:
        client = MagicMock()
        client.get_inventory_summary_marketplace.return_value = mock_response
        mock_client.return_value = client

        items = adapter.list_inventory(limit=10)

    assert len(items) == 2
    assert items[0].sku == "SKU-1"
    assert items[0].available_quantity == 50
    assert items[1].sku == "SKU-2"
    assert items[1].inbound_quantity == 10


def test_list_inventory_filter_by_fulfillment(settings: AmazonSettings) -> None:
    adapter = SpApiInventoryAdapter(settings)
    mock_response = MagicMock()
    mock_response.payload = {
        "inventorySummaries": [
            {
                "sellerSku": "SKU-1",
                "fnSku": "FN-1",
                "inventoryDetails": {
                    "totalQuantity": {
                        "availableQuantity": 50,
                        "inboundWorkingQuantity": 0,
                        "reservedQuantity": 0,
                    }
                },
                "lastUpdatedTime": "2026-09-15T00:00:00Z",
            }
        ]
    }

    with patch.object(adapter, "_get_client") as mock_client:
        client = MagicMock()
        client.get_inventory_summary_marketplace.return_value = mock_response
        mock_client.return_value = client

        items = adapter.list_inventory(fulfillment_channel="MFN", limit=10)

    assert len(items) == 0
