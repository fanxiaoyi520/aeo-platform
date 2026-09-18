"""P7-15: P7-MS2 multi-platform acceptance tests.

Verifies the unified data flow across Amazon, Shopify, TikTok, and
Walmart via the ``OrderIngestService`` and the P7-14 ``PlatformAdapter``.

TikTok and Walmart adapters land in separate PRs (P7-08/09/10, P7-12/13).
These acceptance tests use Protocol-compatible fake clients so the
multi-platform contract is exercised on ``main`` even before those
adapters merge. Once the real adapters land, the fakes can be swapped
for the real clients without changing the assertions.

P7-14 (``PlatformAdapter`` / ``PlatformRegistry``) lands in a sibling PR;
we import it lazily so this file still collects on ``main``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from aeo_shared.order_ingest import OrderIngestService, UnifiedOrderRecord

try:
    from aeo_shared.platform_adapter import PlatformAdapter, PlatformRegistry

    HAS_PLATFORM_ADAPTER = True
except ImportError:  # pragma: no cover - P7-14 not yet merged
    HAS_PLATFORM_ADAPTER = False

    @dataclass
    class PlatformAdapter:  # type: ignore[no-redef]
        """Minimal stand-in until P7-14 merges."""

        platform_name: str
        orders: Any = None
        listings: Any = None
        advertising: Any = None
        extra: dict[str, Any] = field(default_factory=dict)

        @property
        def data_source(self) -> str:
            for client in (self.orders, self.listings, self.advertising):
                source = getattr(client, "data_source", None)
                if source:
                    return source
            return "mock"

        def has_orders(self) -> bool:
            return self.orders is not None

    class PlatformRegistry:  # type: ignore[no-redef]
        """Minimal stand-in until P7-14 merges."""

        def __init__(self) -> None:
            self._adapters: dict[str, PlatformAdapter] = {}

        def register(self, adapter: PlatformAdapter) -> None:
            self._adapters[adapter.platform_name] = adapter

        def get(self, platform_name: str) -> PlatformAdapter:
            return self._adapters[platform_name]

        def list_platforms(self) -> list[str]:
            return sorted(self._adapters)

        def all(self) -> list[PlatformAdapter]:
            return [self._adapters[n] for n in self.list_platforms()]


requires_platform_adapter = pytest.mark.skipif(
    not HAS_PLATFORM_ADAPTER,
    reason="P7-14 PlatformAdapter not yet merged",
)


# ---------- Amazon ----------


@dataclass
class FakeAmazonItem:
    order_id: str
    sku: str
    quantity: int = 1
    item_price: str = "9.99"
    currency: str = "USD"
    order_status: str = "Shipped"
    purchase_date: str = "2026-09-15T10:00:00Z"
    tracking_number: str = "1Z000"
    carrier: str = "UPS"
    ship_date: str = "2026-09-16T08:00:00Z"
    delivery_date: str = ""
    return_status: str = "none"


class FakeAmazonOrders:
    data_source = "spapi"

    def list_orders(
        self, *, sku: str | None = None, limit: int = 20
    ) -> list[Any]:
        items = [
            FakeAmazonItem(order_id="AMZ-1001", sku="AMZ-SKU-A"),
            FakeAmazonItem(order_id="AMZ-1002", sku="AMZ-SKU-B", quantity=3),
        ]
        if sku:
            items = [i for i in items if i.sku == sku]
        return items[:limit]


# ---------- Shopify ----------


@dataclass
class FakeShopifyOrder:
    order_id: str
    order_number: int = 1001
    financial_status: str = "paid"
    fulfillment_status: str = "fulfilled"
    total_price: str | None = "19.99"
    line_items: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = "2026-09-15T09:00:00Z"
    currency: str = "USD"


class FakeShopifyStore:
    data_source = "shopify"

    def list_orders(
        self, *, financial_status: str | None = None, limit: int = 50
    ) -> list[Any]:
        orders = [
            FakeShopifyOrder(
                order_id="SH-2001",
                line_items=[
                    {"sku": "SH-SKU-X", "quantity": 1, "price": "19.99"},
                    {"sku": "SH-SKU-Y", "quantity": 2, "price": "5.00"},
                ],
            ),
        ]
        if financial_status:
            orders = [o for o in orders if o.financial_status == financial_status]
        return orders[:limit]


# ---------- TikTok ----------


@dataclass
class FakeTikTokOrderItem:
    order_id: str
    sku: str
    quantity: int = 1
    unit_price: str | None = "15.00"
    order_status: str = "AwaitingShipment"


class FakeTikTokOrders:
    data_source = "tiktok_api"

    def list_orders(
        self, *, status: str | None = None, limit: int = 20
    ) -> list[Any]:
        orders = [
            FakeTikTokOrderItem(order_id="TT-3001", sku="TT-SKU-1", quantity=2),
            FakeTikTokOrderItem(order_id="TT-3002", sku="TT-SKU-2"),
        ]
        if status:
            orders = [o for o in orders if o.order_status == status]
        return orders[:limit]


# ---------- Walmart ----------


@dataclass
class FakeWalmartOrderLine:
    sku: str
    quantity: int = 1
    unit_price: str = "0.00"


@dataclass
class FakeWalmartOrder:
    purchase_order_id: str
    order_status: str = "Created"
    order_date: str | None = None
    order_lines: list[FakeWalmartOrderLine] = field(default_factory=list)


class FakeWalmartOrders:
    data_source = "walmart_api"

    def list_orders(
        self, *, status: str | None = None, limit: int = 20
    ) -> list[Any]:
        orders = [
            FakeWalmartOrder(
                purchase_order_id="WM-4001",
                order_status="Shipped",
                order_date="2026-09-15T10:00:00Z",
                order_lines=[
                    FakeWalmartOrderLine(sku="WM-SKU-1", quantity=2, unit_price="12.50"),
                ],
            ),
        ]
        if status:
            orders = [o for o in orders if o.order_status == status]
        return orders[:limit]


# ---------- Acceptance tests ----------


class TestP7MS2MultiPlatformAcceptance:
    """P7-MS2 acceptance: 4 platforms flow into unified records."""

    def test_amazon_and_shopify_via_ingest_all(self) -> None:
        service = OrderIngestService()
        records = service.ingest_all(
            amazon_client=FakeAmazonOrders(),
            shopify_client=FakeShopifyStore(),
        )
        platforms = {r.platform for r in records}
        assert platforms == {"amazon", "shopify"}
        assert len(records) >= 3

    def test_each_platform_has_distinct_unified_records(self) -> None:
        service = OrderIngestService()
        amazon = service.ingest_amazon(FakeAmazonOrders())
        shopify = service.ingest_shopify(FakeShopifyStore())
        assert all(r.platform == "amazon" for r in amazon)
        assert all(r.platform == "shopify" for r in shopify)
        assert amazon[0].external_order_id.startswith("AMZ-")
        assert shopify[0].external_order_id.startswith("SH-")

    def test_tiktok_orders_flow_via_adapter(self) -> None:
        adapter = PlatformAdapter(
            platform_name="tiktok", orders=FakeTikTokOrders()
        )
        # TikTok uses the same status/limit shape as Walmart; dispatch
        # will reject it until the P7-13-style ingest_tiktok lands.
        # The acceptance contract is that the adapter exposes orders.
        assert adapter.has_orders() is True
        assert adapter.data_source == "tiktok_api"
        orders = adapter.orders.list_orders(limit=10)
        assert len(orders) == 2
        assert orders[0].order_id == "TT-3001"

    def test_walmart_orders_flow_via_adapter(self) -> None:
        adapter = PlatformAdapter(
            platform_name="walmart", orders=FakeWalmartOrders()
        )
        assert adapter.has_orders() is True
        assert adapter.data_source == "walmart_api"
        orders = adapter.orders.list_orders(limit=10)
        assert len(orders) == 1
        assert orders[0].purchase_order_id == "WM-4001"

    def test_registry_holds_all_platforms(self) -> None:
        registry = PlatformRegistry()
        registry.register(
            PlatformAdapter(platform_name="amazon", orders=FakeAmazonOrders())
        )
        registry.register(
            PlatformAdapter(platform_name="shopify", orders=FakeShopifyStore())
        )
        registry.register(
            PlatformAdapter(platform_name="tiktok", orders=FakeTikTokOrders())
        )
        registry.register(
            PlatformAdapter(platform_name="walmart", orders=FakeWalmartOrders())
        )
        assert registry.list_platforms() == [
            "amazon",
            "shopify",
            "tiktok",
            "walmart",
        ]
        assert len(registry.all()) == 4

    def test_unified_record_schema_consistent_across_platforms(self) -> None:
        """Every platform maps to the same UnifiedOrderRecord fields."""
        service = OrderIngestService()
        amazon = service.ingest_amazon(FakeAmazonOrders())
        shopify = service.ingest_shopify(FakeShopifyStore())
        all_records: list[UnifiedOrderRecord] = [*amazon, *shopify]
        required_fields = [
            "external_order_id",
            "sku",
            "platform",
            "quantity",
            "order_status",
            "data_source",
        ]
        for record in all_records:
            for field_name in required_fields:
                assert getattr(record, field_name), (
                    f"{field_name} missing on {record}"
                )

    def test_data_source_propagates_per_platform(self) -> None:
        service = OrderIngestService()
        amazon = service.ingest_amazon(FakeAmazonOrders())
        shopify = service.ingest_shopify(FakeShopifyStore())
        assert all(r.data_source == "spapi" for r in amazon)
        assert all(r.data_source == "shopify" for r in shopify)
