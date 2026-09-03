"""MV2-02 acceptance tests — A01 Selection Agent end-to-end."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse

_AEO_PLATFORM_ROOT = Path(__file__).resolve().parents[3]

_SELECTION_ARTIFACTS = [
    "apps/orchestrator/src/aeo_orchestrator/nodes/selection.py",
    "apps/orchestrator/tests/test_selection.py",
]


@pytest.mark.parametrize("relative_path", _SELECTION_ARTIFACTS)
def test_mv2_02_artifacts_exist(relative_path: str) -> None:
    path = _AEO_PLATFORM_ROOT / relative_path
    assert path.is_file(), f"missing MV2-02 artifact: {relative_path}"


def test_selection_agent_active_in_registry() -> None:
    from aeo_shared import get_default_registry

    registry = get_default_registry()
    agent = registry.get("selection_agent")
    assert agent.status == "active"
    assert agent.graph_node == "selection"
    assert agent.category.value == "A01"
    capability_names = [c.name for c in agent.capabilities]
    assert "selection.score" in capability_names
    assert "selection.competitor_research" in capability_names
    assert "selection.report" in capability_names


def test_selection_subgraph_registered() -> None:
    from aeo_shared import get_subgraph

    graph = get_subgraph("selection")
    assert graph.graph_id == "selection"
    assert "selection_agent" in graph.agent_ids


def test_selection_graph_builds() -> None:
    from aeo_orchestrator.graph import build_selection_graph

    graph = build_selection_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_selection_graph_e2e() -> None:
    from aeo_orchestrator.graph import build_selection_graph
    from aeo_orchestrator.state import initial_state

    graph = build_selection_graph()
    state = initial_state(
        task_id="mv2-02-e2e",
        platform="amazon",
        sku="E2E-001",
        product_info={
            "title": "Bluetooth Speaker",
            "price": 39.99,
            "rating": 4.3,
            "review_count": 300,
            "category": "Electronics",
            "bullet_points": ["Waterproof", "12h battery"],
            "keywords": ["bluetooth speaker"],
            "images": ["speaker.jpg"],
            "competitors": [
                {"asin": "B100", "price": 35.0, "rating": 4.1, "review_count": 600},
                {"asin": "B101", "price": 45.0, "rating": 4.5, "review_count": 1200},
            ],
        },
    )

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(
        content="Strong market demand with moderate competition.",
        model="test",
    )

    with patch("aeo_orchestrator.nodes.selection.get_llm_provider", return_value=mock_provider):
        result = await graph.ainvoke(state, config={"configurable": {"thread_id": "mv2-02-e2e"}})

    selection = result.get("selection")
    assert selection is not None
    assert selection["sku"] == "E2E-001"
    assert 0 <= selection["total_score"] <= 100
    assert selection["competitor_count"] == 2
    assert selection["recommendation"] in ("proceed", "review", "skip")
    assert isinstance(selection["report"], str)
    assert len(selection["report"]) > 0

    trace = result.get("trace", [])
    agent_events = [e for e in trace if e["agent"] == "selection_agent"]
    assert len(agent_events) >= 2
    assert agent_events[0]["status"] == "started"
    assert agent_events[-1]["status"] == "completed"


@pytest.mark.asyncio
async def test_run_selection_task() -> None:
    from aeo_orchestrator.runner import run_selection_task

    mock_provider = AsyncMock()
    mock_provider.chat.return_value = LLMResponse(
        content="Good product candidate.",
        model="test",
    )

    with patch("aeo_orchestrator.nodes.selection.get_llm_provider", return_value=mock_provider):
        result = await run_selection_task(
            sku="RUN-001",
            product_info={
                "title": "USB Hub",
                "price": 19.99,
                "competitors": [
                    {"asin": "B200", "price": 22.0, "rating": 4.0, "review_count": 400},
                ],
            },
            task_id="runner-sel-1",
        )

    assert result["task_id"] == "runner-sel-1"
    assert result["selection"] is not None
    assert result["selection"]["sku"] == "RUN-001"


def test_serialize_selection_result() -> None:
    from aeo_orchestrator.runner import serialize_selection_result
    from aeo_orchestrator.state import initial_state

    state = initial_state(task_id="ser-1", platform="amazon", sku="SER-001")
    state["selection"] = {"total_score": 72.5, "recommendation": "review"}

    serialized = serialize_selection_result(state)
    assert serialized["task_id"] == "ser-1"
    assert serialized["sku"] == "SER-001"
    assert serialized["selection"]["total_score"] == 72.5


def test_selection_agent_in_graph_catalog() -> None:
    from aeo_shared import build_graph_catalog

    catalog = build_graph_catalog()
    assert "selection" in catalog
    assert "listing" in catalog
