"""P7-10: Tests for TikTok Shop advertising client."""

from __future__ import annotations

import pytest
from aeo_integrations.tiktok import TikTokAdvertisingClient


class TestTikTokAdvertisingClient:
    def test_client_initialization_mock_mode(self) -> None:
        client = TikTokAdvertisingClient()
        assert client._use_mock is True
        assert client.data_source == "mock"

    def test_client_initialization_with_credentials(self) -> None:
        client = TikTokAdvertisingClient(access_token="test_token", shop_id="test_shop")
        assert client._use_mock is False
        assert client.data_source == "api"

    def test_list_campaigns_mock(self) -> None:
        client = TikTokAdvertisingClient()
        campaigns = client.list_campaigns()

        assert len(campaigns) == 3
        assert campaigns[0].campaign_id == "TT-AD-001"
        assert campaigns[0].name == "Earbuds Video Promo"
        assert campaigns[0].status == "ENABLE"
        assert campaigns[0].budget == "100.00"

    def test_list_campaigns_with_status_filter(self) -> None:
        client = TikTokAdvertisingClient()
        campaigns = client.list_campaigns(status="ENABLE")

        assert len(campaigns) == 2
        assert all(c.status == "ENABLE" for c in campaigns)

    def test_list_campaigns_with_limit(self) -> None:
        client = TikTokAdvertisingClient()
        campaigns = client.list_campaigns(limit=2)

        assert len(campaigns) == 2

    def test_get_campaign_mock(self) -> None:
        client = TikTokAdvertisingClient()
        campaign = client.get_campaign("TT-AD-001")

        assert campaign.campaign_id == "TT-AD-001"
        assert campaign.name == "Earbuds Video Promo"

    def test_get_campaign_not_found(self) -> None:
        client = TikTokAdvertisingClient()

        with pytest.raises(KeyError, match="Campaign not found"):
            client.get_campaign("NONEXISTENT")

    def test_list_spend_snapshots_mock(self) -> None:
        client = TikTokAdvertisingClient()
        snapshots = client.list_spend_snapshots()

        assert len(snapshots) == 4
        assert snapshots[0].campaign_id == "TT-AD-001"
        assert snapshots[0].date == "2026-09-15"
        assert snapshots[0].impressions == 5000
        assert snapshots[0].spend == "45.50"

    def test_list_spend_snapshots_with_campaign_filter(self) -> None:
        client = TikTokAdvertisingClient()
        snapshots = client.list_spend_snapshots(campaign_id="TT-AD-001")

        assert len(snapshots) == 2
        assert all(s.campaign_id == "TT-AD-001" for s in snapshots)

    def test_list_spend_snapshots_with_date_filter(self) -> None:
        client = TikTokAdvertisingClient()
        snapshots = client.list_spend_snapshots(start_date="2026-09-16")

        assert len(snapshots) == 2
        assert all(s.date >= "2026-09-16" for s in snapshots)

    def test_list_spend_snapshots_with_limit(self) -> None:
        client = TikTokAdvertisingClient()
        snapshots = client.list_spend_snapshots(limit=2)

        assert len(snapshots) == 2

    def test_api_methods_raise_not_implemented(self) -> None:
        client = TikTokAdvertisingClient(access_token="token", shop_id="shop")

        with pytest.raises(NotImplementedError):
            client._api_list_campaigns(status=None, limit=20)

        with pytest.raises(NotImplementedError):
            client._api_get_campaign("TT-AD-001")

        with pytest.raises(NotImplementedError):
            client._api_list_spend_snapshots(
                campaign_id=None,
                start_date=None,
                end_date=None,
                limit=50,
            )
