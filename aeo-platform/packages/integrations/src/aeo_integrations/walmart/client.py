"""Walmart Marketplace API client with mock fallback."""

from __future__ import annotations

import os

from aeo_integrations.walmart.models import WalmartItem, WalmartOrder, WalmartOrderLine


class WalmartMarketplaceClient:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        self.client_id = client_id or os.environ.get("WALMART_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("WALMART_CLIENT_SECRET")
        self._use_mock = not (self.client_id and self.client_secret)

    @property
    def data_source(self) -> str:
        return "mock" if self._use_mock else "api"

    def list_orders(
        self,
        *,
        status: str | None = None,
        limit: int = 20,
    ) -> list[WalmartOrder]:
        if self._use_mock:
            return self._mock_orders(status=status, limit=limit)
        return self._api_list_orders(status=status, limit=limit)

    def get_order(self, purchase_order_id: str) -> WalmartOrder:
        if self._use_mock:
            orders = self._mock_orders(limit=100)
            for order in orders:
                if order.purchase_order_id == purchase_order_id:
                    return order
            msg = f"Order not found: {purchase_order_id}"
            raise KeyError(msg)
        return self._api_get_order(purchase_order_id)

    def list_items(
        self,
        *,
        status: str | None = None,
        limit: int = 20,
    ) -> list[WalmartItem]:
        if self._use_mock:
            return self._mock_items(status=status, limit=limit)
        return self._api_list_items(status=status, limit=limit)

    def get_item(self, sku: str) -> WalmartItem:
        if self._use_mock:
            items = self._mock_items(limit=100)
            for item in items:
                if item.sku == sku:
                    return item
            msg = f"Item not found: {sku}"
            raise KeyError(msg)
        return self._api_get_item(sku)

    def _api_list_orders(self, *, status: str | None, limit: int) -> list[WalmartOrder]:
        raise NotImplementedError("Walmart API integration pending")

    def _api_get_order(self, purchase_order_id: str) -> WalmartOrder:
        raise NotImplementedError("Walmart API integration pending")

    def _api_list_items(self, *, status: str | None, limit: int) -> list[WalmartItem]:
        raise NotImplementedError("Walmart API integration pending")

    def _api_get_item(self, sku: str) -> WalmartItem:
        raise NotImplementedError("Walmart API integration pending")

    def _mock_orders(self, *, status: str | None = None, limit: int = 20) -> list[WalmartOrder]:
        orders = [
            WalmartOrder(
                purchase_order_id="WM-001",
                order_status="Shipped",
                order_date="2026-09-15T10:00:00Z",
                customer_name="John Doe",
                shipping_address={"city": "New York", "state": "NY", "zip": "10001"},
                order_lines=[
                    WalmartOrderLine(
                        line_number=1,
                        sku="WM-SKU-A",
                        product_name="Wireless Mouse",
                        quantity=2,
                        unit_price="24.99",
                    ),
                ],
                currency="USD",
            ),
            WalmartOrder(
                purchase_order_id="WM-002",
                order_status="Created",
                order_date="2026-09-16T14:30:00Z",
                customer_name="Jane Smith",
                shipping_address={"city": "Los Angeles", "state": "CA", "zip": "90001"},
                order_lines=[
                    WalmartOrderLine(
                        line_number=1,
                        sku="WM-SKU-B",
                        product_name="USB-C Cable",
                        quantity=3,
                        unit_price="12.99",
                    ),
                ],
                currency="USD",
            ),
            WalmartOrder(
                purchase_order_id="WM-003",
                order_status="Delivered",
                order_date="2026-09-10T09:15:00Z",
                customer_name="Bob Johnson",
                shipping_address={"city": "Chicago", "state": "IL", "zip": "60601"},
                order_lines=[
                    WalmartOrderLine(
                        line_number=1,
                        sku="WM-SKU-A",
                        product_name="Wireless Mouse",
                        quantity=1,
                        unit_price="24.99",
                    ),
                ],
                currency="USD",
            ),
        ]
        if status:
            orders = [o for o in orders if o.order_status == status]
        return orders[:limit]

    def _mock_items(self, *, status: str | None = None, limit: int = 20) -> list[WalmartItem]:
        items = [
            WalmartItem(
                sku="WM-SKU-A",
                product_name="Wireless Mouse Pro",
                brand="TechBrand",
                price="24.99",
                stock=150,
                category="Electronics",
                status="ACTIVE",
                create_date="2026-08-01T00:00:00Z",
            ),
            WalmartItem(
                sku="WM-SKU-B",
                product_name="USB-C Cable 6ft",
                brand="CableCo",
                price="12.99",
                stock=300,
                category="Accessories",
                status="ACTIVE",
                create_date="2026-08-05T00:00:00Z",
            ),
        ]
        if status:
            items = [i for i in items if i.status == status]
        return items[:limit]
