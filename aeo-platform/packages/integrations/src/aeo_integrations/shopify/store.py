"""Shopify Store API — Protocol + MockAdapter + Factory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, runtime_checkable

from aeo_integrations.shopify.models import (
    ShopifyAbandonedCart,
    ShopifyCustomer,
    ShopifyDiscountCode,
    ShopifyInventoryItem,
    ShopifyOrder,
    ShopifyProduct,
    ShopifyStoreMetrics,
)

_MOCK_DIR = Path(__file__).resolve().parent / "mock"


@runtime_checkable
class StoreClient(Protocol):
    """Read-only Shopify Store API client."""

    def list_products(
        self, *, status: str | None = None, limit: int = 50
    ) -> list[ShopifyProduct]: ...

    def list_orders(
        self, *, financial_status: str | None = None, limit: int = 50
    ) -> list[ShopifyOrder]: ...

    def list_inventory(
        self, *, sku: str | None = None, limit: int = 100
    ) -> list[ShopifyInventoryItem]: ...

    def list_abandoned_carts(
        self, *, limit: int = 50
    ) -> list[ShopifyAbandonedCart]: ...

    def list_customers(
        self, *, limit: int = 50
    ) -> list[ShopifyCustomer]: ...

    def list_discount_codes(
        self, *, is_active: bool | None = None, limit: int = 50
    ) -> list[ShopifyDiscountCode]: ...

    def get_store_metrics(
        self, *, limit: int = 30
    ) -> list[ShopifyStoreMetrics]: ...


class MockStoreAdapter:
    """Mock Shopify Store API adapter using local JSON fixtures."""

    def __init__(self) -> None:
        self._products = self._load_products()
        self._orders = self._load_orders()
        self._inventory = self._load_inventory()
        self._abandoned_carts = self._load_abandoned_carts()
        self._customers = self._load_customers()
        self._discount_codes = self._load_discount_codes()
        self._store_metrics = self._load_store_metrics()

    def _load_products(self) -> list[ShopifyProduct]:
        path = _MOCK_DIR / "sample_products.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return [ShopifyProduct(**item) for item in data]

    def _load_orders(self) -> list[ShopifyOrder]:
        path = _MOCK_DIR / "sample_orders.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return [ShopifyOrder(**item) for item in data]

    def _load_inventory(self) -> list[ShopifyInventoryItem]:
        path = _MOCK_DIR / "sample_inventory.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return [ShopifyInventoryItem(**item) for item in data]

    def _load_abandoned_carts(self) -> list[ShopifyAbandonedCart]:
        path = _MOCK_DIR / "sample_abandoned_carts.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return [ShopifyAbandonedCart(**item) for item in data]

    def _load_customers(self) -> list[ShopifyCustomer]:
        path = _MOCK_DIR / "sample_customers.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return [ShopifyCustomer(**item) for item in data]

    def _load_discount_codes(self) -> list[ShopifyDiscountCode]:
        path = _MOCK_DIR / "sample_discount_codes.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return [ShopifyDiscountCode(**item) for item in data]

    def _load_store_metrics(self) -> list[ShopifyStoreMetrics]:
        path = _MOCK_DIR / "sample_store_metrics.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return [ShopifyStoreMetrics(**item) for item in data]

    def list_products(self, *, status: str | None = None, limit: int = 50) -> list[ShopifyProduct]:
        results = self._products
        if status:
            results = [p for p in results if p.status == status]
        return results[:limit]

    def list_orders(
        self, *, financial_status: str | None = None, limit: int = 50
    ) -> list[ShopifyOrder]:
        results = self._orders
        if financial_status:
            results = [o for o in results if o.financial_status == financial_status]
        return results[:limit]

    def list_inventory(
        self, *, sku: str | None = None, limit: int = 100
    ) -> list[ShopifyInventoryItem]:
        results = self._inventory
        if sku:
            results = [i for i in results if i.sku == sku]
        return results[:limit]

    def list_abandoned_carts(
        self, *, limit: int = 50
    ) -> list[ShopifyAbandonedCart]:
        return self._abandoned_carts[:limit]

    def list_customers(
        self, *, limit: int = 50
    ) -> list[ShopifyCustomer]:
        return self._customers[:limit]

    def list_discount_codes(
        self, *, is_active: bool | None = None, limit: int = 50
    ) -> list[ShopifyDiscountCode]:
        results = self._discount_codes
        if is_active is not None:
            results = [c for c in results if c.is_active == is_active]
        return results[:limit]

    def get_store_metrics(
        self, *, limit: int = 30
    ) -> list[ShopifyStoreMetrics]:
        return self._store_metrics[:limit]


_client: MockStoreAdapter | None = None


def get_store_client() -> MockStoreAdapter:
    """Return the singleton mock store client."""
    global _client
    if _client is None:
        _client = MockStoreAdapter()
    return _client
