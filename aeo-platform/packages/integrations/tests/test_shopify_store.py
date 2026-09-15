"""Tests for Shopify Store API integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aeo_integrations.shopify.shopify_adapter import ShopifyApiAdapter

from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestShopifyModels:
    def test_shopify_product_model(self) -> None:
        from aeo_integrations.shopify.models import ShopifyProduct

        product = ShopifyProduct(
            product_id="P-001",
            title="Electric Kettle",
            handle="electric-kettle",
            status="active",
            vendor="HomeBrew",
            price=Decimal("29.99"),
            compare_at_price=Decimal("39.99"),
            sku="KETTLE-001",
            inventory_quantity=50,
        )
        assert product.product_id == "P-001"
        assert product.price == Decimal("29.99")
        assert product.inventory_quantity == 50

    def test_shopify_order_model(self) -> None:
        from aeo_integrations.shopify.models import ShopifyOrder

        order = ShopifyOrder(
            order_id="ORD-001",
            order_number=1001,
            financial_status="paid",
            fulfillment_status="fulfilled",
            total_price=Decimal("59.98"),
            currency="USD",
            line_items=[
                {"sku": "KETTLE-001", "quantity": 2, "price": Decimal("29.99")},
            ],
        )
        assert order.order_id == "ORD-001"
        assert order.total_price == Decimal("59.98")
        assert len(order.line_items) == 1

    def test_shopify_inventory_model(self) -> None:
        from aeo_integrations.shopify.models import ShopifyInventoryItem

        item = ShopifyInventoryItem(
            sku="KETTLE-001",
            location_id="LOC-001",
            available=50,
            reserved=5,
        )
        assert item.sku == "KETTLE-001"
        assert item.available == 50


class TestShopifyStoreClient:
    def test_get_store_client_returns_mock(self) -> None:
        from aeo_integrations.shopify import store as store_mod

        store_mod._client = None
        client = store_mod.get_store_client()
        assert client is not None

    def test_list_products(self) -> None:
        from aeo_integrations.shopify import store as store_mod

        store_mod._client = None
        client = store_mod.get_store_client()
        products = client.list_products()
        assert len(products) >= 1
        assert all(hasattr(p, "product_id") for p in products)

    def test_list_products_with_limit(self) -> None:
        from aeo_integrations.shopify import store as store_mod

        store_mod._client = None
        client = store_mod.get_store_client()
        products = client.list_products(limit=2)
        assert len(products) <= 2

    def test_list_products_filter_status(self) -> None:
        from aeo_integrations.shopify import store as store_mod

        store_mod._client = None
        client = store_mod.get_store_client()
        active = client.list_products(status="active")
        assert all(p.status == "active" for p in active)

    def test_list_orders(self) -> None:
        from aeo_integrations.shopify import store as store_mod

        store_mod._client = None
        client = store_mod.get_store_client()
        orders = client.list_orders()
        assert len(orders) >= 1
        assert all(hasattr(o, "order_id") for o in orders)

    def test_list_orders_with_limit(self) -> None:
        from aeo_integrations.shopify import store as store_mod

        store_mod._client = None
        client = store_mod.get_store_client()
        orders = client.list_orders(limit=1)
        assert len(orders) <= 1

    def test_list_inventory(self) -> None:
        from aeo_integrations.shopify import store as store_mod

        store_mod._client = None
        client = store_mod.get_store_client()
        inventory = client.list_inventory()
        assert len(inventory) >= 1
        assert all(hasattr(i, "sku") for i in inventory)


class TestShopifyApiAdapter:
    def _make_adapter(self) -> ShopifyApiAdapter:
        from aeo_integrations.shopify.config import ShopifySettings
        from aeo_integrations.shopify.shopify_adapter import ShopifyApiAdapter

        settings = ShopifySettings(
            SHOPIFY_STORE_URL="https://test.myshopify.com",
            SHOPIFY_ACCESS_TOKEN="test-token",
        )
        return ShopifyApiAdapter(settings)

    def _mock_response(self, json_data: dict[str, Any]) -> MagicMock:
        resp = MagicMock()
        resp.json.return_value = json_data
        resp.raise_for_status.return_value = None
        return resp

    def test_list_products_calls_api(self) -> None:
        adapter = self._make_adapter()
        mock_resp = self._mock_response(
            {
                "products": [
                    {
                        "id": 1,
                        "title": "Widget",
                        "handle": "widget",
                        "status": "active",
                        "vendor": "ACME",
                        "product_type": "gadget",
                        "variants": [{"price": "10.00", "sku": "W1"}],
                    },
                ]
            }
        )
        with patch("aeo_integrations.shopify.shopify_adapter.requests.get", return_value=mock_resp):
            products = adapter.list_products()
        assert len(products) == 1
        assert products[0].title == "Widget"

    def test_list_orders_calls_api(self) -> None:
        adapter = self._make_adapter()
        mock_resp = self._mock_response(
            {
                "orders": [
                    {
                        "id": 100,
                        "order_number": 1,
                        "financial_status": "paid",
                        "fulfillment_status": "unfulfilled",
                        "total_price": "59.98",
                        "currency": "USD",
                    },
                ]
            }
        )
        with patch("aeo_integrations.shopify.shopify_adapter.requests.get", return_value=mock_resp):
            orders = adapter.list_orders()
        assert len(orders) == 1
        assert orders[0].order_id == "100"

    def test_list_customers_calls_api(self) -> None:
        adapter = self._make_adapter()
        mock_resp = self._mock_response(
            {
                "customers": [
                    {"id": 42, "email": "test@example.com", "first_name": "A", "last_name": "B"},
                ]
            }
        )
        with patch("aeo_integrations.shopify.shopify_adapter.requests.get", return_value=mock_resp):
            customers = adapter.list_customers()
        assert len(customers) == 1
        assert customers[0].email == "test@example.com"

    def test_data_source(self) -> None:
        adapter = self._make_adapter()
        assert adapter.data_source == "shopify"


class TestShopifyMockDataIntegrity:
    def test_product_fields_complete(self) -> None:
        from aeo_integrations.shopify import store as store_mod

        store_mod._client = None
        client = store_mod.get_store_client()
        products = client.list_products()
        for p in products:
            assert p.product_id
            assert p.title
            assert p.sku

    def test_order_fields_complete(self) -> None:
        from aeo_integrations.shopify import store as store_mod

        store_mod._client = None
        client = store_mod.get_store_client()
        orders = client.list_orders()
        for o in orders:
            assert o.order_id
            assert o.total_price is not None

    def test_inventory_fields_complete(self) -> None:
        from aeo_integrations.shopify import store as store_mod

        store_mod._client = None
        client = store_mod.get_store_client()
        items = client.list_inventory()
        for i in items:
            assert i.sku
            assert i.available >= 0
