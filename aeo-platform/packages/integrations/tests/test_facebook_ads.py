"""Tests for Facebook Ads DTC integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aeo_integrations.facebook_ads.adapter import FacebookAdsApiAdapter

from decimal import Decimal
from unittest.mock import MagicMock, patch

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
        from aeo_integrations.facebook_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_facebook_ads_client()
        assert client is not None

    def test_list_campaigns(self) -> None:
        from aeo_integrations.facebook_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_facebook_ads_client()
        campaigns = client.list_campaigns()
        assert len(campaigns) >= 1

    def test_list_campaigns_filter_status(self) -> None:
        from aeo_integrations.facebook_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_facebook_ads_client()
        active = client.list_campaigns(status="ACTIVE")
        assert all(c.status == "ACTIVE" for c in active)

    def test_get_campaign(self) -> None:
        from aeo_integrations.facebook_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_facebook_ads_client()
        campaign = client.get_campaign("FB-CAMP-001")
        assert campaign.campaign_id == "FB-CAMP-001"

    def test_get_campaign_not_found_raises(self) -> None:
        from aeo_integrations.facebook_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_facebook_ads_client()
        with pytest.raises(KeyError):
            client.get_campaign("NONEXISTENT")

    def test_list_spend_snapshots(self) -> None:
        from aeo_integrations.facebook_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_facebook_ads_client()
        snapshots = client.list_spend_snapshots()
        assert len(snapshots) >= 1

    def test_list_spend_snapshots_filter_campaign(self) -> None:
        from aeo_integrations.facebook_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_facebook_ads_client()
        snapshots = client.list_spend_snapshots(campaign_id="FB-CAMP-001")
        assert all(s.campaign_id == "FB-CAMP-001" for s in snapshots)

    def test_list_campaigns_with_limit(self) -> None:
        from aeo_integrations.facebook_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_facebook_ads_client()
        campaigns = client.list_campaigns(limit=2)
        assert len(campaigns) <= 2


class TestFacebookAdsApiAdapter:
    def _make_adapter(self) -> FacebookAdsApiAdapter:
        from aeo_integrations.facebook_ads.adapter import FacebookAdsApiAdapter
        from aeo_integrations.facebook_ads.config import FacebookAdsSettings

        settings = FacebookAdsSettings(
            FACEBOOK_ADS_ACCESS_TOKEN="test-token",
            FACEBOOK_ADS_AD_ACCOUNT_ID="123456",
        )
        return FacebookAdsApiAdapter(settings)

    def _mock_response(self, json_data: dict[str, Any]) -> MagicMock:
        resp = MagicMock()
        resp.json.return_value = json_data
        resp.raise_for_status.return_value = None
        return resp

    def test_list_campaigns_calls_api(self) -> None:
        adapter = self._make_adapter()
        mock_resp = self._mock_response(
            {
                "data": [
                    {
                        "id": "111",
                        "name": "Campaign A",
                        "status": "ACTIVE",
                        "objective": "CONVERSIONS",
                    },
                ]
            }
        )
        with patch("aeo_integrations.facebook_ads.adapter.requests.get", return_value=mock_resp):
            campaigns = adapter.list_campaigns()
        assert len(campaigns) == 1
        assert campaigns[0].name == "Campaign A"

    def test_get_campaign_calls_api(self) -> None:
        adapter = self._make_adapter()
        mock_resp = self._mock_response(
            {"id": "222", "name": "Campaign B", "status": "PAUSED", "objective": "TRAFFIC"}
        )
        with patch("aeo_integrations.facebook_ads.adapter.requests.get", return_value=mock_resp):
            campaign = adapter.get_campaign("222")
        assert campaign.campaign_id == "222"
        assert campaign.status == "PAUSED"

    def test_list_spend_snapshots_calls_api(self) -> None:
        adapter = self._make_adapter()
        mock_resp = self._mock_response(
            {
                "data": [
                    {
                        "campaign_id": "111",
                        "date_start": "2026-09-01",
                        "spend": "50.00",
                        "impressions": "1000",
                        "clicks": "30",
                        "actions": [{"action_type": "purchase", "value": "5"}],
                        "actions_value": [{"action_type": "purchase", "value": "250.00"}],
                    },
                ]
            }
        )
        with patch("aeo_integrations.facebook_ads.adapter.requests.get", return_value=mock_resp):
            snapshots = adapter.list_spend_snapshots()
        assert len(snapshots) == 1
        assert snapshots[0].conversions == 5

    def test_data_source(self) -> None:
        adapter = self._make_adapter()
        assert adapter.data_source == "facebook"


class TestFacebookAdsMockDataIntegrity:
    def test_campaign_fields_complete(self) -> None:
        from aeo_integrations.facebook_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_facebook_ads_client()
        for c in client.list_campaigns():
            assert c.campaign_id
            assert c.name

    def test_snapshot_fields_complete(self) -> None:
        from aeo_integrations.facebook_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_facebook_ads_client()
        for s in client.list_spend_snapshots():
            assert s.campaign_id
            assert s.spend is not None
