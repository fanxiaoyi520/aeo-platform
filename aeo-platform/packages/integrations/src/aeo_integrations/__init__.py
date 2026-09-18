"""External platform integrations (Amazon SP-API, Shopify, Walmart, etc.)."""

from aeo_integrations.amazon import get_listings_client, get_orders_client
from aeo_integrations.shopify.store import get_store_client
from aeo_integrations.walmart import WalmartMarketplaceClient

__all__ = [
    "get_listings_client",
    "get_orders_client",
    "get_store_client",
    "WalmartMarketplaceClient",
]
