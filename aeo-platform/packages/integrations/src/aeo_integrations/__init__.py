"""External platform integrations (Amazon SP-API, Shopify, etc.)."""

from aeo_integrations.amazon import get_listings_client, get_orders_client
from aeo_integrations.shopify.store import get_store_client

__all__ = ["get_listings_client", "get_orders_client", "get_store_client"]
