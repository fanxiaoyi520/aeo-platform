"""Tests for P6-18: SpApiOrdersAdapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from aeo_integrations.amazon.config import AmazonDataSource, AmazonSettings
from aeo_integrations.amazon.spapi_adapter import SpApiOrdersAdapter


@pytest.fixture
def settings() -> AmazonSettings:
    return AmazonSettings(
        AMAZON_DATA_SOURCE=AmazonDataSource.SPAPI,
        AMAZON_MARKETPLACE_ID="ATVPDKIKX0DER",
        SP_API_CLIENT_ID="test-id",
        SP_API_CLIENT_SECRET="test-secret",
        SP_API_REFRESH_TOKEN="test-refresh",
    )


def test_list_orders_success(settings: AmazonSettings) -> None:
    adapter = SpApiOrdersAdapter(settings)

    orders_response = MagicMock()
    orders_response.payload = {
        "Orders": [
            {
                "AmazonOrderId": "111-1234567-1234567",
                "OrderStatus": "Shipped",
                "PurchaseDate": "2026-09-01T10:00:00Z",
            }
        ]
    }

    items_response = MagicMock()
    items_response.payload = {
        "OrderItems": [
            {
                "SellerSKU": "TEST-SKU-001",
                "QuantityOrdered": 2,
                "ItemPrice": {"Amount": "29.99", "CurrencyCode": "USD"},
            }
        ]
    }

    with patch.object(adapter, "_get_client") as mock_client:
        client = MagicMock()
        client.get_orders.return_value = orders_response
        client.get_order_items.return_value = items_response
        mock_client.return_value = client

        orders = adapter.list_orders(limit=10)

    assert len(orders) == 1
    assert orders[0].order_id == "111-1234567-1234567"
    assert orders[0].sku == "TEST-SKU-001"
    assert orders[0].quantity == 2
    assert orders[0].order_status == "Shipped"


def test_list_orders_filter_by_sku(settings: AmazonSettings) -> None:
    adapter = SpApiOrdersAdapter(settings)

    orders_response = MagicMock()
    orders_response.payload = {
        "Orders": [
            {
                "AmazonOrderId": "111-1234567-1234567",
                "OrderStatus": "Shipped",
                "PurchaseDate": "2026-09-01T10:00:00Z",
            }
        ]
    }

    items_response = MagicMock()
    items_response.payload = {
        "OrderItems": [
            {"SellerSKU": "SKU-A", "QuantityOrdered": 1, "ItemPrice": None},
            {"SellerSKU": "SKU-B", "QuantityOrdered": 3, "ItemPrice": None},
        ]
    }

    with patch.object(adapter, "_get_client") as mock_client:
        client = MagicMock()
        client.get_orders.return_value = orders_response
        client.get_order_items.return_value = items_response
        mock_client.return_value = client

        orders = adapter.list_orders(sku="SKU-B", limit=10)

    assert len(orders) == 1
    assert orders[0].sku == "SKU-B"
    assert orders[0].quantity == 3


def test_list_orders_handles_item_fetch_failure(settings: AmazonSettings) -> None:
    adapter = SpApiOrdersAdapter(settings)

    orders_response = MagicMock()
    orders_response.payload = {
        "Orders": [
            {
                "AmazonOrderId": "111-FAIL",
                "OrderStatus": "Pending",
                "PurchaseDate": "2026-09-01T10:00:00Z",
            }
        ]
    }

    with patch.object(adapter, "_get_client") as mock_client:
        client = MagicMock()
        client.get_orders.return_value = orders_response
        client.get_order_items.side_effect = Exception("API error")
        mock_client.return_value = client

        orders = adapter.list_orders(limit=10)

    assert len(orders) == 0
