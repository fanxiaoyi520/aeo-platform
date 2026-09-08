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
    tracking_number: str = ""
    carrier: str = ""
    ship_date: str = ""
    delivery_date: str = ""
    return_status: Literal["none", "requested", "in_transit", "completed", "rejected"] = "none"


class AmazonAccessToken(BaseModel):
    access_token: str
    expires_in: int
    token_type: str = "bearer"


class AmazonAdCampaign(BaseModel):
    """Normalized advertising campaign (Advertising API simplified)."""

    campaign_id: str
    name: str = ""
    status: Literal["enabled", "paused", "archived"] = "enabled"
    campaign_type: Literal["sponsored_products", "sponsored_brands", "sponsored_display"] = (
        "sponsored_products"
    )
    daily_budget: Decimal | None = None
    currency: str = "USD"
    start_date: str = ""
    end_date: str | None = None
    associated_skus: list[str] = Field(default_factory=list)


class AmazonAdSpendSnapshot(BaseModel):
    """Daily advertising performance snapshot."""

    campaign_id: str
    snapshot_date: str = ""
    spend: Decimal | None = None
    impressions: int = 0
    clicks: int = 0
    attributed_gmv: Decimal | None = None
    currency: str = "USD"


class AmazonInventoryItem(BaseModel):
    """Normalized inventory view (FBA Inventory API simplified)."""

    sku: str
    fulfillment_channel: Literal["AFN", "MFN"] = "MFN"
    available_quantity: int = 0
    inbound_quantity: int = 0
    reserved_quantity: int = 0
    warehouse: str = ""
    last_updated: str = ""
