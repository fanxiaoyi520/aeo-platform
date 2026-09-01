"""External platform integrations (Amazon SP-API, etc.)."""

from aeo_integrations.amazon import get_listings_client, get_orders_client

__all__ = ["get_listings_client", "get_orders_client"]
