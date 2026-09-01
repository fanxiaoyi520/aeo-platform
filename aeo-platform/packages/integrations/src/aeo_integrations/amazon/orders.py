from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from aeo_integrations.amazon.config import AmazonDataSource, AmazonSettings, get_amazon_settings
from aeo_integrations.amazon.models import AmazonOrderItem
from aeo_integrations.amazon.spapi_adapter import SpApiOrdersAdapter

_MOCK_DIR = Path(__file__).resolve().parent / "mock"
_DEFAULT_FIXTURE = _MOCK_DIR / "sample_orders.json"


class OrdersClient(Protocol):
    def list_orders(
        self,
        *,
        sku: str | None = None,
        limit: int = 20,
    ) -> list[AmazonOrderItem]: ...


class MockOrdersAdapter:
    def __init__(self, fixture_path: Path | None = None) -> None:
        self._fixture_path = fixture_path or _DEFAULT_FIXTURE
        self._cache: list[AmazonOrderItem] | None = None

    def _load(self) -> list[AmazonOrderItem]:
        if self._cache is not None:
            return self._cache
        raw = json.loads(self._fixture_path.read_text(encoding="utf-8"))
        self._cache = [AmazonOrderItem.model_validate(item) for item in raw["orders"]]
        return self._cache

    def list_orders(
        self,
        *,
        sku: str | None = None,
        limit: int = 20,
    ) -> list[AmazonOrderItem]:
        items = self._load()
        if sku:
            key = sku.strip().upper()
            items = [item for item in items if item.sku.upper() == key]
        return items[:limit]


def get_orders_client(settings: AmazonSettings | None = None) -> OrdersClient:
    resolved = settings or get_amazon_settings()
    if resolved.data_source == AmazonDataSource.MOCK:
        return MockOrdersAdapter()
    return SpApiOrdersAdapter(settings=resolved)
