"""Tests for Google Ads DTC integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aeo_integrations.google_ads.adapter import GoogleAdsApiAdapter

from decimal import Decimal
from unittest.mock import MagicMock, patch

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
        from aeo_integrations.google_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_google_ads_client()
        assert client is not None

    def test_list_campaigns(self) -> None:
        from aeo_integrations.google_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_google_ads_client()
        campaigns = client.list_campaigns()
        assert len(campaigns) >= 1

    def test_list_campaigns_filter_status(self) -> None:
        from aeo_integrations.google_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_google_ads_client()
        enabled = client.list_campaigns(status="ENABLED")
        assert all(c.status == "ENABLED" for c in enabled)

    def test_get_campaign(self) -> None:
        from aeo_integrations.google_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_google_ads_client()
        campaign = client.get_campaign("G-CAMP-001")
        assert campaign.campaign_id == "G-CAMP-001"

    def test_get_campaign_not_found(self) -> None:
        from aeo_integrations.google_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_google_ads_client()
        with pytest.raises(KeyError):
            client.get_campaign("NONEXISTENT")

    def test_list_spend_snapshots(self) -> None:
        from aeo_integrations.google_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_google_ads_client()
        snapshots = client.list_spend_snapshots()
        assert len(snapshots) >= 1

    def test_list_spend_snapshots_filter_campaign(self) -> None:
        from aeo_integrations.google_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_google_ads_client()
        snapshots = client.list_spend_snapshots(campaign_id="G-CAMP-002")
        assert all(s.campaign_id == "G-CAMP-002" for s in snapshots)

    def test_list_campaigns_with_limit(self) -> None:
        from aeo_integrations.google_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_google_ads_client()
        campaigns = client.list_campaigns(limit=2)
        assert len(campaigns) <= 2


class TestGoogleAdsApiAdapter:
    def _make_adapter(self) -> GoogleAdsApiAdapter:
        from aeo_integrations.google_ads.adapter import GoogleAdsApiAdapter
        from aeo_integrations.google_ads.config import GoogleAdsSettings

        settings = GoogleAdsSettings(
            GOOGLE_ADS_DEVELOPER_TOKEN="dev-token",
            GOOGLE_ADS_CLIENT_ID="client-id",
            GOOGLE_ADS_CLIENT_SECRET="client-secret",
            GOOGLE_ADS_REFRESH_TOKEN="refresh-token",
            GOOGLE_ADS_CUSTOMER_ID="123-456-7890",
        )
        return GoogleAdsApiAdapter(settings)

    def _mock_response(self, json_data: list[dict[str, Any]]) -> MagicMock:
        resp = MagicMock()
        resp.json.return_value = json_data
        resp.raise_for_status.return_value = None
        return resp

    def test_list_campaigns_calls_api(self) -> None:
        adapter = self._make_adapter()
        mock_resp = self._mock_response(
            [
                {
                    "results": [
                        {
                            "campaign": {
                                "id": "111",
                                "name": "Search Camp",
                                "status": "ENABLED",
                                "advertisingChannelType": "SEARCH",
                            },
                            "campaignBudget": {"amountMicros": 50000000},
                        }
                    ]
                }
            ]
        )
        with (
            patch("aeo_integrations.google_ads.adapter.get_access_token") as mock_auth,
            patch("aeo_integrations.google_ads.adapter.requests.post", return_value=mock_resp),
        ):
            mock_auth.return_value = MagicMock(access_token="test-token")
            campaigns = adapter.list_campaigns()
        assert len(campaigns) == 1
        assert campaigns[0].name == "Search Camp"
        assert campaigns[0].daily_budget == Decimal("50")

    def test_get_campaign_calls_api(self) -> None:
        adapter = self._make_adapter()
        mock_resp = self._mock_response(
            [
                {
                    "results": [
                        {
                            "campaign": {
                                "id": "222",
                                "name": "Shopping Camp",
                                "status": "PAUSED",
                                "advertisingChannelType": "SHOPPING",
                            },
                            "campaignBudget": {"amountMicros": 30000000},
                        }
                    ]
                }
            ]
        )
        with (
            patch("aeo_integrations.google_ads.adapter.get_access_token") as mock_auth,
            patch("aeo_integrations.google_ads.adapter.requests.post", return_value=mock_resp),
        ):
            mock_auth.return_value = MagicMock(access_token="test-token")
            campaign = adapter.get_campaign("222")
        assert campaign.campaign_id == "222"
        assert campaign.status == "PAUSED"

    def test_list_spend_snapshots_calls_api(self) -> None:
        adapter = self._make_adapter()
        mock_resp = self._mock_response(
            [
                {
                    "results": [
                        {
                            "campaign": {"id": "111"},
                            "segments": {"date": "2026-09-01"},
                            "metrics": {
                                "costMicros": 5000000,
                                "impressions": 1000,
                                "clicks": 30,
                                "conversions": 5,
                                "conversionsValue": 250.0,
                            },
                        }
                    ]
                }
            ]
        )
        with (
            patch("aeo_integrations.google_ads.adapter.get_access_token") as mock_auth,
            patch("aeo_integrations.google_ads.adapter.requests.post", return_value=mock_resp),
        ):
            mock_auth.return_value = MagicMock(access_token="test-token")
            snapshots = adapter.list_spend_snapshots()
        assert len(snapshots) == 1
        assert snapshots[0].spend == Decimal("5")
        assert snapshots[0].conversions == 5

    def test_data_source(self) -> None:
        adapter = self._make_adapter()
        assert adapter.data_source == "google"

    def test_clean_customer_id(self) -> None:
        from aeo_integrations.google_ads.config import GoogleAdsSettings

        settings = GoogleAdsSettings(GOOGLE_ADS_CUSTOMER_ID="123-456-7890")
        assert settings.clean_customer_id == "1234567890"


class TestGoogleAdsMockDataIntegrity:
    def test_campaign_fields_complete(self) -> None:
        from aeo_integrations.google_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_google_ads_client()
        for c in client.list_campaigns():
            assert c.campaign_id
            assert c.name

    def test_snapshot_fields_complete(self) -> None:
        from aeo_integrations.google_ads import client as client_mod

        client_mod._client = None
        client = client_mod.get_google_ads_client()
        for s in client.list_spend_snapshots():
            assert s.campaign_id
            assert s.spend is not None
