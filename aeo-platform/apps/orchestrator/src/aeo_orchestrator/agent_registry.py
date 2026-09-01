"""Orchestrator integration with MV1-01 agent registry."""

from __future__ import annotations

from aeo_shared.agent_catalog import get_default_registry, listing_graph_node_names

__all__ = ["get_default_registry", "listing_graph_node_names", "validate_listing_graph"]


def validate_listing_graph(node_names: set[str]) -> list[str]:
    """Return graph node names missing from the active listing agent catalog."""
    expected = listing_graph_node_names()
    return sorted(expected - node_names)
