"""Shopify integration models."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class ShopifyProduct(BaseModel):
    """Normalized Shopify product (Admin API simplified)."""

    product_id: str
    title: str
    handle: str = ""
    status: Literal["active", "archived", "draft"] = "active"
    vendor: str = ""
    product_type: str = ""
    price: Decimal | None = None
    compare_at_price: Decimal | None = None
    sku: str = ""
    inventory_quantity: int = 0
    tags: list[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class ShopifyOrder(BaseModel):
    """Normalized Shopify order (Admin API simplified)."""

    order_id: str
    order_number: int = 0
    financial_status: Literal["pending", "paid", "partially_paid", "refunded", "voided"] = "pending"
    fulfillment_status: Literal["fulfilled", "partial", "unfulfilled"] = "unfulfilled"
    total_price: Decimal | None = None
    subtotal_price: Decimal | None = None
    currency: str = "USD"
    line_items: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class ShopifyInventoryItem(BaseModel):
    """Normalized Shopify inventory item."""

    sku: str
    location_id: str = ""
    available: int = 0
    reserved: int = 0
    committed: int = 0
    updated_at: str = ""


class ShopifyAbandonedCart(BaseModel):
    """Normalized Shopify abandoned cart."""

    cart_id: str
    customer_email: str
    customer_id: str = ""
    total_value: Decimal | None = None
    line_count: int = 0
    recovery_email_sent: bool = False
    abandoned_at: str = ""


class ShopifyCustomer(BaseModel):
    """Normalized Shopify customer."""

    customer_id: str
    email: str
    first_name: str = ""
    last_name: str = ""
    total_spent: Decimal | None = None
    orders_count: int = 0
    accepts_marketing: bool = False
    state: str = "disabled"
    created_at: str = ""


class ShopifyDiscountCode(BaseModel):
    """Normalized Shopify discount code."""

    code_id: str
    code: str
    discount_type: str = "percentage"
    discount_value: Decimal | None = None
    usage_limit: int = 0
    times_used: int = 0
    is_active: bool = True
    created_at: str = ""


class ShopifyStoreMetrics(BaseModel):
    """Normalized Shopify store daily metrics."""

    date: str
    sessions: int = 0
    orders: int = 0
    revenue: Decimal | None = None
    conversion_rate: Decimal | None = None
    cart_abandonment_rate: Decimal | None = None
    avg_order_value: Decimal | None = None
