"""P7-25: Data export tool (CSV/JSON).

Exports tenant data (orders, listings, metrics, billing) to CSV or
JSON with explicit column definitions and safe serialization of
non-JSON-native types.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from enum import StrEnum
from typing import Any


class ExportFormat(StrEnum):
    CSV = "csv"
    JSON = "json"


class ExportKind(StrEnum):
    ORDERS = "orders"
    LISTINGS = "listings"
    METRICS = "metrics"
    BILLING = "billing"


@dataclass(frozen=True)
class ExportColumn:
    """One column in an export."""

    name: str
    accessor: str  # attribute name on the row dataclass


@dataclass(frozen=True)
class ExportResult:
    """Output of an export operation."""

    kind: ExportKind
    format: ExportFormat
    content: str
    row_count: int
    columns: list[str]


def _serialize_value(value: Any) -> Any:
    """Make a value JSON-safe."""
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    return str(value)


def _extract_columns(
    row: Any, columns: list[ExportColumn]
) -> dict[str, Any]:
    return {
        col.name: _serialize_value(getattr(row, col.accessor, None))
        for col in columns
    }


def export_to_csv(
    rows: Iterable[Any], columns: list[ExportColumn]
) -> str:
    """Render rows as CSV. Non-string values are serialized safely."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=[c.name for c in columns])
    writer.writeheader()
    for row in rows:
        writer.writerow(_extract_columns(row, columns))
    return buffer.getvalue()


def export_to_json(
    rows: Iterable[Any], columns: list[ExportColumn]
) -> str:
    """Render rows as a JSON array."""
    data = [_extract_columns(row, columns) for row in rows]
    return json.dumps(data, indent=2, ensure_ascii=False)


def columns_from_dataclass(cls: type) -> list[ExportColumn]:
    """Build a column list from a dataclass's fields."""
    if not is_dataclass(cls):
        msg = f"{cls!r} is not a dataclass"
        raise TypeError(msg)
    return [ExportColumn(name=f.name, accessor=f.name) for f in fields(cls)]


@dataclass
class DataExporter:
    """High-level export facade."""

    def export(
        self,
        rows: Iterable[Any],
        *,
        kind: ExportKind,
        format: ExportFormat,
        columns: list[ExportColumn] | None = None,
    ) -> ExportResult:
        if columns is None:
            msg = "columns must be provided (or derive from dataclass)"
            raise ValueError(msg)
        rows_list = list(rows)
        if format == ExportFormat.CSV:
            content = export_to_csv(rows_list, columns)
        elif format == ExportFormat.JSON:
            content = export_to_json(rows_list, columns)
        else:
            msg = f"Unsupported format: {format}"
            raise ValueError(msg)
        return ExportResult(
            kind=kind,
            format=format,
            content=content,
            row_count=len(rows_list),
            columns=[c.name for c in columns],
        )
