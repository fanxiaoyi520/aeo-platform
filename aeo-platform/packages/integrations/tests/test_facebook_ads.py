"""Tests for P3-03: Facebook Ads DTC integration."""

from __future__ import annotations

from decimal import Decimal

import pytest


class TestFacebookAdModels:
    def test_campaign_model(self) -> None:
        from aeo_integrations.facebook_ads.models import FacebookAdCampaign

        campaign = FacebookAdCampaign(
            campaign_id="FB-001",
            name="Test Campaign",
            status="ACTIVE",
            daily_budget=Decimal("50.00"),
        )
        assert campaign.campaign_id == "FB-001"
        assert campaign.daily_budget == Decimal("50.00")

    def test_spend_snapshot_model(self) -> None:
        from aeo_integrations.facebook_ads.models import FacebookAdSpendSnapshot

        snapshot = FacebookAdSpendSnapshot(
            campaign_id="FB-001",
            snapshot_date="2026-09-01",
            spend=Decimal("48.50"),
            impressions=12500,
            clicks=375,
            conversions=15,
            attributed_gmv=Decimal("750.00"),
        )
        assert snapshot.spend == Decimal("48.50")
        assert snapshot.conversions == 15


class TestFacebookAdsClient:
    def test_get_client_returns_mock(self) -> None:
        from aeo_integrations.facebook_ads.client import get_facebook_ads_client

        client = get_facebook_ads_client()
        assert client is not None

    def test_list_campaigns(self) -> None:
        from aeo_integrations.facebook_ads.client import get_facebook_ads_client

        client = get_facebook_ads_client()
        campaigns = client.list_campaigns()
        assert len(campaigns) >= 1

    def test_list_campaigns_filter_status(self) -> None:
        from aeo_integrations.facebook_ads.client import get_facebook_ads_client

        client = get_facebook_ads_client()
        active = client.list_campaigns(status="ACTIVE")
        assert all(c.status == "ACTIVE" for c in active)

    def test_get_campaign(self) -> None:
        from aeo_integrations.facebook_ads.client import get_facebook_ads_client

        client = get_facebook_ads_client()
        campaign = client.get_campaign("FB-CAMP-001")
        assert campaign.campaign_id == "FB-CAMP-001"

    def test_get_campaign_not_found_raises(self) -> None:
        from aeo_integrations.facebook_ads.client import get_facebook_ads_client

        client = get_facebook_ads_client()
        with pytest.raises(KeyError):
            client.get_campaign("NONEXISTENT")

    def test_list_spend_snapshots(self) -> None:
        from aeo_integrations.facebook_ads.client import get_facebook_ads_client

        client = get_facebook_ads_client()
        snapshots = client.list_spend_snapshots()
        assert len(snapshots) >= 1

    def test_list_spend_snapshots_filter_campaign(self) -> None:
        from aeo_integrations.facebook_ads.client import get_facebook_ads_client

        client = get_facebook_ads_client()
        snapshots = client.list_spend_snapshots(campaign_id="FB-CAMP-001")
        assert all(s.campaign_id == "FB-CAMP-001" for s in snapshots)

    def test_list_campaigns_with_limit(self) -> None:
        from aeo_integrations.facebook_ads.client import get_facebook_ads_client

        client = get_facebook_ads_client()
        campaigns = client.list_campaigns(limit=2)
        assert len(campaigns) <= 2


class TestFacebookAdsAdapter:
    def test_adapter_raises_not_implemented(self) -> None:
        from aeo_integrations.facebook_ads.adapter import FacebookAdsApiAdapter

        adapter = FacebookAdsApiAdapter(access_token="tok", ad_account_id="act_123")
        with pytest.raises(NotImplementedError):
            adapter.list_campaigns()

    def test_adapter_get_campaign_raises(self) -> None:
        from aeo_integrations.facebook_ads.adapter import FacebookAdsApiAdapter

        adapter = FacebookAdsApiAdapter(access_token="tok", ad_account_id="act_123")
        with pytest.raises(NotImplementedError):
            adapter.get_campaign("FB-001")

    def test_adapter_list_snapshots_raises(self) -> None:
        from aeo_integrations.facebook_ads.adapter import FacebookAdsApiAdapter

        adapter = FacebookAdsApiAdapter(access_token="tok", ad_account_id="act_123")
        with pytest.raises(NotImplementedError):
            adapter.list_spend_snapshots()


class TestFacebookAdsMockDataIntegrity:
    def test_campaign_fields_complete(self) -> None:
        from aeo_integrations.facebook_ads.client import get_facebook_ads_client

        client = get_facebook_ads_client()
        for c in client.list_campaigns():
            assert c.campaign_id
            assert c.name

    def test_snapshot_fields_complete(self) -> None:
        from aeo_integrations.facebook_ads.client import get_facebook_ads_client

        client = get_facebook_ads_client()
        for s in client.list_spend_snapshots():
            assert s.campaign_id
            assert s.spend is not None
