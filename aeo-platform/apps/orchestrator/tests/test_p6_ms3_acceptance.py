"""P6-MS3 acceptance tests — SP-API fallback end-to-end through orchestrator nodes."""

from __future__ import annotations

import json
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest
import requests
from aeo_integrations.amazon.config import AmazonDataSource, AmazonSettings
from aeo_integrations.amazon.fallback import FallbackWrapper
from aeo_llm.provider import LLMResponse
from aeo_orchestrator.state import TaskState


@pytest.fixture
def spapi_fallback_settings() -> AmazonSettings:
    return AmazonSettings(
        AMAZON_DATA_SOURCE=AmazonDataSource.SPAPI,
        AMAZON_MARKETPLACE_ID="ATVPDKIKX0DER",
        SP_API_CLIENT_ID="test-id",
        SP_API_CLIENT_SECRET="test-secret",
        SP_API_REFRESH_TOKEN="test-refresh",
        AMAZON_FALLBACK_ENABLED=True,
    )


def _mock_llm(response_body: dict[str, object]) -> AsyncMock:
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(content=json.dumps(response_body), model="test")
    return mock_provider


def _mock_ads_llm() -> AsyncMock:
    return _mock_llm(
        {
            "suggestions": [
                {
                    "campaign_id": "CAMP-001",
                    "type": "bid_increase",
                    "reason": "Low ACoS",
                    "suggested_value": "1.50",
                }
            ],
            "bid_simulation": {
                "campaign_id": "CAMP-001",
                "current_bid": "1.00",
                "suggested_bid": "1.50",
                "estimated_impression_lift": "25%",
                "estimated_gmv_change": "15%",
            },
            "report": "Campaigns performing well.",
        }
    )


def _mock_ops_llm() -> AsyncMock:
    return _mock_llm(
        {
            "inventory_alerts": [{"sku": "SKU-001", "level": "warning", "message": "Low stock"}],
            "pricing_suggestions": [],
            "restock_recommendations": [],
            "report": "Inventory health acceptable.",
        }
    )


def _mock_support_llm() -> AsyncMock:
    return _mock_llm(
        {
            "reply_draft": "Thank you for your inquiry about your order.",
            "confidence": "high",
            "requires_human_review": False,
        }
    )


class TestFallbackIntegration:
    def test_listings_fallback_returns_mock_data(
        self, spapi_fallback_settings: AmazonSettings
    ) -> None:
        from aeo_integrations.amazon.listings import get_listings_client

        with patch(
            "aeo_integrations.amazon.spapi_adapter.SpApiListingsAdapter.get_listing",
            side_effect=requests.exceptions.ConnectionError("SP-API unavailable"),
        ):
            client = get_listings_client(spapi_fallback_settings)
            assert isinstance(client, FallbackWrapper)
            listing = client.get_listing("HOMEBREW-KETTLE-1L")
            assert listing.sku
            assert client.data_source == "spapi-degraded"

    def test_orders_fallback_returns_mock_data(
        self, spapi_fallback_settings: AmazonSettings
    ) -> None:
        from aeo_integrations.amazon.orders import get_orders_client

        with patch(
            "aeo_integrations.amazon.spapi_adapter.SpApiOrdersAdapter.list_orders",
            side_effect=requests.exceptions.ConnectionError("SP-API unavailable"),
        ):
            client = get_orders_client(spapi_fallback_settings)
            assert isinstance(client, FallbackWrapper)
            orders = client.list_orders()
            assert isinstance(orders, list)
            assert client.data_source == "spapi-degraded"

    def test_advertising_fallback_returns_mock_data(
        self, spapi_fallback_settings: AmazonSettings
    ) -> None:
        from aeo_integrations.amazon.advertising import get_advertising_client

        with patch(
            "aeo_integrations.amazon.spapi_adapter.SpApiAdvertisingAdapter.list_campaigns",
            side_effect=requests.exceptions.ConnectionError("SP-API unavailable"),
        ):
            client = get_advertising_client(spapi_fallback_settings)
            assert isinstance(client, FallbackWrapper)
            campaigns = client.list_campaigns()
            assert isinstance(campaigns, list)
            assert client.data_source == "spapi-degraded"

    def test_inventory_fallback_returns_mock_data(
        self, spapi_fallback_settings: AmazonSettings
    ) -> None:
        from aeo_integrations.amazon.inventory import get_inventory_client

        with patch(
            "aeo_integrations.amazon.spapi_adapter.SpApiInventoryAdapter.list_inventory",
            side_effect=requests.exceptions.ConnectionError("SP-API unavailable"),
        ):
            client = get_inventory_client(spapi_fallback_settings)
            assert isinstance(client, FallbackWrapper)
            inventory = client.list_inventory()
            assert isinstance(inventory, list)
            assert client.data_source == "spapi-degraded"


class TestResearchNodeFallback:
    @pytest.mark.asyncio
    async def test_research_node_with_spapi_fallback(
        self, spapi_fallback_settings: AmazonSettings
    ) -> None:
        from aeo_orchestrator.nodes.research import research_node

        with (
            patch(
                "aeo_integrations.amazon.config.get_amazon_settings",
                return_value=spapi_fallback_settings,
            ),
            patch(
                "aeo_integrations.amazon.spapi_adapter.SpApiListingsAdapter.get_listing",
                side_effect=requests.exceptions.ConnectionError("SP-API unavailable"),
            ),
        ):
            state: TaskState = {
                "sku": "HOMEBREW-KETTLE-1L",
                "task_id": "p6-23-research-001",
                "platform": "amazon",
                "market": "US",
                "product_info": {"title": "Test Product"},
            }
            result = await research_node(state)

        assert "product_info" in result
        assert "research" in result
        research = cast("dict[str, Any]", result["research"])
        assert research["amazon_listing_loaded"] is True
        assert "keywords" in research


class TestAdsNodeFallback:
    @pytest.mark.asyncio
    async def test_ads_node_with_spapi_fallback(
        self, spapi_fallback_settings: AmazonSettings
    ) -> None:
        from aeo_orchestrator.nodes.ads import ads_node

        mock_provider = _mock_ads_llm()
        with (
            patch(
                "aeo_integrations.amazon.config.get_amazon_settings",
                return_value=spapi_fallback_settings,
            ),
            patch(
                "aeo_integrations.amazon.spapi_adapter.SpApiAdvertisingAdapter.list_campaigns",
                side_effect=requests.exceptions.ConnectionError("SP-API unavailable"),
            ),
            patch(
                "aeo_integrations.amazon.spapi_adapter.SpApiAdvertisingAdapter.list_spend_snapshots",
                side_effect=requests.exceptions.ConnectionError("SP-API unavailable"),
            ),
            patch(
                "aeo_orchestrator.nodes.ads.get_llm_provider",
                return_value=mock_provider,
            ),
        ):
            state: TaskState = {
                "sku": "SKU-001",
                "task_id": "p6-23-ads-001",
                "platform": "amazon",
                "product_info": {"title": "Test Product", "price": 29.99},
            }
            result = await ads_node(state)

        ads = cast("dict[str, Any]", result["ads"])
        assert "campaigns" in ads
        assert "metrics" in ads
        assert "suggestions" in ads
        assert "report" in ads
        assert isinstance(ads["campaigns"], list)
        assert len(ads["campaigns"]) > 0


class TestOpsNodeFallback:
    @pytest.mark.asyncio
    async def test_ops_node_with_spapi_fallback(
        self, spapi_fallback_settings: AmazonSettings
    ) -> None:
        from aeo_orchestrator.nodes.operations import operations_node

        mock_provider = _mock_ops_llm()
        with (
            patch(
                "aeo_integrations.amazon.config.get_amazon_settings",
                return_value=spapi_fallback_settings,
            ),
            patch(
                "aeo_integrations.amazon.spapi_adapter.SpApiInventoryAdapter.list_inventory",
                side_effect=requests.exceptions.ConnectionError("SP-API unavailable"),
            ),
            patch(
                "aeo_orchestrator.nodes.operations.get_llm_provider",
                return_value=mock_provider,
            ),
        ):
            state: TaskState = {
                "sku": "SKU-001",
                "task_id": "p6-23-ops-001",
                "platform": "amazon",
                "product_info": {"title": "Test Product", "price": 19.99},
            }
            result = await operations_node(state)

        ops = cast("dict[str, Any]", result["ops"])
        assert "inventory" in ops
        assert "health_metrics" in ops
        assert "report" in ops
        assert isinstance(ops["inventory"], list)
        assert len(ops["inventory"]) > 0
        health = ops["health_metrics"]
        assert "total_available" in health
        assert "item_count" in health


class TestSupportNodeFallback:
    @pytest.mark.asyncio
    async def test_support_node_with_spapi_fallback(
        self, spapi_fallback_settings: AmazonSettings
    ) -> None:
        from aeo_orchestrator.nodes.support import support_node

        mock_provider = _mock_support_llm()
        with (
            patch(
                "aeo_integrations.amazon.config.get_amazon_settings",
                return_value=spapi_fallback_settings,
            ),
            patch(
                "aeo_integrations.amazon.spapi_adapter.SpApiOrdersAdapter.list_orders",
                side_effect=requests.exceptions.ConnectionError("SP-API unavailable"),
            ),
            patch(
                "aeo_orchestrator.nodes.support.get_llm_provider",
                return_value=mock_provider,
            ),
            patch(
                "aeo_orchestrator.nodes.support._search_rag",
                return_value=[],
            ),
        ):
            state: TaskState = {
                "sku": "SKU-001",
                "task_id": "p6-23-support-001",
                "platform": "amazon",
                "product_info": {"title": "Test Product"},
            }
            result = await support_node(state)

        support = cast("dict[str, Any]", result["support"])
        assert "reply_draft" in support
        assert "order_context" in support
        assert "escalation" in support
        assert "confidence" in support
        assert isinstance(support["reply_draft"], str)


class TestMockModeRegression:
    def test_mock_mode_listings(self) -> None:
        from aeo_integrations.amazon.listings import MockListingsAdapter, get_listings_client

        mock_settings = AmazonSettings(AMAZON_DATA_SOURCE=AmazonDataSource.MOCK)
        client = get_listings_client(mock_settings)
        assert isinstance(client, MockListingsAdapter)
        assert client.data_source == "mock"
        listing = client.get_listing("HOMEBREW-KETTLE-1L")
        assert listing.sku

    def test_mock_mode_orders(self) -> None:
        from aeo_integrations.amazon.orders import MockOrdersAdapter, get_orders_client

        mock_settings = AmazonSettings(AMAZON_DATA_SOURCE=AmazonDataSource.MOCK)
        client = get_orders_client(mock_settings)
        assert isinstance(client, MockOrdersAdapter)
        assert client.data_source == "mock"
        orders = client.list_orders()
        assert isinstance(orders, list)

    def test_mock_mode_advertising(self) -> None:
        from aeo_integrations.amazon.advertising import (
            MockAdvertisingAdapter,
            get_advertising_client,
        )

        mock_settings = AmazonSettings(AMAZON_DATA_SOURCE=AmazonDataSource.MOCK)
        client = get_advertising_client(mock_settings)
        assert isinstance(client, MockAdvertisingAdapter)
        assert client.data_source == "mock"
        campaigns = client.list_campaigns()
        assert isinstance(campaigns, list)

    def test_mock_mode_inventory(self) -> None:
        from aeo_integrations.amazon.inventory import (
            MockInventoryAdapter,
            get_inventory_client,
        )

        mock_settings = AmazonSettings(AMAZON_DATA_SOURCE=AmazonDataSource.MOCK)
        client = get_inventory_client(mock_settings)
        assert isinstance(client, MockInventoryAdapter)
        assert client.data_source == "mock"
        inventory = client.list_inventory()
        assert isinstance(inventory, list)


class TestDataSourceMarking:
    def test_spapi_degraded_marking(self, spapi_fallback_settings: AmazonSettings) -> None:
        from aeo_integrations.amazon.listings import get_listings_client

        with patch(
            "aeo_integrations.amazon.spapi_adapter.SpApiListingsAdapter.get_listing",
            side_effect=requests.exceptions.ConnectionError("SP-API unavailable"),
        ):
            client = get_listings_client(spapi_fallback_settings)
            assert client.data_source == "spapi"  # type: ignore[attr-defined]
            client.get_listing("HOMEBREW-KETTLE-1L")
            assert client.data_source == "spapi-degraded"  # type: ignore[attr-defined]

    def test_spapi_recovery_marking(self, spapi_fallback_settings: AmazonSettings) -> None:
        from aeo_integrations.amazon.listings import get_listings_client
        from aeo_integrations.amazon.models import AmazonListing

        call_count = 0

        def side_effect(*args: object, **kwargs: object) -> AmazonListing:
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise requests.exceptions.ConnectionError("SP-API unavailable")
            return AmazonListing(
                sku="HOMEBREW-KETTLE-1L",
                seller_sku="HOMEBREW-KETTLE-1L",
                asin="B001",
                marketplace_id="ATVPDKIKX0DER",
                status="ACTIVE",
                title="Test",
                brand="TestBrand",
            )

        with patch(
            "aeo_integrations.amazon.spapi_adapter.SpApiListingsAdapter.get_listing",
            side_effect=side_effect,
        ):
            client = get_listings_client(spapi_fallback_settings)
            client.get_listing("HOMEBREW-KETTLE-1L")
            assert client.data_source == "spapi-degraded"  # type: ignore[attr-defined]
            client.get_listing("HOMEBREW-KETTLE-1L")
            assert client.data_source == "spapi"  # type: ignore[attr-defined]
