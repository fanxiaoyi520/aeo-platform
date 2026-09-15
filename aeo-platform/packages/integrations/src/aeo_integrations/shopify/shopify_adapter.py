from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

import requests

from aeo_integrations.shopify.config import ShopifySettings
from aeo_integrations.shopify.models import (
    ShopifyAbandonedCart,
    ShopifyCustomer,
    ShopifyDiscountCode,
    ShopifyInventoryItem,
    ShopifyOrder,
    ShopifyProduct,
    ShopifyStoreMetrics,
)

logger = logging.getLogger(__name__)


def _safe_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


class ShopifyApiAdapter:
    def __init__(self, settings: ShopifySettings) -> None:
        self._settings = settings
        self._base_url = f"{settings.store_url.rstrip('/')}/admin/api/{settings.api_version}"
        self._headers = {
            "X-Shopify-Access-Token": settings.access_token,
            "Content-Type": "application/json",
        }

    @property
    def data_source(self) -> str:
        return "shopify"

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self._base_url}/{path}"
        response = requests.get(
            url, headers=self._headers, params=params, timeout=self._settings.request_timeout
        )
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    def list_products(self, *, status: str | None = None, limit: int = 50) -> list[ShopifyProduct]:
        params: dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status
        data = self._get("products.json", params)
        return [self._map_product(p) for p in data.get("products", [])[:limit]]

    def list_orders(
        self, *, financial_status: str | None = None, limit: int = 50
    ) -> list[ShopifyOrder]:
        params: dict[str, Any] = {"limit": limit, "status": "any"}
        if financial_status:
            params["financial_status"] = financial_status
        data = self._get("orders.json", params)
        return [self._map_order(o) for o in data.get("orders", [])[:limit]]

    def list_inventory(
        self, *, sku: str | None = None, limit: int = 100
    ) -> list[ShopifyInventoryItem]:
        params: dict[str, Any] = {"limit": limit}
        data = self._get("inventory_levels.json", params)
        items = [self._map_inventory(i) for i in data.get("inventory_levels", [])[:limit]]
        if sku:
            items = [i for i in items if i.sku.upper() == sku.upper()]
        return items

    def list_abandoned_carts(self, *, limit: int = 50) -> list[ShopifyAbandonedCart]:
        params: dict[str, Any] = {"limit": limit}
        data = self._get("checkouts.json", params)
        return [self._map_cart(c) for c in data.get("checkouts", [])[:limit]]

    def list_customers(self, *, limit: int = 50) -> list[ShopifyCustomer]:
        params: dict[str, Any] = {"limit": limit}
        data = self._get("customers.json", params)
        return [self._map_customer(c) for c in data.get("customers", [])[:limit]]

    def list_discount_codes(
        self, *, is_active: bool | None = None, limit: int = 50
    ) -> list[ShopifyDiscountCode]:
        params: dict[str, Any] = {"limit": limit}
        data = self._get("price_rules.json", params)
        codes = [self._map_discount(pr) for pr in data.get("price_rules", [])[:limit]]
        if is_active is not None:
            codes = [c for c in codes if c.is_active == is_active]
        return codes

    def get_store_metrics(self, *, limit: int = 30) -> list[ShopifyStoreMetrics]:
        logger.warning(
            "Shopify Admin API does not provide direct store metrics; returning empty list"
        )
        return []

    def _map_product(self, data: dict[str, Any]) -> ShopifyProduct:
        variants = data.get("variants", [])
        first_variant = variants[0] if variants else {}
        return ShopifyProduct(
            product_id=str(data.get("id", "")),
            title=data.get("title", ""),
            handle=data.get("handle", ""),
            status=data.get("status", "active"),
            vendor=data.get("vendor", ""),
            product_type=data.get("product_type", ""),
            price=_safe_decimal(first_variant.get("price")),
            compare_at_price=_safe_decimal(first_variant.get("compare_at_price")),
            sku=first_variant.get("sku", ""),
            inventory_quantity=first_variant.get("inventory_quantity", 0),
            tags=data.get("tags", "").split(",") if data.get("tags") else [],
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def _map_order(self, data: dict[str, Any]) -> ShopifyOrder:
        return ShopifyOrder(
            order_id=str(data.get("id", "")),
            order_number=data.get("order_number", 0),
            financial_status=data.get("financial_status", "pending"),
            fulfillment_status=data.get("fulfillment_status", "unfulfilled"),
            total_price=_safe_decimal(data.get("total_price")),
            subtotal_price=_safe_decimal(data.get("subtotal_price")),
            currency=data.get("currency", "USD"),
            line_items=data.get("line_items", []),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def _map_inventory(self, data: dict[str, Any]) -> ShopifyInventoryItem:
        return ShopifyInventoryItem(
            sku=data.get("sku", ""),
            location_id=str(data.get("location_id", "")),
            available=data.get("available", 0),
            reserved=0,
            committed=0,
            updated_at=data.get("updated_at", ""),
        )

    def _map_cart(self, data: dict[str, Any]) -> ShopifyAbandonedCart:
        return ShopifyAbandonedCart(
            cart_id=str(data.get("id", "")),
            customer_email=data.get("email", ""),
            customer_id=str(data.get("customer", {}).get("id", "")) if data.get("customer") else "",
            total_value=_safe_decimal(data.get("total_price")),
            line_count=len(data.get("line_items", [])),
            recovery_email_sent=False,
            abandoned_at=data.get("abandoned_checkout_url", ""),
        )

    def _map_customer(self, data: dict[str, Any]) -> ShopifyCustomer:
        return ShopifyCustomer(
            customer_id=str(data.get("id", "")),
            email=data.get("email", ""),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            total_spent=_safe_decimal(data.get("total_spent")),
            orders_count=data.get("orders_count", 0),
            accepts_marketing=data.get("accepts_marketing", False),
            state=data.get("state", "disabled"),
            created_at=data.get("created_at", ""),
        )

    def _map_discount(self, data: dict[str, Any]) -> ShopifyDiscountCode:
        return ShopifyDiscountCode(
            code_id=str(data.get("id", "")),
            code=data.get("title", ""),
            discount_type=data.get("target_type", "percentage"),
            discount_value=_safe_decimal(data.get("value")),
            usage_limit=data.get("usage_limit", 0) or 0,
            times_used=data.get("times_used", 0),
            is_active=data.get("status", "active") == "active",
            created_at=data.get("created_at", ""),
        )
