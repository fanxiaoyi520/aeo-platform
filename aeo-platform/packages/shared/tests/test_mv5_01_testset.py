"""MV5-01: validate 50-SKU multi-platform test set."""

import json
from pathlib import Path
from typing import Any

import pytest

TESTSET_PATH = Path(__file__).resolve().parents[3] / "pilot" / "mv5-50sku-testset.json"

REQUIRED_FIELDS = {
    "id",
    "sku",
    "product_name",
    "platform",
    "market",
    "category",
    "product_line",
    "knowledge_doc",
    "competitor_asins",
    "keywords",
    "notes",
    "price_usd",
    "monthly_sales",
    "support_scenarios",
}
VALID_PLATFORMS = {"amazon", "tiktok", "shopify"}
MIN_CATEGORIES = 8
MIN_SKUS = 50
MIN_NO_COMP = 5
MIN_NO_KNOWLEDGE = 5


@pytest.fixture(scope="module")
def testset() -> dict[str, Any]:
    assert TESTSET_PATH.exists(), f"Test set not found: {TESTSET_PATH}"
    with open(TESTSET_PATH, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


@pytest.fixture(scope="module")
def items(testset: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = testset["items"]
    return result


def test_mv5_01_total_count(items: list[dict[str, Any]]) -> None:
    assert len(items) >= MIN_SKUS, f"Expected >= {MIN_SKUS} SKUs, got {len(items)}"


def test_mv5_01_platform_distribution(items: list[dict[str, Any]]) -> None:
    counts: dict[str, int] = {}
    for item in items:
        p: str = item["platform"]
        counts[p] = counts.get(p, 0) + 1

    assert counts.get("amazon", 0) >= 25, f"Amazon SKUs: {counts.get('amazon', 0)}"
    assert counts.get("tiktok", 0) >= 15, f"TikTok SKUs: {counts.get('tiktok', 0)}"
    assert counts.get("shopify", 0) >= 10, f"Shopify SKUs: {counts.get('shopify', 0)}"


def test_mv5_01_category_coverage(items: list[dict[str, Any]]) -> None:
    categories = {item["category"] for item in items}
    assert len(categories) >= MIN_CATEGORIES, (
        f"Expected >= {MIN_CATEGORIES} categories, got {len(categories)}: {categories}"
    )


def test_mv5_01_required_fields(items: list[dict[str, Any]]) -> None:
    for item in items:
        missing = REQUIRED_FIELDS - set(item.keys())
        assert not missing, f"Item {item.get('id', '?')} missing fields: {missing}"


def test_mv5_01_no_empty_required_fields(items: list[dict[str, Any]]) -> None:
    for item in items:
        assert item["id"], f"Empty id in {item}"
        assert item["sku"], f"Empty sku in {item}"
        assert item["product_name"], f"Empty product_name in {item}"
        assert item["platform"] in VALID_PLATFORMS, (
            f"Invalid platform '{item['platform']}' in {item['id']}"
        )
        assert item["market"], f"Empty market in {item['id']}"
        assert isinstance(item["competitor_asins"], list)
        assert isinstance(item["keywords"], list)
        assert isinstance(item["support_scenarios"], list)
        assert isinstance(item["price_usd"], (int, float))
        assert item["price_usd"] > 0
        assert isinstance(item["monthly_sales"], int)
        assert item["monthly_sales"] >= 0


def test_mv5_01_degradation_no_competitor_asins(items: list[dict[str, Any]]) -> None:
    no_comp = [i for i in items if not i["competitor_asins"]]
    assert len(no_comp) >= MIN_NO_COMP, (
        f"Expected >= {MIN_NO_COMP} items with empty competitor_asins, got {len(no_comp)}"
    )


def test_mv5_01_degradation_no_knowledge_doc(items: list[dict[str, Any]]) -> None:
    no_knowledge = [i for i in items if not i.get("knowledge_doc")]
    assert len(no_knowledge) >= MIN_NO_KNOWLEDGE, (
        f"Expected >= {MIN_NO_KNOWLEDGE} items with null knowledge_doc, got {len(no_knowledge)}"
    )


def test_mv5_01_support_scenarios_coverage(items: list[dict[str, Any]]) -> None:
    expected_scenarios = {"shipping", "return", "refund", "complaint", "exchange", "inquiry"}
    all_scenarios: set[str] = set()
    for item in items:
        all_scenarios.update(item["support_scenarios"])
    uncovered = expected_scenarios - all_scenarios
    assert not uncovered, f"Support scenarios not covered: {uncovered}"


def test_mv5_01_unique_ids_and_skus(items: list[dict[str, Any]]) -> None:
    ids = [item["id"] for item in items]
    skus = [item["sku"] for item in items]
    assert len(ids) == len(set(ids)), "Duplicate IDs found"
    assert len(skus) == len(set(skus)), "Duplicate SKUs found"
