"""Walmart Marketplace integration models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WalmartOrderLine:
    line_number: int
    sku: str
    product_name: str = ""
    quantity: int = 1
    unit_price: str = "0.00"
    currency: str = "USD"


@dataclass
class WalmartOrder:
    purchase_order_id: str
    order_status: str = "Created"
    order_date: str | None = None
    customer_name: str = ""
    shipping_address: dict[str, Any] = field(default_factory=dict)
    order_lines: list[WalmartOrderLine] = field(default_factory=list)
    currency: str = "USD"


@dataclass
class WalmartItem:
    sku: str
    product_name: str
    brand: str = ""
    price: str = "0.00"
    currency: str = "USD"
    stock: int = 0
    category: str = ""
    status: str = "ACTIVE"
    create_date: str | None = None
    update_date: str | None = None
