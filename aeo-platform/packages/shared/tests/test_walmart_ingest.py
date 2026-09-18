"""P7-13: Walmart ingest adapter tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aeo_shared.order_ingest import OrderIngestService


@dataclass
class FakeWalmartOrderLine:
    sku: str
    quantity: int = 1
    unit_price: str = "0.00"


@dataclass
class FakeWalmartOrder:
    purchase_order_id: str
    order_status: str = "Created"
    order_date: str | None = None
    order_lines: list[FakeWalmartOrderLine] = field(default_factory=list)


class FakeWalmartOrders:
    def __init__(self, data_source: str = "mock") -> None:
        self._data_source = data_source

    @property
    def data_source(self) -> str:
        return self._data_source

    def list_orders(
        self, *, status: str | None = None, limit: int = 20
    ) -> list[Any]:
        orders = [
            FakeWalmartOrder(
                purchase_order_id="WM-001",
                order_status="Shipped",
                order_date="2026-09-10T10:00:00Z",
                order_lines=[
                    FakeWalmartOrderLine(sku="WM-SKU-1", quantity=2, unit_price="12.50"),
                    FakeWalmartOrderLine(sku="WM-SKU-2", quantity=1, unit_price="5.00"),
                ],
            ),
            FakeWalmartOrder(
                purchase_order_id="WM-002",
                order_status="Created",
                order_date="2026-09-11T12:00:00Z",
                order_lines=[FakeWalmartOrderLine(sku="WM-SKU-3", quantity=4)],
            ),
            FakeWalmartOrder(
                purchase_order_id="WM-EMPTY",
                order_status="Created",
                order_date="2026-09-12T08:00:00Z",
                order_lines=[],
            ),
        ]
        if status:
            orders = [o for o in orders if o.order_status == status]
        return orders[:limit]


class TestWalmartIngest:
    def test_ingest_walmart_returns_records_per_line(self) -> None:
        service = OrderIngestService()
        records = service.ingest_walmart(FakeWalmartOrders())
        # WM-001 has 2 lines, WM-002 has 1 line, WM-EMPTY has 0
        assert len(records) == 3
        assert all(r.platform == "walmart" for r in records)

    def test_ingest_walmart_maps_fields(self) -> None:
        service = OrderIngestService()
        records = service.ingest_walmart(FakeWalmartOrders())
        first = records[0]
        assert first.external_order_id == "WM-001"
        assert first.sku == "WM-SKU-1"
        assert first.quantity == 2
        assert first.item_price == "12.50"
        assert first.order_status == "Shipped"
        assert first.purchase_date == "2026-09-10T10:00:00Z"
        assert first.currency == "USD"

    def test_ingest_walmart_status_mapping(self) -> None:
        service = OrderIngestService()
        records = service.ingest_walmart(FakeWalmartOrders())
        # Second record is from WM-002 (Created -> Unshipped)
        created_record = next(r for r in records if r.external_order_id == "WM-002")
        assert created_record.order_status == "Unshipped"

    def test_ingest_walmart_with_status_filter(self) -> None:
        service = OrderIngestService()
        records = service.ingest_walmart(FakeWalmartOrders(), status="Shipped")
        # Only WM-001 is Shipped, with 2 lines
        assert len(records) == 2
        assert all(r.external_order_id == "WM-001" for r in records)

    def test_ingest_walmart_with_limit(self) -> None:
        service = OrderIngestService()
        records = service.ingest_walmart(FakeWalmartOrders(), limit=1)
        # Only first order (WM-001, 2 lines)
        assert len(records) == 2
        assert all(r.external_order_id == "WM-001" for r in records)

    def test_ingest_walmart_propagates_data_source(self) -> None:
        service = OrderIngestService()
        records = service.ingest_walmart(FakeWalmartOrders(data_source="api"))
        assert all(r.data_source == "api" for r in records)

    def test_ingest_walmart_defaults_to_mock_when_no_data_source(self) -> None:
        class NoDataSourceClient:
            def list_orders(
                self, *, status: str | None = None, limit: int = 20
            ) -> list[Any]:
                return [
                    FakeWalmartOrder(
                        purchase_order_id="WM-NO-DS",
                        order_status="Created",
                        order_lines=[FakeWalmartOrderLine(sku="SKU-X")],
                    )
                ]

        service = OrderIngestService()
        records = service.ingest_walmart(NoDataSourceClient())
        assert len(records) == 1
        assert records[0].data_source == "mock"

    def test_ingest_walmart_skips_lines_with_empty_sku(self) -> None:
        class EmptySkuClient:
            def __init__(self) -> None:
                self.data_source = "mock"

            def list_orders(
                self, *, status: str | None = None, limit: int = 20
            ) -> list[Any]:
                return [
                    FakeWalmartOrder(
                        purchase_order_id="WM-ES",
                        order_lines=[
                            FakeWalmartOrderLine(sku="", quantity=1),
                            FakeWalmartOrderLine(sku="VALID", quantity=2),
                        ],
                    )
                ]

        service = OrderIngestService()
        records = service.ingest_walmart(EmptySkuClient())
        assert len(records) == 1
        assert records[0].sku == "VALID"

    def test_ingest_all_includes_walmart(self) -> None:
        service = OrderIngestService()
        records = service.ingest_all(walmart_client=FakeWalmartOrders())
        assert len(records) == 3
        assert {r.platform for r in records} == {"walmart"}
