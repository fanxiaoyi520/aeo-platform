"""Agent command console API — MV4-07 / MV1-01 registry exposure."""

from __future__ import annotations

from typing import Any

from aeo_shared.agent_catalog import get_default_registry
from aeo_shared.graph_catalog import get_graph_catalog
from aeo_shared.responses import success_response
from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


def _ok(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return success_response(data, request.state.request_id).model_dump()


@router.get("")
async def list_agents(request: Request) -> dict[str, Any]:
    """Return registered agents and sub-graph catalog for the command console."""
    registry = get_default_registry()
    agents = registry.to_catalog()
    graphs = [
        {
            "graph_id": graph.graph_id,
            "display_name": graph.display_name,
            "description": graph.description,
            "category": graph.category.value,
            "agent_ids": graph.agent_ids,
            "step_count": len(graph.agent_ids),
        }
        for graph in get_graph_catalog().values()
    ]
    active_count = sum(1 for item in agents if item.get("status") == "active")
    planned_count = sum(1 for item in agents if item.get("status") == "planned")
    payload = {
        "agents": agents,
        "graphs": graphs,
        "summary": {
            "total": len(agents),
            "active": active_count,
            "planned": planned_count,
        },
    }
    return _ok(request, payload)
