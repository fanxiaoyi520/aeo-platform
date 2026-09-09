"""Tests for P3-03: Google Ads DTC integration."""

from __future__ import annotations

from decimal import Decimal

import pytest


class TestGoogleAdModels:
    def test_campaign_model(self) -> None:
        from aeo_integrations.google_ads.models import GoogleAdCampaign

        campaign = GoogleAdCampaign(
            campaign_id="G-001",
            name="Test Campaign",
            status="ENABLED",
            daily_budget=Decimal("40.00"),
        )
        assert campaign.campaign_id == "G-001"
        assert campaign.daily_budget == Decimal("40.00")

    def test_spend_snapshot_model(self) -> None:
        from aeo_integrations.google_ads.models import GoogleAdSpendSnapshot

        snapshot = GoogleAdSpendSnapshot(
            campaign_id="G-001",
            snapshot_date="2026-09-01",
            spend=Decimal("38.50"),
            impressions=5200,
            clicks=312,
            conversions=12,
            attributed_gmv=Decimal("480.00"),
        )
        assert snapshot.spend == Decimal("38.50")
        assert snapshot.conversions == 12


class TestGoogleAdsClient:
    def test_get_client_returns_mock(self) -> None:
        from aeo_integrations.google_ads.client import get_google_ads_client

        client = get_google_ads_client()
        assert client is not None

    def test_list_campaigns(self) -> None:
        from aeo_integrations.google_ads.client import get_google_ads_client

        client = get_google_ads_client()
        campaigns = client.list_campaigns()
        assert len(campaigns) >= 1

    def test_list_campaigns_filter_status(self) -> None:
        from aeo_integrations.google_ads.client import get_google_ads_client

        client = get_google_ads_client()
        enabled = client.list_campaigns(status="ENABLED")
        assert all(c.status == "ENABLED" for c in enabled)

    def test_get_campaign(self) -> None:
        from aeo_integrations.google_ads.client import get_google_ads_client

        client = get_google_ads_client()
        campaign = client.get_campaign("G-CAMP-001")
        assert campaign.campaign_id == "G-CAMP-001"

    def test_get_campaign_not_found(self) -> None:
        from aeo_integrations.google_ads.client import get_google_ads_client

        client = get_google_ads_client()
        with pytest.raises(KeyError):
            client.get_campaign("NONEXISTENT")

    def test_list_spend_snapshots(self) -> None:
        from aeo_integrations.google_ads.client import get_google_ads_client

        client = get_google_ads_client()
        snapshots = client.list_spend_snapshots()
        assert len(snapshots) >= 1

    def test_list_spend_snapshots_filter_campaign(self) -> None:
        from aeo_integrations.google_ads.client import get_google_ads_client

        client = get_google_ads_client()
        snapshots = client.list_spend_snapshots(campaign_id="G-CAMP-002")
        assert all(s.campaign_id == "G-CAMP-002" for s in snapshots)

    def test_list_campaigns_with_limit(self) -> None:
        from aeo_integrations.google_ads.client import get_google_ads_client

        client = get_google_ads_client()
        campaigns = client.list_campaigns(limit=2)
        assert len(campaigns) <= 2


class TestGoogleAdsAdapter:
    def test_adapter_raises_not_implemented(self) -> None:
        from aeo_integrations.google_ads.adapter import GoogleAdsApiAdapter

        adapter = GoogleAdsApiAdapter(developer_token="tok", customer_id="123-456-7890")
        with pytest.raises(NotImplementedError):
            adapter.list_campaigns()

    def test_adapter_get_campaign_raises(self) -> None:
        from aeo_integrations.google_ads.adapter import GoogleAdsApiAdapter

        adapter = GoogleAdsApiAdapter(developer_token="tok", customer_id="123-456-7890")
        with pytest.raises(NotImplementedError):
            adapter.get_campaign("G-001")

    def test_adapter_list_snapshots_raises(self) -> None:
        from aeo_integrations.google_ads.adapter import GoogleAdsApiAdapter

        adapter = GoogleAdsApiAdapter(developer_token="tok", customer_id="123-456-7890")
        with pytest.raises(NotImplementedError):
            adapter.list_spend_snapshots()


class TestGoogleAdsMockDataIntegrity:
    def test_campaign_fields_complete(self) -> None:
        from aeo_integrations.google_ads.client import get_google_ads_client

        client = get_google_ads_client()
        for c in client.list_campaigns():
            assert c.campaign_id
            assert c.name

    def test_snapshot_fields_complete(self) -> None:
        from aeo_integrations.google_ads.client import get_google_ads_client

        client = get_google_ads_client()
        for s in client.list_spend_snapshots():
            assert s.campaign_id
            assert s.spend is not None
