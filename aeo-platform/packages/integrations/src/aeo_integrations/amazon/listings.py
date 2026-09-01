from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from aeo_integrations.amazon.config import AmazonDataSource, AmazonSettings, get_amazon_settings
from aeo_integrations.amazon.models import AmazonListing
from aeo_integrations.amazon.spapi_adapter import SpApiListingsAdapter

_MOCK_DIR = Path(__file__).resolve().parent / "mock"
_DEFAULT_FIXTURE = _MOCK_DIR / "sample_listings.json"


class ListingsClient(Protocol):
    def get_listing(self, sku: str, *, marketplace_id: str | None = None) -> AmazonListing: ...

    def list_listings(
        self,
        *,
        marketplace_id: str | None = None,
        limit: int = 20,
    ) -> list[AmazonListing]: ...


class MockListingsAdapter:
    def __init__(
        self, fixture_path: Path | None = None, settings: AmazonSettings | None = None
    ) -> None:
        self._fixture_path = fixture_path or _DEFAULT_FIXTURE
        self._settings = settings or get_amazon_settings()
        self._cache: dict[str, AmazonListing] | None = None

    def _load(self) -> dict[str, AmazonListing]:
        if self._cache is not None:
            return self._cache
        raw = json.loads(self._fixture_path.read_text(encoding="utf-8"))
        listings = [AmazonListing.model_validate(item) for item in raw["listings"]]
        self._cache = {listing.sku.upper(): listing for listing in listings}
        return self._cache

    def get_listing(self, sku: str, *, marketplace_id: str | None = None) -> AmazonListing:
        key = sku.strip().upper()
        listing = self._load().get(key)
        if listing is None:
            msg = f"Listing not found for SKU: {sku}"
            raise KeyError(msg)
        if marketplace_id and listing.marketplace_id != marketplace_id:
            msg = f"Listing {sku} not found in marketplace {marketplace_id}"
            raise KeyError(msg)
        return listing

    def list_listings(
        self,
        *,
        marketplace_id: str | None = None,
        limit: int = 20,
    ) -> list[AmazonListing]:
        marketplace = marketplace_id or self._settings.marketplace_id
        items = [
            listing for listing in self._load().values() if listing.marketplace_id == marketplace
        ]
        return items[:limit]


def get_listings_client(settings: AmazonSettings | None = None) -> ListingsClient:
    resolved = settings or get_amazon_settings()
    if resolved.data_source == AmazonDataSource.MOCK:
        return MockListingsAdapter(settings=resolved)
    return SpApiListingsAdapter(settings=resolved)
