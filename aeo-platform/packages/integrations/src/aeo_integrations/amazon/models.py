from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class AmazonListing(BaseModel):
    """Normalized listing view aligned with SP-API Listings Items (simplified)."""

    sku: str
    seller_sku: str
    asin: str | None = None
    marketplace_id: str = "ATVPDKIKX0DER"
    status: Literal["ACTIVE", "INACTIVE", "SUPPRESSED"] = "ACTIVE"
    title: str
    brand: str = ""
    bullets: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    price: Decimal | None = None
    currency: str = "USD"
    fulfillment_channel: Literal["AFN", "MFN"] = "MFN"
    quantity: int | None = None


class AmazonOrderItem(BaseModel):
    """Normalized order line item (Orders API simplified)."""

    order_id: str
    sku: str
    quantity: int
    item_price: Decimal | None = None
    currency: str = "USD"
    order_status: Literal["Pending", "Unshipped", "Shipped", "Canceled"] = "Unshipped"
    purchase_date: str = ""


class AmazonAccessToken(BaseModel):
    access_token: str
    expires_in: int
    token_type: str = "bearer"
