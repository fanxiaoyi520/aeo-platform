"""P7-25: Tests for data export tool."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass

import pytest
from aeo_shared.data_export import (
    DataExporter,
    ExportColumn,
    ExportFormat,
    ExportKind,
    ExportResult,
    columns_from_dataclass,
    export_to_csv,
    export_to_json,
)


@dataclass
class FakeOrder:
    order_id: str
    sku: str
    quantity: int
    price: float


@dataclass
class FakeMetric:
    tenant_id: str
    api_calls: int
    tags: list[str]


class TestExportToCsv:
    def test_basic_csv(self) -> None:
        rows = [FakeOrder("O1", "SKU-A", 1, 9.99)]
        columns = columns_from_dataclass(FakeOrder)
        csv_text = export_to_csv(rows, columns)
        reader = csv.DictReader(io.StringIO(csv_text))
        parsed = list(reader)
        assert len(parsed) == 1
        assert parsed[0]["order_id"] == "O1"
        assert parsed[0]["sku"] == "SKU-A"
        assert parsed[0]["quantity"] == "1"

    def test_empty_rows_writes_header_only(self) -> None:
        columns = columns_from_dataclass(FakeOrder)
        csv_text = export_to_csv([], columns)
        reader = csv.DictReader(io.StringIO(csv_text))
        assert list(reader) == []
        assert "order_id" in csv_text

    def test_subset_of_columns(self) -> None:
        rows = [FakeOrder("O1", "SKU-A", 1, 9.99)]
        columns = [
            ExportColumn(name="id", accessor="order_id"),
            ExportColumn(name="qty", accessor="quantity"),
        ]
        csv_text = export_to_csv(rows, columns)
        reader = csv.DictReader(io.StringIO(csv_text))
        parsed = list(reader)
        assert set(parsed[0].keys()) == {"id", "qty"}


class TestExportToJson:
    def test_basic_json(self) -> None:
        rows = [FakeOrder("O1", "SKU-A", 1, 9.99)]
        columns = columns_from_dataclass(FakeOrder)
        json_text = export_to_json(rows, columns)
        parsed = json.loads(json_text)
        assert len(parsed) == 1
        assert parsed[0]["order_id"] == "O1"
        assert parsed[0]["price"] == 9.99

    def test_empty_rows_returns_empty_array(self) -> None:
        columns = columns_from_dataclass(FakeOrder)
        json_text = export_to_json([], columns)
        assert json.loads(json_text) == []

    def test_list_field_serialized(self) -> None:
        rows = [FakeMetric("t1", 100, ["vip", "beta"])]
        columns = columns_from_dataclass(FakeMetric)
        json_text = export_to_json(rows, columns)
        parsed = json.loads(json_text)
        assert parsed[0]["tags"] == ["vip", "beta"]


class TestColumnsFromDataclass:
    def test_derives_from_fields(self) -> None:
        columns = columns_from_dataclass(FakeOrder)
        names = [c.name for c in columns]
        assert names == ["order_id", "sku", "quantity", "price"]
        assert all(c.name == c.accessor for c in columns)

    def test_non_dataclass_raises(self) -> None:
        with pytest.raises(TypeError, match="dataclass"):
            columns_from_dataclass(dict)  # type: ignore[arg-type]


class TestDataExporter:
    def test_export_csv(self) -> None:
        exporter = DataExporter()
        rows = [FakeOrder("O1", "SKU-A", 1, 9.99)]
        result = exporter.export(
            rows,
            kind=ExportKind.ORDERS,
            format=ExportFormat.CSV,
            columns=columns_from_dataclass(FakeOrder),
        )
        assert isinstance(result, ExportResult)
        assert result.row_count == 1
        assert result.format == ExportFormat.CSV
        assert result.kind == ExportKind.ORDERS
        assert "order_id" in result.content

    def test_export_json(self) -> None:
        exporter = DataExporter()
        rows = [FakeOrder("O1", "SKU-A", 1, 9.99)]
        result = exporter.export(
            rows,
            kind=ExportKind.ORDERS,
            format=ExportFormat.JSON,
            columns=columns_from_dataclass(FakeOrder),
        )
        assert result.format == ExportFormat.JSON
        parsed = json.loads(result.content)
        assert len(parsed) == 1

    def test_export_without_columns_raises(self) -> None:
        exporter = DataExporter()
        with pytest.raises(ValueError, match="columns"):
            exporter.export(
                [], kind=ExportKind.ORDERS, format=ExportFormat.CSV
            )

    def test_export_result_columns_match(self) -> None:
        exporter = DataExporter()
        rows = [FakeOrder("O1", "SKU-A", 1, 9.99)]
        result = exporter.export(
            rows,
            kind=ExportKind.ORDERS,
            format=ExportFormat.JSON,
            columns=columns_from_dataclass(FakeOrder),
        )
        assert result.columns == ["order_id", "sku", "quantity", "price"]
