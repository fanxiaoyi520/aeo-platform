"""Shopify Admin API adapter — stub for production use."""

from __future__ import annotations

from aeo_integrations.shopify.models import (
    ShopifyInventoryItem,
    ShopifyOrder,
    ShopifyProduct,
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
