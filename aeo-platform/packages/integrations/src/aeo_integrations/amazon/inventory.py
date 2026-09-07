from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from aeo_integrations.amazon.config import AmazonDataSource, AmazonSettings, get_amazon_settings
from aeo_integrations.amazon.models import AmazonInventoryItem
from aeo_integrations.amazon.spapi_adapter import SpApiInventoryAdapter

_MOCK_DIR = Path(__file__).resolve().parent / "mock"
_DEFAULT_FIXTURE = _MOCK_DIR / "sample_inventory.json"


class InventoryClient(Protocol):
    def get_inventory(self, sku: str) -> AmazonInventoryItem: ...

    def list_inventory(
        self,
        *,
        fulfillment_channel: str | None = None,
        limit: int = 50,
    ) -> list[AmazonInventoryItem]: ...


class MockInventoryAdapter:
    def __init__(self, fixture_path: Path | None = None) -> None:
        self._fixture_path = fixture_path or _DEFAULT_FIXTURE
        self._cache: dict[str, AmazonInventoryItem] | None = None

    def _load(self) -> dict[str, AmazonInventoryItem]:
        if self._cache is not None:
            return self._cache
        raw = json.loads(self._fixture_path.read_text(encoding="utf-8"))
        items = [AmazonInventoryItem.model_validate(item) for item in raw["inventory"]]
        self._cache = {item.sku.upper(): item for item in items}
        return self._cache

    def get_inventory(self, sku: str) -> AmazonInventoryItem:
        key = sku.strip().upper()
        item = self._load().get(key)
        if item is None:
            msg = f"Inventory not found for SKU: {sku}"
            raise KeyError(msg)
        return item

    def list_inventory(
        self,
        *,
        fulfillment_channel: str | None = None,
        limit: int = 50,
    ) -> list[AmazonInventoryItem]:
        items = list(self._load().values())
        if fulfillment_channel:
            items = [i for i in items if i.fulfillment_channel == fulfillment_channel]
        return items[:limit]


def get_inventory_client(
    settings: AmazonSettings | None = None,
) -> InventoryClient:
    resolved = settings or get_amazon_settings()
    if resolved.data_source == AmazonDataSource.MOCK:
        return MockInventoryAdapter()
    return SpApiInventoryAdapter(settings=resolved)
