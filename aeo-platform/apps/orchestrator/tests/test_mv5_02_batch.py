"""MV5-02: batch runner script tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from aeo_shared.batch_metrics import AgentExecRecord, SkuBatchResult


@pytest.fixture()
def sample_items() -> list[dict[str, Any]]:
    return [
        {
            "id": "MV5-001",
            "sku": "ACME-EARBUDS-PRO",
            "product_name": "Acme Wireless Earbuds Pro",
            "platform": "amazon",
            "market": "US",
            "category": "wireless_earbuds",
            "product_line": "Audio",
            "knowledge_doc": "knowledge/products/sample-product.md",
            "competitor_asins": ["B09XS7JWHH"],
            "keywords": ["wireless earbuds"],
            "price_usd": 49.99,
            "monthly_sales": 1200,
            "support_scenarios": ["shipping", "return"],
            "notes": "test",
        },
        {
            "id": "MV5-026",
            "sku": "ACME-EARBUDS-TK",
            "product_name": "Acme Wireless Earbuds Pro",
            "platform": "tiktok",
            "market": "US",
            "category": "wireless_earbuds",
            "product_line": "Audio",
            "knowledge_doc": None,
            "competitor_asins": [],
            "keywords": ["wireless earbuds"],
            "price_usd": 49.99,
            "monthly_sales": 600,
            "support_scenarios": ["shipping"],
            "notes": "test",
        },
        {
            "id": "MV5-040",
            "sku": "HOMEBREW-AIR-PURIFIER-SF",
            "product_name": "HomeBrew HEPA Air Purifier",
            "platform": "shopify",
            "market": "US",
            "category": "air_purifier",
            "product_line": "Home",
            "knowledge_doc": None,
            "competitor_asins": [],
            "keywords": ["air purifier"],
            "price_usd": 99.99,
            "monthly_sales": 200,
            "support_scenarios": ["shipping", "complaint"],
            "notes": "test",
        },
    ]


def test_load_testset_from_file(tmp_path: Path) -> None:
    testset = {
        "version": "2.0",
        "items": [{"id": "T1", "sku": "SKU1", "platform": "amazon"}],
    }
    p = tmp_path / "test.json"
    p.write_text(json.dumps(testset), encoding="utf-8")

    from scripts.batch_mv5_pilot import load_testset

    items = load_testset(p)
    assert len(items) == 1
    assert items[0]["sku"] == "SKU1"


def test_dry_run_mode(sample_items: list[dict[str, Any]], tmp_path: Path) -> None:
    testset = {"items": sample_items}
    p = tmp_path / "test.json"
    p.write_text(json.dumps(testset), encoding="utf-8")

    from scripts.batch_mv5_pilot import main

    rc = main(["--testset", str(p), "--dry-run", "--limit", "2"])
    assert rc == 0


def test_build_report_structure(sample_items: list[dict[str, Any]]) -> None:
    from scripts.batch_mv5_pilot import build_report

    results = [
        SkuBatchResult(
            sku_id="MV5-001",
            sku="A",
            platform="amazon",
            market="US",
            agents=[
                AgentExecRecord(
                    agent="selection",
                    status="completed",
                    duration_ms=100,
                    platform="amazon",
                ),
                AgentExecRecord(
                    agent="ads",
                    status="completed",
                    duration_ms=200,
                    platform="amazon",
                ),
            ],
        ),
        SkuBatchResult(
            sku_id="MV5-026",
            sku="B",
            platform="tiktok",
            market="US",
            agents=[
                AgentExecRecord(
                    agent="selection",
                    status="completed",
                    duration_ms=150,
                    platform="tiktok",
                ),
            ],
        ),
        SkuBatchResult(
            sku_id="MV5-040",
            sku="C",
            platform="shopify",
            market="US",
            agents=[
                AgentExecRecord(
                    agent="selection",
                    status="failed",
                    duration_ms=50,
                    platform="shopify",
                    error="err",
                ),
            ],
        ),
    ]

    report = build_report(results, testset_path="test.json")

    assert report["milestone"] == "MV5"
    assert report["task"] == "MV5-02"
    assert "summary" in report
    assert "per_sku" in report
    assert "kpi_check" in report

    s = report["summary"]
    assert s["total_skus"] == 3
    assert s["total_agent_runs"] == 4
    assert s["completed"] == 3
    assert s["failed"] == 1
    assert "amazon" in s["per_platform"]
    assert "tiktok" in s["per_platform"]
    assert "shopify" in s["per_platform"]


def test_kpi_check_in_report(sample_items: list[dict[str, Any]]) -> None:
    from scripts.batch_mv5_pilot import build_report

    results = [
        SkuBatchResult(
            sku_id=f"MV5-{i:03d}",
            sku=f"SKU-{i}",
            platform="amazon",
            market="US",
            agents=[
                AgentExecRecord(
                    agent="selection",
                    status="completed",
                    duration_ms=100,
                    platform="amazon",
                ),
            ],
        )
        for i in range(3)
    ]

    report = build_report(results, testset_path="test.json")
    kpi_check = report["kpi_check"]

    assert isinstance(kpi_check, list)
    assert len(kpi_check) > 0
    for check in kpi_check:
        assert "metric" in check
        assert "passed" in check


def test_is_degraded_detection() -> None:
    from scripts.batch_mv5_pilot import _is_degraded

    item_no_comp = {"competitor_asins": [], "knowledge_doc": "doc.md"}
    assert _is_degraded(item_no_comp, "selection") is True
    assert _is_degraded(item_no_comp, "ads") is False

    item_no_knowledge = {"competitor_asins": ["B123"], "knowledge_doc": None}
    assert _is_degraded(item_no_knowledge, "content") is True
    assert _is_degraded(item_no_knowledge, "selection") is False

    item_full = {"competitor_asins": ["B123"], "knowledge_doc": "doc.md"}
    assert _is_degraded(item_full, "selection") is False
    assert _is_degraded(item_full, "content") is False


def test_platform_choice_includes_shopify() -> None:
    from aeo_orchestrator.runner import PlatformChoice

    valid: PlatformChoice = "shopify"
    assert valid == "shopify"
