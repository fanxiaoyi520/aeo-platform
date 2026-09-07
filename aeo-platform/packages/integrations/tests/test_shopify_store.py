"""Tests for MV3-06: Shopify Store API read-only integration."""

from __future__ import annotations

from decimal import Decimal

import pytest


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
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        assert client is not None

    def test_list_products(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        products = client.list_products()
        assert len(products) >= 1
        assert all(hasattr(p, "product_id") for p in products)

    def test_list_products_with_limit(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        products = client.list_products(limit=2)
        assert len(products) <= 2

    def test_list_products_filter_status(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        active = client.list_products(status="active")
        assert all(p.status == "active" for p in active)

    def test_list_orders(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        orders = client.list_orders()
        assert len(orders) >= 1
        assert all(hasattr(o, "order_id") for o in orders)

    def test_list_orders_with_limit(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        orders = client.list_orders(limit=1)
        assert len(orders) <= 1

    def test_list_inventory(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        inventory = client.list_inventory()
        assert len(inventory) >= 1
        assert all(hasattr(i, "sku") for i in inventory)


class TestShopifyApiAdapter:
    def test_adapter_raises_not_implemented(self) -> None:
        from aeo_integrations.shopify.shopify_adapter import ShopifyApiAdapter

        adapter = ShopifyApiAdapter(store_url="test.myshopify.com", access_token="tok")
        with pytest.raises(NotImplementedError):
            adapter.list_products()

    def test_adapter_list_orders_raises(self) -> None:
        from aeo_integrations.shopify.shopify_adapter import ShopifyApiAdapter

        adapter = ShopifyApiAdapter(store_url="test.myshopify.com", access_token="tok")
        with pytest.raises(NotImplementedError):
            adapter.list_orders()

    def test_adapter_list_inventory_raises(self) -> None:
        from aeo_integrations.shopify.shopify_adapter import ShopifyApiAdapter

        adapter = ShopifyApiAdapter(store_url="test.myshopify.com", access_token="tok")
        with pytest.raises(NotImplementedError):
            adapter.list_inventory()


class TestShopifyMockDataIntegrity:
    def test_product_fields_complete(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        products = client.list_products()
        for p in products:
            assert p.product_id
            assert p.title
            assert p.sku

    def test_order_fields_complete(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        orders = client.list_orders()
        for o in orders:
            assert o.order_id
            assert o.total_price is not None

    def test_inventory_fields_complete(self) -> None:
        from aeo_integrations.shopify.store import get_store_client

        client = get_store_client()
        items = client.list_inventory()
        for i in items:
            assert i.sku
            assert i.available >= 0
