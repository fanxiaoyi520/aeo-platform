"""P7-14: Tests for unified platform adapter interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from aeo_shared.order_ingest import OrderIngestService
from aeo_shared.platform_adapter import (
    PlatformAdapter,
    PlatformRegistry,
    build_amazon_adapter,
    build_shopify_adapter,
)


@dataclass
class FakeAmazonItem:
    order_id: str
    sku: str
    quantity: int = 1
    item_price: str | None = "9.99"
    currency: str = "USD"
    order_status: str = "Shipped"
    purchase_date: str = "2026-09-15T10:00:00Z"
    tracking_number: str = ""
    carrier: str = ""
    ship_date: str = ""
    delivery_date: str = ""
    return_status: str = "none"


class FakeAmazonOrders:
    data_source = "mock"

    def list_orders(
        self, *, sku: str | None = None, limit: int = 20
    ) -> list[Any]:
        items = [
            FakeAmazonItem(order_id="AMZ-1", sku="SKU-A"),
            FakeAmazonItem(order_id="AMZ-2", sku="SKU-B"),
        ]
        if sku:
            items = [i for i in items if i.sku == sku]
        return items[:limit]


class FakeAmazonListings:
    data_source = "mock"

    def list_items(self, **kwargs: Any) -> list[Any]:
        return [{"sku": "SKU-A"}, {"sku": "SKU-B"}]


class FakeAmazonAds:
    data_source = "mock"

    def list_campaigns(self, **kwargs: Any) -> list[Any]:
        return [{"campaign_id": "C1"}]


@dataclass
class FakeShopifyOrder:
    order_id: str
    order_number: int = 1001
    financial_status: str = "paid"
    fulfillment_status: str = "fulfilled"
    total_price: str | None = "19.99"
    line_items: list[dict[str, Any]] | None = None
    created_at: str = "2026-09-15T09:00:00Z"
    currency: str = "USD"


class FakeShopifyStore:
    data_source = "mock"

    def list_orders(
        self, *, financial_status: str | None = None, limit: int = 50
    ) -> list[Any]:
        items = [
            FakeShopifyOrder(
                order_id="SH-1",
                line_items=[{"sku": "SKU-C", "quantity": 1, "price": "19.99"}],
            ),
        ]
        if financial_status:
            items = [o for o in items if o.financial_status == financial_status]
        return items[:limit]

    def list_items(self, **kwargs: Any) -> list[Any]:
        return [{"sku": "SKU-C"}]


class TestPlatformAdapter:
    def test_adapter_exposes_platform_name(self) -> None:
        adapter = PlatformAdapter(platform_name="amazon")
        assert adapter.platform_name == "amazon"
        assert adapter.has_orders() is False
        assert adapter.has_listings() is False
        assert adapter.has_advertising() is False

    def test_adapter_with_clients(self) -> None:
        adapter = PlatformAdapter(
            platform_name="amazon",
            orders=FakeAmazonOrders(),
            listings=FakeAmazonListings(),
            advertising=FakeAmazonAds(),
        )
        assert adapter.has_orders() is True
        assert adapter.has_listings() is True
        assert adapter.has_advertising() is True
        assert adapter.data_source == "mock"

    def test_data_source_defaults_to_mock(self) -> None:
        class NoDataSource:
            def list_orders(self, **kwargs: Any) -> list[Any]:
                return []

        adapter = PlatformAdapter(
            platform_name="custom", orders=NoDataSource()
        )
        assert adapter.data_source == "mock"


class TestPlatformRegistry:
    def test_register_and_get(self) -> None:
        registry = PlatformRegistry()
        adapter = PlatformAdapter(platform_name="amazon")
        registry.register(adapter)
        assert registry.get("amazon") is adapter
        assert registry.list_platforms() == ["amazon"]

    def test_get_unknown_raises(self) -> None:
        registry = PlatformRegistry()
        with pytest.raises(KeyError, match="Unknown platform"):
            registry.get("walmart")

    def test_all_returns_sorted(self) -> None:
        registry = PlatformRegistry()
        registry.register(PlatformAdapter(platform_name="shopify"))
        registry.register(PlatformAdapter(platform_name="amazon"))
        names = [a.platform_name for a in registry.all()]
        assert names == ["amazon", "shopify"]


class TestIngestPlatform:
    def test_ingest_amazon_via_adapter(self) -> None:
        adapter = PlatformAdapter(
            platform_name="amazon", orders=FakeAmazonOrders()
        )
        service = OrderIngestService()
        records = service.ingest_platform(adapter)
        assert len(records) == 2
        assert all(r.platform == "amazon" for r in records)
        assert records[0].external_order_id == "AMZ-1"

    def test_ingest_shopify_via_adapter(self) -> None:
        adapter = PlatformAdapter(
            platform_name="shopify", orders=FakeShopifyStore()
        )
        service = OrderIngestService()
        records = service.ingest_platform(adapter)
        assert len(records) == 1
        assert records[0].platform == "shopify"
        assert records[0].sku == "SKU-C"

    def test_ingest_platform_unsupported_raises(self) -> None:
        adapter = PlatformAdapter(
            platform_name="newegg", orders=FakeAmazonOrders()
        )
        service = OrderIngestService()
        with pytest.raises(ValueError, match="Unsupported platform"):
            service.ingest_platform(adapter)

    def test_ingest_platform_no_orders_returns_empty(self) -> None:
        adapter = PlatformAdapter(platform_name="amazon")
        service = OrderIngestService()
        assert service.ingest_platform(adapter) == []

    def test_ingest_platform_requires_platform_name(self) -> None:
        service = OrderIngestService()
        with pytest.raises(ValueError, match="platform_name"):
            service.ingest_platform(object())

    def test_ingest_platform_propagates_data_source(self) -> None:
        class ApiSourceOrders(FakeAmazonOrders):
            data_source = "spapi"

        adapter = PlatformAdapter(
            platform_name="amazon", orders=ApiSourceOrders()
        )
        service = OrderIngestService()
        records = service.ingest_platform(adapter)
        assert all(r.data_source == "spapi" for r in records)


class TestBuilderFunctions:
    def test_build_amazon_adapter_with_explicit_clients(self) -> None:
        adapter = build_amazon_adapter(
            orders_client=FakeAmazonOrders(),
            listings_client=FakeAmazonListings(),
            advertising_client=FakeAmazonAds(),
        )
        assert adapter.platform_name == "amazon"
        assert adapter.has_orders() is True
        assert adapter.has_listings() is True
        assert adapter.has_advertising() is True

    def test_build_shopify_adapter_with_explicit_client(self) -> None:
        adapter = build_shopify_adapter(store_client=FakeShopifyStore())
        assert adapter.platform_name == "shopify"
        assert adapter.has_orders() is True
        assert adapter.has_listings() is True
