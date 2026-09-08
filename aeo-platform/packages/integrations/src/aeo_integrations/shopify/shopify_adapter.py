"""Shopify Admin API adapter — stub for production use."""

from __future__ import annotations

from aeo_integrations.shopify.models import (
    ShopifyAbandonedCart,
    ShopifyCustomer,
    ShopifyDiscountCode,
    ShopifyInventoryItem,
    ShopifyOrder,
    ShopifyProduct,
    ShopifyStoreMetrics,
)


class ShopifyApiAdapter:
    """Production Shopify Admin API adapter (not yet implemented)."""

    def __init__(self, store_url: str, access_token: str) -> None:
        self._store_url = store_url
        self._access_token = access_token

    def list_products(self, *, status: str | None = None, limit: int = 50) -> list[ShopifyProduct]:
        raise NotImplementedError("Shopify Admin API integration pending")

    def list_orders(
        self, *, financial_status: str | None = None, limit: int = 50
    ) -> list[ShopifyOrder]:
        raise NotImplementedError("Shopify Admin API integration pending")

    def list_inventory(
        self, *, sku: str | None = None, limit: int = 100
    ) -> list[ShopifyInventoryItem]:
        raise NotImplementedError("Shopify Admin API integration pending")

    def list_abandoned_carts(
        self, *, limit: int = 50
    ) -> list[ShopifyAbandonedCart]:
        raise NotImplementedError("Shopify Admin API integration pending")

    def list_customers(
        self, *, limit: int = 50
    ) -> list[ShopifyCustomer]:
        raise NotImplementedError("Shopify Admin API integration pending")

    def list_discount_codes(
        self, *, is_active: bool | None = None, limit: int = 50
    ) -> list[ShopifyDiscountCode]:
        raise NotImplementedError("Shopify Admin API integration pending")

    def get_store_metrics(
        self, *, limit: int = 30
    ) -> list[ShopifyStoreMetrics]:
        raise NotImplementedError("Shopify Admin API integration pending")
