"""MV1-03 — sub-graph definitions mapped to registered agents."""

from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel, Field

from aeo_shared.agent_registry import AgentCategory


class SubGraphDefinition(BaseModel):
    """Ordered agent chain for a LangGraph-style workflow."""

    graph_id: str
    display_name: str
    agent_ids: list[str] = Field(min_length=1)
    category: AgentCategory
    description: str = ""


_LISTING_GRAPH = SubGraphDefinition(
    graph_id="listing",
    display_name="Listing Generation",
    description="Research → rules → generate → compliance → HITL → review.",
    category=AgentCategory.LISTING,
    agent_ids=[
        "research_agent",
        "rules_agent",
        "generate_agent",
        "compliance_agent",
        "human_review",
        "review_agent",
    ],
)

_SELECTION_GRAPH = SubGraphDefinition(
    graph_id="selection",
    display_name="Selection Analysis",
    description="Competitor research → scoring → recommendation report.",
    category=AgentCategory.SELECTION,
    agent_ids=["selection_agent"],
)

_IMAGE_COPY_GRAPH = SubGraphDefinition(
    graph_id="image_copy",
    display_name="Image Copywriting",
    description="Main image callouts + scene image lifestyle copy.",
    category=AgentCategory.LISTING,
    agent_ids=["image_copy_agent"],
)

_TIKTOK_VIDEO_GRAPH = SubGraphDefinition(
    graph_id="tiktok_video",
    display_name="TikTok Video Script",
    description="Short video script + shot-by-shot storyboard for TikTok Shop.",
    category=AgentCategory.LISTING,
    agent_ids=["tiktok_video_agent"],
)

_SELECTION_TO_CONTENT_GRAPH = SubGraphDefinition(
    graph_id="selection_to_content",
    display_name="Selection to Content Pipeline",
    description="Full pipeline: selection → listing → image copy → TikTok video.",
    category=AgentCategory.LISTING,
    agent_ids=[
        "selection_agent",
        "research_agent",
        "rules_agent",
        "generate_agent",
        "compliance_agent",
        "human_review",
        "review_agent",
        "image_copy_agent",
        "tiktok_video_agent",
    ],
)

_ADS_GRAPH = SubGraphDefinition(
    graph_id="ads",
    display_name="Ads Analysis",
    description="Campaign performance analysis + bid/structure optimization suggestions.",
    category=AgentCategory.ADS,
    agent_ids=["ads_agent"],
)

_OPS_GRAPH = SubGraphDefinition(
    graph_id="ops",
    display_name="Operations Analysis",
    description="Inventory health monitoring + pricing/restock recommendations.",
    category=AgentCategory.OPERATIONS,
    agent_ids=["operations_agent"],
)

_SUPPORT_GRAPH = SubGraphDefinition(
    graph_id="support",
    display_name="Support Agent",
    description="Customer service reply drafts using RAG + order context.",
    category=AgentCategory.SUPPORT,
    agent_ids=["support_agent"],
)

_ANALYTICS_GRAPH = SubGraphDefinition(
    graph_id="analytics",
    display_name="Analytics Agent",
    description="Daily/weekly business review reports with strategy suggestions.",
    category=AgentCategory.ANALYTICS,
    agent_ids=["analytics_agent"],
)

_GRAPH_CATALOG: dict[str, SubGraphDefinition] = {
    _LISTING_GRAPH.graph_id: _LISTING_GRAPH,
    _SELECTION_GRAPH.graph_id: _SELECTION_GRAPH,
    _IMAGE_COPY_GRAPH.graph_id: _IMAGE_COPY_GRAPH,
    _TIKTOK_VIDEO_GRAPH.graph_id: _TIKTOK_VIDEO_GRAPH,
    _SELECTION_TO_CONTENT_GRAPH.graph_id: _SELECTION_TO_CONTENT_GRAPH,
    _ADS_GRAPH.graph_id: _ADS_GRAPH,
    _OPS_GRAPH.graph_id: _OPS_GRAPH,
    _SUPPORT_GRAPH.graph_id: _SUPPORT_GRAPH,
    _ANALYTICS_GRAPH.graph_id: _ANALYTICS_GRAPH,
}


def build_graph_catalog() -> dict[str, SubGraphDefinition]:
    return dict(_GRAPH_CATALOG)


@lru_cache
def get_graph_catalog() -> dict[str, SubGraphDefinition]:
    return build_graph_catalog()


def get_subgraph(graph_id: str) -> SubGraphDefinition:
    try:
        return get_graph_catalog()[graph_id]
    except KeyError as exc:
        msg = f"Sub-graph not found: {graph_id}"
        raise KeyError(msg) from exc
