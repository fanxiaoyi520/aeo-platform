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
