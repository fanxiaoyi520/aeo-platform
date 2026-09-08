"""Shopify Store API — Protocol + MockAdapter + Factory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, runtime_checkable

from aeo_integrations.shopify.models import (
    ShopifyInventoryItem,
    ShopifyOrder,
    ShopifyProduct,
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


class MockStoreAdapter:
    """Mock Shopify Store API adapter using local JSON fixtures."""

    def __init__(self) -> None:
        self._products = self._load_products()
        self._orders = self._load_orders()
        self._inventory = self._load_inventory()

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


_client: MockStoreAdapter | None = None


def get_store_client() -> MockStoreAdapter:
    """Return the singleton mock store client."""
    global _client
    if _client is None:
        _client = MockStoreAdapter()
    return _client
