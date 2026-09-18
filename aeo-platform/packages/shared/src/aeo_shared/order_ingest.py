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


class WalmartOrdersClient(Protocol):
    """Protocol matching the Walmart Marketplace adapter's order surface."""

    def list_orders(self, *, status: str | None = None, limit: int = 20) -> list[Any]: ...


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
        data_source = getattr(client, "data_source", "mock")
        return [self._map_amazon(item, data_source=data_source) for item in items]

    def ingest_shopify(
        self,
        client: ShopifyOrdersClient,
        *,
        financial_status: str | None = None,
        limit: int = 50,
    ) -> list[UnifiedOrderRecord]:
        items = client.list_orders(financial_status=financial_status, limit=limit)
        data_source = getattr(client, "data_source", "mock")
        records: list[UnifiedOrderRecord] = []
        for order in items:
            records.extend(self._map_shopify_order(order, data_source=data_source))
        return records

    def ingest_walmart(
        self,
        client: WalmartOrdersClient,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[UnifiedOrderRecord]:
        orders = client.list_orders(status=status, limit=limit)
        data_source = getattr(client, "data_source", "mock")
        records: list[UnifiedOrderRecord] = []
        for order in orders:
            records.extend(self._map_walmart_order(order, data_source=data_source))
        return records

    def ingest_all(
        self,
        *,
        amazon_client: AmazonOrdersClient | None = None,
        shopify_client: ShopifyOrdersClient | None = None,
        walmart_client: WalmartOrdersClient | None = None,
    ) -> list[UnifiedOrderRecord]:
        records: list[UnifiedOrderRecord] = []
        if amazon_client is not None:
            records.extend(self.ingest_amazon(amazon_client))
        if shopify_client is not None:
            records.extend(self.ingest_shopify(shopify_client))
        if walmart_client is not None:
            records.extend(self.ingest_walmart(walmart_client))
        return records

    def _map_amazon(self, item: Any, *, data_source: str = "mock") -> UnifiedOrderRecord:
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
            data_source=data_source,
        )

    def _map_shopify_order(
        self, order: Any, *, data_source: str = "mock"
    ) -> list[UnifiedOrderRecord]:
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
                    data_source=data_source,
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

    def _map_walmart_order(
        self, order: Any, *, data_source: str = "mock"
    ) -> list[UnifiedOrderRecord]:
        records: list[UnifiedOrderRecord] = []
        order_status = self._walmart_to_order_status(
            getattr(order, "order_status", "Created")
        )
        purchase_date = getattr(order, "order_date", "") or ""
        order_lines = getattr(order, "order_lines", None) or []
        for line in order_lines:
            sku = getattr(line, "sku", "") or ""
            if not sku:
                continue
            records.append(
                UnifiedOrderRecord(
                    external_order_id=getattr(order, "purchase_order_id", ""),
                    sku=sku,
                    platform="walmart",
                    marketplace=self._default_marketplace,
                    quantity=getattr(line, "quantity", 1),
                    item_price=str(getattr(line, "unit_price", "") or ""),
                    currency="USD",
                    order_status=order_status,
                    purchase_date=purchase_date,
                    data_source=data_source,
                )
            )
        return records

    @staticmethod
    def _walmart_to_order_status(walmart_status: str) -> str:
        mapping = {
            "Created": "Unshipped",
            "Acknowledged": "Unshipped",
            "Shipped": "Shipped",
            "Delivered": "Delivered",
            "Cancelled": "Canceled",
            "Returned": "Returned",
        }
        return mapping.get(walmart_status, "Unshipped")
