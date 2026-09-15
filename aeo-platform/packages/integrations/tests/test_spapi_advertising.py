"""Tests for P6-19: SpApiAdvertisingAdapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from aeo_integrations.amazon.config import AmazonDataSource, AmazonSettings
from aeo_integrations.amazon.models import AmazonAccessToken
from aeo_integrations.amazon.spapi_adapter import SpApiAdvertisingAdapter


@pytest.fixture
def settings() -> AmazonSettings:
    return AmazonSettings(
        AMAZON_DATA_SOURCE=AmazonDataSource.SPAPI,
        AMAZON_MARKETPLACE_ID="ATVPDKIKX0DER",
        SP_API_CLIENT_ID="test-id",
        SP_API_CLIENT_SECRET="test-secret",
        SP_API_REFRESH_TOKEN="test-refresh",
        AMAZON_AD_REGION="na",
    )


def test_get_campaign_success(settings: AmazonSettings) -> None:
    adapter = SpApiAdvertisingAdapter(settings)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "campaignId": 123456,
        "name": "Test Campaign",
        "state": "enabled",
        "dailyBudget": 50.0,
        "currencyCode": "USD",
        "startDate": "20260101",
    }
    mock_response.raise_for_status = MagicMock()

    with (
        patch("aeo_integrations.amazon.auth.get_access_token") as mock_auth,
        patch("aeo_integrations.amazon.spapi_adapter.requests.get") as mock_get,
    ):
        mock_auth.return_value = AmazonAccessToken(access_token="test-token", expires_in=3600)
        mock_get.return_value = mock_response

        campaign = adapter.get_campaign("123456")

    assert campaign.campaign_id == "123456"
    assert campaign.name == "Test Campaign"
    assert campaign.status == "enabled"
    assert campaign.daily_budget is not None
    assert float(campaign.daily_budget) == 50.0


def test_list_campaigns_success(settings: AmazonSettings) -> None:
    adapter = SpApiAdvertisingAdapter(settings)
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"campaignId": 1, "name": "Campaign A", "state": "enabled"},
        {"campaignId": 2, "name": "Campaign B", "state": "paused"},
    ]
    mock_response.raise_for_status = MagicMock()

    with (
        patch("aeo_integrations.amazon.auth.get_access_token") as mock_auth,
        patch("aeo_integrations.amazon.spapi_adapter.requests.get") as mock_get,
    ):
        mock_auth.return_value = AmazonAccessToken(access_token="test-token", expires_in=3600)
        mock_get.return_value = mock_response

        campaigns = adapter.list_campaigns(limit=10)

    assert len(campaigns) == 2
    assert campaigns[0].campaign_id == "1"
    assert campaigns[1].status == "paused"


def test_list_spend_snapshots_success(settings: AmazonSettings) -> None:
    adapter = SpApiAdvertisingAdapter(settings)
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "campaignId": 123,
            "date": "20260915",
            "cost": 25.50,
            "impressions": 1000,
            "clicks": 50,
            "attributedSales": 500.00,
        }
    ]
    mock_response.raise_for_status = MagicMock()

    with (
        patch("aeo_integrations.amazon.auth.get_access_token") as mock_auth,
        patch("aeo_integrations.amazon.spapi_adapter.requests.post") as mock_post,
    ):
        mock_auth.return_value = AmazonAccessToken(access_token="test-token", expires_in=3600)
        mock_post.return_value = mock_response

        snapshots = adapter.list_spend_snapshots(limit=10)

    assert len(snapshots) == 1
    assert snapshots[0].campaign_id == "123"
    assert snapshots[0].impressions == 1000
    assert snapshots[0].clicks == 50
    assert snapshots[0].spend is not None
    assert float(snapshots[0].spend) == 25.5
