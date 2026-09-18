"""P7-14: Unified platform adapter interface.

Defines a platform-agnostic adapter Protocol so Amazon, Shopify, TikTok,
Walmart, etc. can be consumed interchangeably by the orchestrator, API,
and analytics layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class OrdersClient(Protocol):
    """Common orders surface across platforms."""

    def list_orders(self, **kwargs: Any) -> list[Any]: ...


@runtime_checkable
class ListingsClient(Protocol):
    """Common listings surface across platforms."""

    def list_items(self, **kwargs: Any) -> list[Any]: ...


@runtime_checkable
class AdvertisingClient(Protocol):
    """Common advertising surface across platforms."""

    def list_campaigns(self, **kwargs: Any) -> list[Any]: ...


@dataclass
class PlatformAdapter:
    """Bundles the per-platform clients under a common identity."""

    platform_name: str
    orders: OrdersClient | None = None
    listings: ListingsClient | None = None
    advertising: AdvertisingClient | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def data_source(self) -> str:
        """Best-effort data_source from the first client that exposes one."""
        for client in (self.orders, self.listings, self.advertising):
            source = getattr(client, "data_source", None)
            if source:
                return source
        return "mock"

    def has_orders(self) -> bool:
        return self.orders is not None

    def has_listings(self) -> bool:
        return self.listings is not None

    def has_advertising(self) -> bool:
        return self.advertising is not None


class PlatformRegistry:
    """Registry of named platform adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, PlatformAdapter] = {}

    def register(self, adapter: PlatformAdapter) -> None:
        self._adapters[adapter.platform_name] = adapter

    def get(self, platform_name: str) -> PlatformAdapter:
        adapter = self._adapters.get(platform_name)
        if adapter is None:
            msg = f"Unknown platform: {platform_name}"
            raise KeyError(msg)
        return adapter

    def list_platforms(self) -> list[str]:
        return sorted(self._adapters)

    def all(self) -> list[PlatformAdapter]:
        return [self._adapters[name] for name in self.list_platforms()]


def build_amazon_adapter(
    *,
    orders_client: OrdersClient | None = None,
    listings_client: ListingsClient | None = None,
    advertising_client: AdvertisingClient | None = None,
) -> PlatformAdapter:
    """Build a PlatformAdapter wired to Amazon clients.

    Clients are optional; callers can wire only the surfaces they need.
    """
    if orders_client is None or listings_client is None or advertising_client is None:
        try:
            from aeo_integrations.amazon import (
                get_advertising_client,
                get_listings_client,
                get_orders_client,
            )
        except ImportError as exc:
            msg = (
                "aeo_integrations.amazon is required to auto-build Amazon clients"
            )
            raise ImportError(msg) from exc
        orders_client = orders_client or get_orders_client()
        listings_client = listings_client or get_listings_client()
        advertising_client = advertising_client or get_advertising_client()
    return PlatformAdapter(
        platform_name="amazon",
        orders=orders_client,
        listings=listings_client,
        advertising=advertising_client,
    )


def build_shopify_adapter(
    *,
    store_client: ListingsClient | None = None,
) -> PlatformAdapter:
    """Build a PlatformAdapter wired to Shopify clients.

    Shopify currently exposes listings/orders through the StoreClient.
    """
    if store_client is None:
        try:
            from aeo_integrations.shopify.store import get_store_client
        except ImportError as exc:
            msg = (
                "aeo_integrations.shopify is required to auto-build Shopify clients"
            )
            raise ImportError(msg) from exc
        store_client = get_store_client()
    return PlatformAdapter(
        platform_name="shopify",
        orders=store_client,
        listings=store_client,
    )
