"""MV4-01: Order ingest service — unified order records from multiple platforms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class UnifiedOrderRecord:
    """Platform-agnostic order record."""

    external_order_id: str
    sku: str
    platform: str = "amazon"
    marketplace: str = "US"
    quantity: int = 1
    item_price: str = ""
    currency: str = "USD"
    order_status: str = "Unshipped"
    purchase_date: str = ""
    tracking_number: str = ""
    carrier: str = ""
    ship_date: str = ""
    delivery_date: str = ""
    return_status: str = "none"
    data_source: str = "mock"


class AmazonOrdersClient(Protocol):
    def list_orders(self, *, sku: str | None = None, limit: int = 20) -> list[Any]: ...


class ShopifyOrdersClient(Protocol):
    def list_orders(self, *, financial_status: str | None = None, limit: int = 50) -> list[Any]: ...


@dataclass
class OrderIngestService:
    """Ingests orders from multiple platforms into unified records."""

    _default_marketplace: str = "US"

    def ingest_amazon(
        self,
        client: AmazonOrdersClient,
        *,
        sku: str | None = None,
        limit: int = 50,
    ) -> list[UnifiedOrderRecord]:
        items = client.list_orders(sku=sku, limit=limit)
        return [self._map_amazon(item) for item in items]

    def ingest_shopify(
        self,
        client: ShopifyOrdersClient,
        *,
        financial_status: str | None = None,
        limit: int = 50,
    ) -> list[UnifiedOrderRecord]:
        items = client.list_orders(financial_status=financial_status, limit=limit)
        records: list[UnifiedOrderRecord] = []
        for order in items:
            records.extend(self._map_shopify_order(order))
        return records

    def ingest_all(
        self,
        *,
        amazon_client: AmazonOrdersClient | None = None,
        shopify_client: ShopifyOrdersClient | None = None,
    ) -> list[UnifiedOrderRecord]:
        records: list[UnifiedOrderRecord] = []
        if amazon_client is not None:
            records.extend(self.ingest_amazon(amazon_client))
        if shopify_client is not None:
            records.extend(self.ingest_shopify(shopify_client))
        return records

    def _map_amazon(self, item: Any) -> UnifiedOrderRecord:
        return UnifiedOrderRecord(
            external_order_id=item.order_id,
            sku=item.sku,
            platform="amazon",
            quantity=item.quantity,
            item_price=str(item.item_price) if item.item_price else "",
            currency=item.currency,
            order_status=item.order_status,
            purchase_date=item.purchase_date,
            tracking_number=item.tracking_number,
            carrier=item.carrier,
            ship_date=item.ship_date,
            delivery_date=item.delivery_date,
            return_status=item.return_status,
        )

    def _map_shopify_order(self, order: Any) -> list[UnifiedOrderRecord]:
        records: list[UnifiedOrderRecord] = []
        fulfillment_status = self._shopify_to_order_status(order.fulfillment_status)
        for line_item in order.line_items:
            sku = line_item.get("sku", "")
            if not sku:
                continue
            records.append(
                UnifiedOrderRecord(
                    external_order_id=order.order_id,
                    sku=sku,
                    platform="shopify",
                    quantity=line_item.get("quantity", 1),
                    item_price=line_item.get("price", ""),
                    currency=order.currency,
                    order_status=fulfillment_status,
                    purchase_date=order.created_at,
                )
            )
        return records

    @staticmethod
    def _shopify_to_order_status(fulfillment_status: str) -> str:
        mapping = {
            "fulfilled": "Shipped",
            "partial": "Unshipped",
            "unfulfilled": "Unshipped",
        }
        return mapping.get(fulfillment_status, "Unshipped")
