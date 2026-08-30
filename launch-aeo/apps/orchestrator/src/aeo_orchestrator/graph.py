"""LangGraph state graph — S3-01 skeleton; checkpoint wiring in S3-06."""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from aeo_orchestrator.nodes.compliance import compliance_node, route_after_compliance
from aeo_orchestrator.nodes.generate import generate_node
from aeo_orchestrator.nodes.research import research_node
from aeo_orchestrator.nodes.review import human_review_node, review_node
from aeo_orchestrator.nodes.rules import rules_node
from aeo_orchestrator.state import TaskState

HUMAN_REVIEW_NODE = "human_review"


def build_graph(
    *, checkpointer: MemorySaver | None = None
) -> CompiledStateGraph[TaskState, None, TaskState, TaskState]:
    """Compile the listing-generation graph with optional in-memory checkpoint."""
    builder = StateGraph(TaskState)

    builder.add_node("research", research_node)
    builder.add_node("rules", rules_node)
    builder.add_node("generate", generate_node)
    builder.add_node("compliance", compliance_node)
    builder.add_node(HUMAN_REVIEW_NODE, human_review_node)
    builder.add_node("review", review_node)

    builder.set_entry_point("research")
    builder.add_edge("research", "rules")
    builder.add_edge("rules", "generate")
    builder.add_edge("generate", "compliance")
    builder.add_conditional_edges(
        "compliance",
        route_after_compliance,
        {"generate": "generate", "human_review": HUMAN_REVIEW_NODE},
    )
    builder.add_edge(HUMAN_REVIEW_NODE, "review")
    builder.add_edge("review", END)

    memory = checkpointer or MemorySaver()
    return builder.compile(
        checkpointer=memory,
        interrupt_before=[HUMAN_REVIEW_NODE],
    )
