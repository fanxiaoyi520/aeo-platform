"""MV4-01: OrderIngestService tests (RED phase)."""

from __future__ import annotations

from typing import Any

from aeo_shared.order_ingest import OrderIngestService, UnifiedOrderRecord


class FakeAmazonOrders:
    def list_orders(self, *, sku: str | None = None, limit: int = 20) -> list[Any]:
        from aeo_integrations.amazon.models import AmazonOrderItem

        items = [
            AmazonOrderItem(
                order_id="AMZ-001",
                sku="SKU-A",
                quantity=1,
                item_price=None,
                order_status="Shipped",
                purchase_date="2026-09-01T10:00:00Z",
                tracking_number="1Z999AA10123456784",
                carrier="UPS",
                ship_date="2026-09-02T08:00:00Z",
            ),
            AmazonOrderItem(
                order_id="AMZ-002",
                sku="SKU-B",
                quantity=2,
                order_status="Unshipped",
                purchase_date="2026-09-03T14:00:00Z",
            ),
        ]
        if sku:
            key = sku.strip().upper()
            items = [i for i in items if i.sku.upper() == key]
        return items[:limit]


class FakeShopifyOrders:
    def list_orders(self, *, financial_status: str | None = None, limit: int = 20) -> list[Any]:
        from aeo_integrations.shopify.models import ShopifyOrder

        items = [
            ShopifyOrder(
                order_id="SH-001",
                order_number=1001,
                financial_status="paid",
                fulfillment_status="fulfilled",
                total_price=None,
                line_items=[{"sku": "SKU-C", "quantity": 1, "price": "19.99"}],
                created_at="2026-09-04T09:00:00Z",
            ),
        ]
        if financial_status:
            items = [o for o in items if o.financial_status == financial_status]
        return items[:limit]


class TestOrderIngestService:
    def test_ingest_amazon_orders(self) -> None:
        service = OrderIngestService()
        records = service.ingest_amazon(FakeAmazonOrders())
        assert len(records) == 2
        assert records[0].platform == "amazon"
        assert records[0].external_order_id == "AMZ-001"
        assert records[0].sku == "SKU-A"
        assert records[0].tracking_number == "1Z999AA10123456784"
        assert records[1].sku == "SKU-B"
        assert records[1].tracking_number == ""

    def test_ingest_shopify_orders(self) -> None:
        service = OrderIngestService()
        records = service.ingest_shopify(FakeShopifyOrders())
        assert len(records) == 1
        assert records[0].platform == "shopify"
        assert records[0].external_order_id == "SH-001"
        assert records[0].sku == "SKU-C"
        assert records[0].quantity == 1

    def test_ingest_all_returns_combined(self) -> None:
        service = OrderIngestService()
        records = service.ingest_all(
            amazon_client=FakeAmazonOrders(),
            shopify_client=FakeShopifyOrders(),
        )
        assert len(records) == 3
        platforms = {r.platform for r in records}
        assert platforms == {"amazon", "shopify"}

    def test_unified_order_record_fields(self) -> None:
        record = UnifiedOrderRecord(
            external_order_id="X-001",
            sku="SKU-X",
            platform="amazon",
            marketplace="US",
            quantity=3,
            order_status="Shipped",
        )
        assert record.tracking_number == ""
        assert record.carrier == ""
        assert record.return_status == "none"

    def test_ingest_amazon_with_sku_filter(self) -> None:
        service = OrderIngestService()
        records = service.ingest_amazon(FakeAmazonOrders(), sku="SKU-A")
        assert len(records) == 1
        assert records[0].sku == "SKU-A"
