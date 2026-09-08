"""MV3-02 acceptance tests — A02 Ads Agent end-to-end."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse


def test_ads_agent_active_in_registry() -> None:
    from aeo_shared import get_default_registry

    registry = get_default_registry()
    agent = registry.get("ads_agent")
    assert agent.status == "active"
    assert agent.graph_node == "ads"
    assert agent.category.value == "A02"
    capability_names = [c.name for c in agent.capabilities]
    assert "ads.analyze" in capability_names
    assert "ads.suggest" in capability_names


def test_ads_subgraph_registered() -> None:
    from aeo_shared import get_subgraph

    graph = get_subgraph("ads")
    assert graph.graph_id == "ads"
    assert "ads_agent" in graph.agent_ids


def test_ads_graph_builds() -> None:
    from aeo_orchestrator.graph import build_ads_graph

    graph = build_ads_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_ads_graph_e2e() -> None:
    from aeo_orchestrator.graph import build_ads_graph
    from aeo_orchestrator.state import initial_state

    graph = build_ads_graph()
    state = initial_state(
        task_id="mv3-02-e2e",
        platform="amazon",
        sku="HOMEBREW-KETTLE-1L",
        product_info={
            "title": "HomeBrew Electric Kettle 1L",
            "price": 29.99,
            "category": "Home & Kitchen",
        },
    )

    mock_llm_response = json.dumps(
        {
            "suggestions": [
                {
                    "campaign_id": "camp-001",
                    "type": "bid_increase",
                    "reason": "Low ACoS indicates room for higher bids",
                    "suggested_value": "12.00",
                },
                {
                    "campaign_id": "camp-003",
                    "type": "pause",
                    "reason": "High ACoS above 40% threshold",
                    "suggested_value": None,
                },
            ],
            "bid_simulation": {
                "campaign_id": "camp-001",
                "current_bid": "8.00",
                "suggested_bid": "12.00",
                "estimated_impression_lift": "25%",
                "estimated_gmv_change": "15%",
            },
            "report": "Campaign camp-001 shows strong ROI. Consider increasing bid.",
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(
        content=mock_llm_response,
        model="test",
    )

    with patch("aeo_orchestrator.nodes.ads.get_llm_provider", return_value=mock_provider):
        result = await graph.ainvoke(state, config={"configurable": {"thread_id": "mv3-02-e2e"}})

    ads = result.get("ads")
    assert ads is not None
    assert "campaigns" in ads
    assert "metrics" in ads
    assert "suggestions" in ads
    assert "bid_simulation" in ads
    assert "report" in ads

    assert len(ads["campaigns"]) >= 1
    assert ads["metrics"]["total_spend"] is not None
    assert ads["metrics"]["total_gmv"] is not None
    assert "avg_acos" in ads["metrics"]
    assert "avg_ctr" in ads["metrics"]

    assert len(ads["suggestions"]) >= 1
    assert ads["suggestions"][0]["campaign_id"] == "camp-001"
    assert ads["suggestions"][0]["type"] == "bid_increase"

    assert isinstance(ads["report"], str)
    assert len(ads["report"]) > 0

    trace = result.get("trace", [])
    agent_events = [e for e in trace if e["agent"] == "ads_agent"]
    assert len(agent_events) >= 2
    assert agent_events[0]["status"] == "started"
    assert agent_events[-1]["status"] == "completed"


@pytest.mark.asyncio
async def test_run_ads_task() -> None:
    from aeo_orchestrator.runner import run_ads_task

    mock_llm_response = json.dumps(
        {
            "suggestions": [],
            "bid_simulation": None,
            "report": "No significant optimization opportunities.",
        }
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(
        content=mock_llm_response,
        model="test",
    )

    with patch("aeo_orchestrator.nodes.ads.get_llm_provider", return_value=mock_provider):
        result = await run_ads_task(
            sku="HOMEBREW-KETTLE-1L",
            product_info={"title": "Electric Kettle", "price": 29.99},
            task_id="runner-ads-1",
        )

    assert result["task_id"] == "runner-ads-1"
    assert result["ads"] is not None


def test_serialize_ads_result() -> None:
    from aeo_orchestrator.runner import serialize_ads_result
    from aeo_orchestrator.state import initial_state

    state = initial_state(task_id="ser-ads", platform="amazon", sku="SER-001")
    state["ads"] = {
        "campaigns": [{"campaign_id": "camp-001"}],
        "metrics": {"total_spend": "50.00", "total_gmv": "200.00"},
        "suggestions": [],
        "report": "Test report",
    }

    serialized = serialize_ads_result(state)
    assert serialized["task_id"] == "ser-ads"
    assert serialized["sku"] == "SER-001"
    assert serialized["ads"]["metrics"]["total_spend"] == "50.00"
    assert len(serialized["ads"]["campaigns"]) == 1


def test_ads_node_metrics_calculation() -> None:
    from aeo_orchestrator.nodes.ads import calculate_campaign_metrics

    campaigns = [
        {
            "campaign_id": "camp-001",
            "name": "Test Campaign",
            "status": "enabled",
            "daily_budget": "15.00",
        }
    ]
    snapshots = [
        {
            "campaign_id": "camp-001",
            "spend": 12.50,
            "impressions": 3200,
            "clicks": 85,
            "attributed_gmv": 149.95,
        },
        {
            "campaign_id": "camp-001",
            "spend": 14.80,
            "impressions": 3800,
            "clicks": 102,
            "attributed_gmv": 179.90,
        },
    ]

    metrics = calculate_campaign_metrics(campaigns, snapshots)

    assert metrics["total_spend"] == pytest.approx(27.30, rel=1e-2)
    assert metrics["total_gmv"] == pytest.approx(329.85, rel=1e-2)
    assert metrics["avg_acos"] == pytest.approx(8.28, rel=1e-1)
    assert metrics["avg_ctr"] == pytest.approx(2.64, rel=1e-1)
    assert metrics["total_impressions"] == 7000
    assert metrics["total_clicks"] == 187


def test_ads_agent_in_graph_catalog() -> None:
    from aeo_shared import build_graph_catalog

    catalog = build_graph_catalog()
    assert "ads" in catalog
    assert "selection" in catalog
    assert "listing" in catalog
