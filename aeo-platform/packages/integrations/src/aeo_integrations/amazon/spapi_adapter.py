from __future__ import annotations

from aeo_integrations.amazon.config import AmazonSettings
from aeo_integrations.amazon.models import AmazonListing, AmazonOrderItem


class SpApiListingsAdapter:
    def __init__(self, settings: AmazonSettings) -> None:
        self._settings = settings

    def get_listing(self, sku: str, *, marketplace_id: str | None = None) -> AmazonListing:
        msg = (
            "SP-API Listings Items client is not implemented yet. "
            "Set AMAZON_DATA_SOURCE=mock until P1-03 / MV0-02 is confirmed."
        )
        raise NotImplementedError(msg)

    def list_listings(
        self,
        *,
        marketplace_id: str | None = None,
        limit: int = 20,
    ) -> list[AmazonListing]:
        msg = (
            "SP-API Listings Items client is not implemented yet. "
            "Set AMAZON_DATA_SOURCE=mock until P1-03 / MV0-02 is confirmed."
        )
        raise NotImplementedError(msg)


class SpApiOrdersAdapter:
    def __init__(self, settings: AmazonSettings) -> None:
        self._settings = settings

    def list_orders(
        self,
        *,
        sku: str | None = None,
        limit: int = 20,
    ) -> list[AmazonOrderItem]:
        msg = (
            "SP-API Orders client is not implemented yet. "
            "Set AMAZON_DATA_SOURCE=mock until P1-03 / MV0-02 is confirmed."
        )
        raise NotImplementedError(msg)
