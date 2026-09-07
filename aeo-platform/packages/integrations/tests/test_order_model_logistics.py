"""MV4-01: order model logistics extension tests (RED phase)."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from aeo_integrations.amazon.models import AmazonOrderItem


class TestAmazonOrderItemLogistics:
    def test_default_logistics_fields_are_empty(self) -> None:
        item = AmazonOrderItem(order_id="111-001", sku="SKU-1", quantity=1)
        assert item.tracking_number == ""
        assert item.carrier == ""
        assert item.ship_date == ""
        assert item.delivery_date == ""
        assert item.return_status == "none"

    def test_logistics_fields_populated(self) -> None:
        item = AmazonOrderItem(
            order_id="111-002",
            sku="SKU-2",
            quantity=1,
            item_price=Decimal("29.99"),
            order_status="Shipped",
            tracking_number="1Z999AA10123456784",
            carrier="UPS",
            ship_date="2026-09-05T10:00:00Z",
            delivery_date="2026-09-08T14:00:00Z",
            return_status="none",
        )
        assert item.tracking_number == "1Z999AA10123456784"
        assert item.carrier == "UPS"
        assert item.ship_date == "2026-09-05T10:00:00Z"
        assert item.delivery_date == "2026-09-08T14:00:00Z"

    def test_return_status_values(self) -> None:
        statuses: list[Literal["none", "requested", "in_transit", "completed", "rejected"]] = [
            "none",
            "requested",
            "in_transit",
            "completed",
            "rejected",
        ]
        for status in statuses:
            item = AmazonOrderItem(
                order_id="111-003",
                sku="SKU-3",
                quantity=1,
                return_status=status,
            )
            assert item.return_status == status
