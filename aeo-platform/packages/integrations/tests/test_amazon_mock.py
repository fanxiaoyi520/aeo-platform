"""Tests for Amazon SP-API mock skeleton."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from aeo_integrations.amazon.auth import get_access_token
from aeo_integrations.amazon.config import AmazonDataSource, AmazonSettings
from aeo_integrations.amazon.listings import MockListingsAdapter, get_listings_client
from aeo_integrations.amazon.orders import MockOrdersAdapter, get_orders_client
from aeo_integrations.amazon.spapi_adapter import SpApiListingsAdapter

_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "aeo_integrations"
    / "amazon"
    / "mock"
    / "sample_listings.json"
)


def test_mock_get_listing_returns_pilot_sku() -> None:
    client = MockListingsAdapter(fixture_path=_FIXTURE)
    listing = client.get_listing("HOMEBREW-KETTLE-1L")
    assert listing.sku == "HOMEBREW-KETTLE-1L"
    assert listing.brand == "HomeBrew"
    assert listing.status == "ACTIVE"
    assert len(listing.bullets) == 3


def test_mock_get_listing_case_insensitive() -> None:
    client = MockListingsAdapter(fixture_path=_FIXTURE)
    listing = client.get_listing("homebrew-kettle-1l")
    assert listing.title == "HomeBrew Electric Kettle 1L"


def test_mock_get_listing_missing_sku_raises() -> None:
    client = MockListingsAdapter(fixture_path=_FIXTURE)
    with pytest.raises(KeyError, match="UNKNOWN-SKU"):
        client.get_listing("UNKNOWN-SKU")


def test_mock_list_listings_returns_all_pilot_skus() -> None:
    client = MockListingsAdapter(fixture_path=_FIXTURE)
    listings = client.list_listings(limit=10)
    assert len(listings) == 5
    skus = {item.sku for item in listings}
    assert "GLOW-HAIRDRYER-ION" in skus


def test_factory_defaults_to_mock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AMAZON_DATA_SOURCE", raising=False)
    from aeo_integrations.amazon import config as config_module

    config_module.get_amazon_settings.cache_clear()
    client = get_listings_client()
    assert isinstance(client, MockListingsAdapter)


def test_factory_spapi_returns_stub() -> None:
    settings = AmazonSettings(AMAZON_DATA_SOURCE=AmazonDataSource.SPAPI)
    client = get_listings_client(settings=settings)
    assert isinstance(client, SpApiListingsAdapter)
    with pytest.raises(NotImplementedError, match="not implemented"):
        client.get_listing("HOMEBREW-KETTLE-1L")


def test_mock_auth_returns_token() -> None:
    from aeo_integrations.amazon import config as config_module

    config_module.get_amazon_settings.cache_clear()
    token = get_access_token()
    assert token.access_token == "mock-access-token"
    assert token.expires_in == 3600


def test_mock_orders_filter_by_sku() -> None:
    client = MockOrdersAdapter()
    orders = client.list_orders(sku="HOMEBREW-KETTLE-1L")
    assert len(orders) == 1
    assert orders[0].order_id.startswith("111-")


def test_fixture_matches_p1_02_skus() -> None:
    raw = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    skus = {item["sku"] for item in raw["listings"]}
    expected = {
        "HOMEBREW-KETTLE-1L",
        "HOMEBREW-VACUUM-S",
        "KITCHEN-AIRFRYER-4QT",
        "KITCHEN-BLENDER-PRO",
        "GLOW-HAIRDRYER-ION",
    }
    assert skus == expected


def test_orders_client_factory_mock() -> None:
    settings = AmazonSettings(AMAZON_DATA_SOURCE=AmazonDataSource.MOCK)
    client = get_orders_client(settings=settings)
    assert isinstance(client, MockOrdersAdapter)
    assert len(client.list_orders()) >= 1
