"""LangGraph state graph — S3-06 HITL routing + pluggable checkpointer."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from aeo_orchestrator.checkpoint import create_memory_checkpointer
from aeo_orchestrator.nodes.compliance import compliance_node, route_after_compliance
from aeo_orchestrator.nodes.generate import generate_node
from aeo_orchestrator.nodes.image_copy import image_copy_node
from aeo_orchestrator.nodes.research import research_node
from aeo_orchestrator.nodes.review import human_review_node, review_node, route_after_human_review
from aeo_orchestrator.nodes.rules import rules_node
from aeo_orchestrator.nodes.selection import selection_node
from aeo_orchestrator.nodes.tiktok_video import tiktok_video_node
from aeo_orchestrator.state import TaskState

HUMAN_REVIEW_NODE = "human_review"


def build_graph(
    *, checkpointer: BaseCheckpointSaver[Any] | None = None
) -> CompiledStateGraph[TaskState, None, TaskState, TaskState]:
    """Compile the listing-generation graph with optional checkpoint backend."""
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
    builder.add_conditional_edges(
        HUMAN_REVIEW_NODE,
        route_after_human_review,
        {"generate": "generate", "review": "review"},
    )
    builder.add_edge("review", END)

    memory = checkpointer or create_memory_checkpointer()
    return builder.compile(
        checkpointer=memory,
        interrupt_before=[HUMAN_REVIEW_NODE],
    )


def build_selection_graph(
    *, checkpointer: BaseCheckpointSaver[Any] | None = None
) -> CompiledStateGraph[TaskState, None, TaskState, TaskState]:
    """Compile the selection analysis graph (single selection_agent node)."""
    builder = StateGraph(TaskState)
    builder.add_node("selection", selection_node)
    builder.set_entry_point("selection")
    builder.add_edge("selection", END)

    memory = checkpointer or create_memory_checkpointer()
    return builder.compile(checkpointer=memory)


def build_image_copy_graph(
    *, checkpointer: BaseCheckpointSaver[Any] | None = None
) -> CompiledStateGraph[TaskState, None, TaskState, TaskState]:
    """Compile the image copywriting graph (single image_copy node)."""
    builder = StateGraph(TaskState)
    builder.add_node("image_copy", image_copy_node)
    builder.set_entry_point("image_copy")
    builder.add_edge("image_copy", END)

    memory = checkpointer or create_memory_checkpointer()
    return builder.compile(checkpointer=memory)


def build_tiktok_video_graph(
    *, checkpointer: BaseCheckpointSaver[Any] | None = None
) -> CompiledStateGraph[TaskState, None, TaskState, TaskState]:
    """Compile the TikTok video script graph (single tiktok_video node)."""
    builder = StateGraph(TaskState)
    builder.add_node("tiktok_video", tiktok_video_node)
    builder.set_entry_point("tiktok_video")
    builder.add_edge("tiktok_video", END)

    memory = checkpointer or create_memory_checkpointer()
    return builder.compile(checkpointer=memory)
