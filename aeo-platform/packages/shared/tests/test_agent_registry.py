"""Tests for MV1-01 agent registry and capability schema."""

from __future__ import annotations

import pytest
from aeo_shared.agent_catalog import get_default_registry, listing_graph_node_names
from aeo_shared.agent_registry import (
    AgentCategory,
    AgentDeclaration,
    AgentRegistry,
    RiskLevel,
)


def test_register_and_get_agent() -> None:
    registry = AgentRegistry()
    decl = AgentDeclaration(
        agent_id="demo_agent",
        display_name="Demo Agent",
        category=AgentCategory.LISTING,
        graph_node="demo",
    )
    registry.register(decl)
    loaded = registry.get("demo_agent")
    assert loaded.display_name == "Demo Agent"
    assert loaded.graph_node == "demo"


def test_register_duplicate_raises() -> None:
    registry = AgentRegistry()
    decl = AgentDeclaration(
        agent_id="dup",
        display_name="Dup",
        category=AgentCategory.LISTING,
    )
    registry.register(decl)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(decl)


def test_list_agents_filters_by_status() -> None:
    registry = AgentRegistry()
    registry.register(
        AgentDeclaration(
            agent_id="active_one",
            display_name="Active",
            category=AgentCategory.LISTING,
            status="active",
        )
    )
    registry.register(
        AgentDeclaration(
            agent_id="planned_one",
            display_name="Planned",
            category=AgentCategory.SELECTION,
            status="planned",
        )
    )
    active = registry.list_agents(status="active")
    assert {item.agent_id for item in active} == {"active_one"}


def test_default_registry_includes_listing_chain() -> None:
    registry = get_default_registry()
    listing_ids = {
        item.agent_id
        for item in registry.list_agents(category=AgentCategory.LISTING, status="active")
    }
    assert listing_ids == {
        "research_agent",
        "rules_agent",
        "generate_agent",
        "compliance_agent",
        "human_review",
        "review_agent",
    }


def test_default_registry_lists_future_mv_agents_as_planned() -> None:
    registry = get_default_registry()
    planned = registry.list_agents(status="planned")
    planned_ids = {item.agent_id for item in planned}
    assert "selection_agent" in planned_ids
    assert "ads_agent" in planned_ids
    assert "operations_agent" in planned_ids


def test_listing_graph_node_names_match_m03() -> None:
    nodes = listing_graph_node_names()
    assert nodes == {
        "research",
        "rules",
        "generate",
        "compliance",
        "human_review",
        "review",
    }


def test_compliance_agent_is_l1_risk() -> None:
    registry = get_default_registry()
    compliance = registry.get("compliance_agent")
    assert compliance.risk_level == RiskLevel.L1


def test_catalog_export_is_json_serializable() -> None:
    registry = get_default_registry()
    catalog = registry.to_catalog()
    assert len(catalog) >= 10
    assert all("agent_id" in item and "capabilities" in item for item in catalog)
