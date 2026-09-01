"""Tests for Amazon listing tool in orchestrator."""

import pytest
from aeo_integrations.amazon.models import AmazonListing
from aeo_orchestrator.tools.amazon_listing import (
    enrich_product_info_from_amazon,
    merge_listing_into_product_info,
)


def test_merge_listing_does_not_overwrite_user_title() -> None:
    listing = AmazonListing(
        sku="SKU-1",
        seller_sku="SKU-1",
        title="Amazon Title",
        brand="BrandX",
        bullets=["Bullet A"],
        keywords=["kw1"],
    )
    merged = merge_listing_into_product_info({"title": "User Title"}, listing)
    assert merged["title"] == "User Title"
    assert merged["brand"] == "BrandX"
    assert merged["amazon_listing"]["sku"] == "SKU-1"


def test_enrich_loads_pilot_sku_from_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMAZON_DATA_SOURCE", "mock")
    from aeo_integrations.amazon import config as config_module

    config_module.get_amazon_settings.cache_clear()
    product_info, listing = enrich_product_info_from_amazon(
        sku="HOMEBREW-KETTLE-1L",
        market="US",
        platform="amazon",
        product_info={},
    )
    assert listing is not None
    assert product_info["title"] == "HomeBrew Electric Kettle 1L"
    assert product_info["brand"] == "HomeBrew"
    assert len(product_info["bullets"]) == 3


def test_enrich_skips_non_amazon_platform() -> None:
    product_info, listing = enrich_product_info_from_amazon(
        sku="HOMEBREW-KETTLE-1L",
        market="US",
        platform="tiktok",
        product_info={"title": "TikTok only"},
    )
    assert listing is None
    assert product_info == {"title": "TikTok only"}


def test_enrich_unknown_sku_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMAZON_DATA_SOURCE", "mock")
    from aeo_integrations.amazon import config as config_module

    config_module.get_amazon_settings.cache_clear()
    product_info, listing = enrich_product_info_from_amazon(
        sku="UNKNOWN-SKU",
        market="US",
        platform="amazon",
        product_info={"category": "test"},
    )
    assert listing is None
    assert product_info == {"category": "test"}
