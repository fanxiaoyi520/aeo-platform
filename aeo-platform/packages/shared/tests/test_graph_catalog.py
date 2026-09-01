"""Tests for MV1-03 graph catalog."""

from __future__ import annotations

import pytest
from aeo_shared.agent_catalog import get_default_registry, listing_graph_node_names
from aeo_shared.graph_catalog import get_graph_catalog, get_subgraph


def test_graph_catalog_includes_listing_graph() -> None:
    catalog = get_graph_catalog()
    assert "listing" in catalog
    listing = catalog["listing"]
    assert listing.graph_id == "listing"
    assert listing.agent_ids[0] == "research_agent"
    assert listing.agent_ids[-1] == "review_agent"


def test_listing_graph_agent_ids_match_registry_nodes() -> None:
    listing = get_subgraph("listing")
    registry = get_default_registry()
    node_names = listing_graph_node_names()
    for agent_id in listing.agent_ids:
        agent = registry.get(agent_id)
        assert agent.graph_node in node_names


def test_get_subgraph_unknown_raises() -> None:
    with pytest.raises(KeyError, match="Sub-graph not found"):
        get_subgraph("unknown_graph")
