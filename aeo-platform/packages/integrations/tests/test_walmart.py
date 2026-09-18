"""P7-12: Tests for Walmart Marketplace integration."""

from __future__ import annotations

import pytest
from aeo_integrations.walmart import WalmartMarketplaceClient


class TestWalmartMarketplaceClient:
    def test_client_initialization_mock_mode(self) -> None:
        client = WalmartMarketplaceClient()
        assert client._use_mock is True
        assert client.data_source == "mock"

    def test_client_initialization_with_credentials(self) -> None:
        client = WalmartMarketplaceClient(client_id="test_id", client_secret="test_secret")
        assert client._use_mock is False
        assert client.data_source == "api"

    def test_list_orders_mock(self) -> None:
        client = WalmartMarketplaceClient()
        orders = client.list_orders()

        assert len(orders) == 3
        assert orders[0].purchase_order_id == "WM-001"
        assert orders[0].order_status == "Shipped"
        assert orders[0].customer_name == "John Doe"
        assert len(orders[0].order_lines) == 1
        assert orders[0].order_lines[0].sku == "WM-SKU-A"

    def test_list_orders_with_status_filter(self) -> None:
        client = WalmartMarketplaceClient()
        orders = client.list_orders(status="Created")

        assert len(orders) == 1
        assert orders[0].order_status == "Created"

    def test_list_orders_with_limit(self) -> None:
        client = WalmartMarketplaceClient()
        orders = client.list_orders(limit=2)

        assert len(orders) == 2

    def test_get_order_mock(self) -> None:
        client = WalmartMarketplaceClient()
        order = client.get_order("WM-001")

        assert order.purchase_order_id == "WM-001"
        assert order.order_status == "Shipped"

    def test_get_order_not_found(self) -> None:
        client = WalmartMarketplaceClient()

        with pytest.raises(KeyError, match="Order not found"):
            client.get_order("NONEXISTENT")

    def test_list_items_mock(self) -> None:
        client = WalmartMarketplaceClient()
        items = client.list_items()

        assert len(items) == 2
        assert items[0].sku == "WM-SKU-A"
        assert items[0].product_name == "Wireless Mouse Pro"
        assert items[0].price == "24.99"
        assert items[0].stock == 150

    def test_list_items_with_status_filter(self) -> None:
        client = WalmartMarketplaceClient()
        items = client.list_items(status="ACTIVE")

        assert len(items) == 2
        assert all(i.status == "ACTIVE" for i in items)

    def test_get_item_mock(self) -> None:
        client = WalmartMarketplaceClient()
        item = client.get_item("WM-SKU-A")

        assert item.sku == "WM-SKU-A"
        assert item.product_name == "Wireless Mouse Pro"

    def test_get_item_not_found(self) -> None:
        client = WalmartMarketplaceClient()

        with pytest.raises(KeyError, match="Item not found"):
            client.get_item("NONEXISTENT")

    def test_api_methods_raise_not_implemented(self) -> None:
        client = WalmartMarketplaceClient(client_id="id", client_secret="secret")

        with pytest.raises(NotImplementedError):
            client._api_list_orders(status=None, limit=20)

        with pytest.raises(NotImplementedError):
            client._api_get_order("WM-001")

        with pytest.raises(NotImplementedError):
            client._api_list_items(status=None, limit=20)

        with pytest.raises(NotImplementedError):
            client._api_get_item("WM-SKU-A")
