"""Validate listing graph nodes against MV1-01 agent registry."""

from aeo_orchestrator.agent_registry import validate_listing_graph
from aeo_orchestrator.graph import HUMAN_REVIEW_NODE, build_graph


def test_listing_graph_matches_agent_registry() -> None:
    graph = build_graph()
    node_names = set(graph.nodes.keys())
    missing = validate_listing_graph(node_names)
    assert missing == [], f"Graph missing registered nodes: {missing}"
    assert HUMAN_REVIEW_NODE in node_names
