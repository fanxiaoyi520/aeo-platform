"""Amazon Selling Partner API adapters (mock + future SP-API)."""

from aeo_integrations.amazon.config import AmazonDataSource, get_amazon_settings
from aeo_integrations.amazon.listings import get_listings_client
from aeo_integrations.amazon.orders import get_orders_client

__all__ = [
    "AmazonDataSource",
    "get_amazon_settings",
    "get_listings_client",
    "get_orders_client",
]
