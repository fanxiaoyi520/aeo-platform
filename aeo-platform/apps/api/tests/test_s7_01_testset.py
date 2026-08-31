"""S7-01 — Sample pilot SKU test set acceptance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

_AEO_PLATFORM_ROOT = Path(__file__).resolve().parents[3]
_REPO_ROOT = _AEO_PLATFORM_ROOT.parent
TESTSET_JSON = _AEO_PLATFORM_ROOT / "pilot" / "sample-sku-testset.json"
TESTSET_DOC = _REPO_ROOT / "docs" / "pilot" / "sample-sku-testset.md"

_REQUIRED_ITEM_FIELDS = {
    "id",
    "sku",
    "product_name",
    "platform",
    "market",
    "category",
    "product_line",
    "competitor_asins",
    "keywords",
    "notes",
}


def _load_testset() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(TESTSET_JSON.read_text(encoding="utf-8"))
    return data


def test_s7_01_testset_files_exist() -> None:
    assert TESTSET_JSON.is_file()
    assert TESTSET_DOC.is_file()


def test_s7_01_testset_has_exactly_20_skus() -> None:
    data = _load_testset()
    assert data["milestone"] == "MS7"
    assert data["task"] == "S7-01"
    items = data["items"]
    assert len(items) == 20
    ids = [item["id"] for item in items]
    assert len(ids) == len(set(ids)), "duplicate pilot ids"


@pytest.mark.parametrize(
    "field",
    sorted(_REQUIRED_ITEM_FIELDS),
)
def test_s7_01_each_item_has_required_fields(field: str) -> None:
    for item in _load_testset()["items"]:
        assert field in item, f"{item.get('id', '?')} missing {field}"


def test_s7_01_platform_distribution() -> None:
    items = _load_testset()["items"]
    amazon = sum(1 for item in items if item["platform"] == "amazon")
    tiktok = sum(1 for item in items if item["platform"] == "tiktok")
    assert amazon == 16
    assert tiktok == 4


def test_s7_01_includes_degraded_path_cases() -> None:
    items = _load_testset()["items"]
    no_competitor = [item for item in items if not item["competitor_asins"]]
    assert len(no_competitor) >= 5


def test_s7_01_skus_are_unique() -> None:
    skus = [item["sku"] for item in _load_testset()["items"]]
    assert len(skus) == len(set(skus))


def test_s7_01_create_task_payload_shape() -> None:
    """Each item maps to CreateTaskRequest-compatible payload."""
    sample = _load_testset()["items"][0]
    payload = {
        "sku": sample["sku"],
        "platform": sample["platform"],
        "market": sample["market"],
        "product_info": {},
    }
    if sample["competitor_asins"]:
        payload["product_info"]["competitor_asins"] = sample["competitor_asins"]
    if sample["keywords"]:
        payload["product_info"]["keywords"] = sample["keywords"]
    assert payload["platform"] in ("amazon", "tiktok")
    assert len(payload["sku"]) >= 1


def test_s7_01_doc_references_json_path() -> None:
    text = TESTSET_DOC.read_text(encoding="utf-8")
    assert "sample-sku-testset.json" in text
    assert "20 SKU" in text
