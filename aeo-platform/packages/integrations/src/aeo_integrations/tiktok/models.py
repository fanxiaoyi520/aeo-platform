"""TikTok Shop integration models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TikTokOrderItem:
    order_id: str
    sku: str
    quantity: int
    unit_price: str | None = None
    product_name: str | None = None
    order_status: str = "AwaitingShipment"
    create_time: str | None = None
    update_time: str | None = None
    tracking_number: str = ""
    shipping_provider: str = ""
    buyer_username: str = ""
    payment_method: str = ""
    currency: str = "USD"


@dataclass
class TikTokProduct:
    product_id: str
    sku: str
    title: str
    description: str = ""
    price: str = "0.00"
    currency: str = "USD"
    stock: int = 0
    status: str = "ACTIVE"
    category_id: str = ""
    brand: str = ""
    images: list[str] = field(default_factory=list)
    create_time: str | None = None
    update_time: str | None = None


@dataclass
class TikTokAdCampaign:
    campaign_id: str
    name: str
    status: str = "ENABLE"
    budget: str | None = None
    currency: str = "USD"
    ad_type: str = "VIDEO_SHOPPING"
    create_time: str | None = None
    update_time: str | None = None


@dataclass
class TikTokAdReport:
    campaign_id: str
    date: str
    impressions: int = 0
    clicks: int = 0
    spend: str = "0.00"
    conversions: int = 0
    gmv: str = "0.00"
    currency: str = "USD"
