"""Tests for product catalog import (P1-02 / OSS patterns)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from aeo_rag.product_catalog import (
    ProductRecord,
    import_csv_to_products,
    map_csv_headers,
    product_chunk_header,
    render_product_markdown,
    sync_testset_knowledge_docs,
)

_ROOT = Path(__file__).resolve().parents[3]
_TEMPLATE_CSV = _ROOT / "knowledge" / "templates" / "pilot-sku-batch.csv"


def test_map_csv_headers_aliases() -> None:
    mapping = map_csv_headers(["SKU", "Title", "bullet_1", "param_1", "keyword_1"])
    assert mapping.canonical["sku"] == "SKU"
    assert mapping.canonical["product_name"] == "Title"
    assert mapping.bullet_cols == ["bullet_1"]
    assert mapping.spec_cols == ["param_1"]
    assert mapping.keyword_cols == ["keyword_1"]


def test_render_product_markdown_includes_sku_table() -> None:
    product = ProductRecord(sku="TEST-SKU-1", product_name="Test Widget")
    md = render_product_markdown(product)
    assert "| SKU | TEST-SKU-1 |" in md
    assert "Test Widget" in md


def test_product_chunk_header_extracts_sku() -> None:
    content = render_product_markdown(ProductRecord(sku="ABC-123", product_name="Demo Product"))
    header = product_chunk_header("knowledge/products/abc-123.md", content)
    assert "SKU: ABC-123" in header
    assert "Product: Demo Product" in header


def test_import_csv_to_products_creates_files(tmp_path: Path) -> None:
    assert _TEMPLATE_CSV.is_file()
    results = import_csv_to_products(_TEMPLATE_CSV, tmp_path)
    assert len(results) == 5
    assert all(r.status in ("created", "updated") for r in results)
    assert (tmp_path / "homebrew-kettle-1l.md").is_file()


def test_import_idempotent_update(tmp_path: Path) -> None:
    import_csv_to_products(_TEMPLATE_CSV, tmp_path)
    second = import_csv_to_products(_TEMPLATE_CSV, tmp_path)
    assert all(r.status == "updated" for r in second)


def test_sync_testset_knowledge_docs(tmp_path: Path) -> None:
    testset = tmp_path / "testset.json"
    testset.write_text(
        json.dumps(
            {
                "items": [
                    {"sku": "HOMEBREW-KETTLE-1L", "knowledge_doc": None},
                    {"sku": "OTHER-SKU", "knowledge_doc": None},
                ]
            }
        ),
        encoding="utf-8",
    )
    updated = sync_testset_knowledge_docs(
        testset,
        {"HOMEBREW-KETTLE-1L": "knowledge/products/homebrew-kettle-1l.md"},
    )
    assert updated == 1
    data = json.loads(testset.read_text(encoding="utf-8"))
    assert data["items"][0]["knowledge_doc"] == "knowledge/products/homebrew-kettle-1l.md"


@pytest.mark.parametrize("score_min", [0, 50])
def test_completeness_score(score_min: int) -> None:
    product = ProductRecord(
        sku="X",
        product_name="Y",
        brand="Z",
        category="cat",
        overview="desc",
        specs=["a", "b"],
        keywords=["k1", "k2", "k3"],
        bullets=["b1", "b2", "b3"],
        competitor_asins=["B00000000"],
    )
    score, missing = product.completeness_score()
    assert score >= score_min
    assert not missing
