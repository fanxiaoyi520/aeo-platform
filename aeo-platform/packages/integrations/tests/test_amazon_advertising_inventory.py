"""Tests for MV3-01: Amazon advertising + inventory mock adapters."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from aeo_integrations.amazon.advertising import (
    MockAdvertisingAdapter,
    get_advertising_client,
)
from aeo_integrations.amazon.config import AmazonDataSource, AmazonSettings
from aeo_integrations.amazon.inventory import (
    MockInventoryAdapter,
    get_inventory_client,
)
from aeo_integrations.amazon.models import (
    AmazonAdCampaign,
    AmazonAdSpendSnapshot,
    AmazonInventoryItem,
)
from aeo_integrations.amazon.spapi_adapter import (
    SpApiAdvertisingAdapter,
    SpApiInventoryAdapter,
)

_MOCK_DIR = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "aeo_integrations"
    / "amazon"
    / "mock"
)
_AD_FIXTURE = _MOCK_DIR / "sample_advertising.json"
_INV_FIXTURE = _MOCK_DIR / "sample_inventory.json"


class TestAmazonAdCampaignModel:
    def test_create_campaign(self) -> None:
        campaign = AmazonAdCampaign(
            campaign_id="camp-001",
            name="Sponsored Kettle Push",
            status="enabled",
            campaign_type="sponsored_products",
            daily_budget=Decimal("15.00"),
            currency="USD",
            start_date="2026-09-01",
        )
        assert campaign.campaign_id == "camp-001"
        assert campaign.status == "enabled"
        assert campaign.daily_budget == Decimal("15.00")

    def test_campaign_defaults(self) -> None:
        campaign = AmazonAdCampaign(
            campaign_id="camp-002",
            name="Minimal Campaign",
        )
        assert campaign.status == "enabled"
        assert campaign.campaign_type == "sponsored_products"
        assert campaign.currency == "USD"
        assert campaign.end_date is None


class TestAmazonAdSpendSnapshotModel:
    def test_create_snapshot(self) -> None:
        snap = AmazonAdSpendSnapshot(
            campaign_id="camp-001",
            snapshot_date="2026-09-05",
            spend=Decimal("12.50"),
            impressions=3200,
            clicks=85,
            attributed_gmv=Decimal("149.95"),
            currency="USD",
        )
        assert snap.spend == Decimal("12.50")
        assert snap.impressions == 3200
        assert snap.attributed_gmv == Decimal("149.95")


class TestAmazonInventoryItemModel:
    def test_create_inventory_item(self) -> None:
        item = AmazonInventoryItem(
            sku="HOMEBREW-KETTLE-1L",
            fulfillment_channel="MFN",
            available_quantity=120,
            inbound_quantity=0,
            reserved_quantity=5,
            warehouse="US-EAST-1",
            last_updated="2026-09-05T10:00:00Z",
        )
        assert item.available_quantity == 120
        assert item.reserved_quantity == 5

    def test_inventory_defaults(self) -> None:
        item = AmazonInventoryItem(
            sku="TEST-SKU",
        )
        assert item.fulfillment_channel == "MFN"
        assert item.available_quantity == 0
        assert item.inbound_quantity == 0
        assert item.reserved_quantity == 0


class TestMockAdvertisingAdapter:
    def test_get_campaign_returns_known_id(self) -> None:
        client = MockAdvertisingAdapter(fixture_path=_AD_FIXTURE)
        campaign = client.get_campaign("camp-001")
        assert campaign.campaign_id == "camp-001"
        assert campaign.name == "Sponsored Kettle Push"
        assert campaign.status == "enabled"

    def test_get_campaign_case_insensitive(self) -> None:
        client = MockAdvertisingAdapter(fixture_path=_AD_FIXTURE)
        campaign = client.get_campaign("CAMP-001")
        assert campaign.campaign_id == "camp-001"

    def test_get_campaign_missing_raises(self) -> None:
        client = MockAdvertisingAdapter(fixture_path=_AD_FIXTURE)
        with pytest.raises(KeyError, match="UNKNOWN"):
            client.get_campaign("UNKNOWN")

    def test_list_campaigns_returns_all(self) -> None:
        client = MockAdvertisingAdapter(fixture_path=_AD_FIXTURE)
        campaigns = client.list_campaigns()
        assert len(campaigns) >= 3
        ids = {c.campaign_id for c in campaigns}
        assert "camp-001" in ids

    def test_list_campaigns_with_limit(self) -> None:
        client = MockAdvertisingAdapter(fixture_path=_AD_FIXTURE)
        campaigns = client.list_campaigns(limit=2)
        assert len(campaigns) == 2

    def test_list_campaigns_filter_by_status(self) -> None:
        client = MockAdvertisingAdapter(fixture_path=_AD_FIXTURE)
        enabled = client.list_campaigns(status="enabled")
        assert all(c.status == "enabled" for c in enabled)

    def test_get_spend_snapshot(self) -> None:
        client = MockAdvertisingAdapter(fixture_path=_AD_FIXTURE)
        snaps = client.list_spend_snapshots(campaign_id="camp-001")
        assert len(snaps) >= 1
        assert all(s.campaign_id == "camp-001" for s in snaps)

    def test_list_spend_snapshots_all(self) -> None:
        client = MockAdvertisingAdapter(fixture_path=_AD_FIXTURE)
        snaps = client.list_spend_snapshots()
        assert len(snaps) >= 3


class TestMockInventoryAdapter:
    def test_get_inventory_returns_known_sku(self) -> None:
        client = MockInventoryAdapter(fixture_path=_INV_FIXTURE)
        item = client.get_inventory("HOMEBREW-KETTLE-1L")
        assert item.sku == "HOMEBREW-KETTLE-1L"
        assert item.available_quantity > 0

    def test_get_inventory_case_insensitive(self) -> None:
        client = MockInventoryAdapter(fixture_path=_INV_FIXTURE)
        item = client.get_inventory("homebrew-kettle-1l")
        assert item.sku == "HOMEBREW-KETTLE-1L"

    def test_get_inventory_missing_sku_raises(self) -> None:
        client = MockInventoryAdapter(fixture_path=_INV_FIXTURE)
        with pytest.raises(KeyError, match="NOPE"):
            client.get_inventory("NOPE-SKU")

    def test_list_inventory_returns_all(self) -> None:
        client = MockInventoryAdapter(fixture_path=_INV_FIXTURE)
        items = client.list_inventory()
        assert len(items) >= 5
        skus = {i.sku for i in items}
        assert "HOMEBREW-KETTLE-1L" in skus

    def test_list_inventory_with_limit(self) -> None:
        client = MockInventoryAdapter(fixture_path=_INV_FIXTURE)
        items = client.list_inventory(limit=3)
        assert len(items) == 3

    def test_list_inventory_filter_by_channel(self) -> None:
        client = MockInventoryAdapter(fixture_path=_INV_FIXTURE)
        mfn = client.list_inventory(fulfillment_channel="MFN")
        assert all(i.fulfillment_channel == "MFN" for i in mfn)


class TestAdvertisingFactory:
    def test_factory_defaults_to_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AMAZON_DATA_SOURCE", raising=False)
        from aeo_integrations.amazon import config as config_module

        config_module.get_amazon_settings.cache_clear()
        client = get_advertising_client()
        assert isinstance(client, MockAdvertisingAdapter)

    def test_factory_spapi_returns_stub(self) -> None:
        settings = AmazonSettings(AMAZON_DATA_SOURCE=AmazonDataSource.SPAPI)
        client = get_advertising_client(settings=settings)
        assert isinstance(client, SpApiAdvertisingAdapter)
        with pytest.raises(NotImplementedError, match="not implemented"):
            client.get_campaign("camp-001")


class TestInventoryFactory:
    def test_factory_defaults_to_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AMAZON_DATA_SOURCE", raising=False)
        from aeo_integrations.amazon import config as config_module

        config_module.get_amazon_settings.cache_clear()
        client = get_inventory_client()
        assert isinstance(client, MockInventoryAdapter)

    def test_factory_spapi_returns_stub(self) -> None:
        settings = AmazonSettings(AMAZON_DATA_SOURCE=AmazonDataSource.SPAPI)
        client = get_inventory_client(settings=settings)
        assert isinstance(client, SpApiInventoryAdapter)
        with pytest.raises(NotImplementedError, match="not implemented"):
            client.get_inventory("HOMEBREW-KETTLE-1L")


class TestFixtureCompleteness:
    def test_advertising_fixture_has_campaigns(self) -> None:
        raw = json.loads(_AD_FIXTURE.read_text(encoding="utf-8"))
        assert "campaigns" in raw
        assert len(raw["campaigns"]) >= 3

    def test_advertising_fixture_has_spend(self) -> None:
        raw = json.loads(_AD_FIXTURE.read_text(encoding="utf-8"))
        assert "spend_snapshots" in raw
        assert len(raw["spend_snapshots"]) >= 3

    def test_inventory_fixture_has_all_pilot_skus(self) -> None:
        raw = json.loads(_INV_FIXTURE.read_text(encoding="utf-8"))
        skus = {item["sku"] for item in raw["inventory"]}
        expected = {
            "HOMEBREW-KETTLE-1L",
            "HOMEBREW-VACUUM-S",
            "KITCHEN-AIRFRYER-4QT",
            "KITCHEN-BLENDER-PRO",
            "GLOW-HAIRDRYER-ION",
        }
        assert skus == expected
