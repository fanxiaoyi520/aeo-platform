"""Default agent catalog — listing chain (active) + MV stubs (planned)."""

from __future__ import annotations

from functools import lru_cache

from aeo_shared.agent_registry import (
    AgentCapability,
    AgentCategory,
    AgentDeclaration,
    AgentRegistry,
    RiskLevel,
)

_LISTING_AGENTS: tuple[AgentDeclaration, ...] = (
    AgentDeclaration(
        agent_id="research_agent",
        display_name="Research Agent",
        category=AgentCategory.LISTING,
        description="Competitor research and keyword expansion.",
        capabilities=[
            AgentCapability(
                name="research.competitors",
                description="Parse and enrich competitor ASINs.",
                tools=["browser.fetch_listing", "integrations.listings"],
            ),
            AgentCapability(
                name="research.keywords",
                description="Baseline and LLM-expanded keywords.",
                tools=["llm.chat"],
            ),
        ],
        graph_node="research",
        timeout_seconds=120,
    ),
    AgentDeclaration(
        agent_id="rules_agent",
        display_name="Rules Agent",
        category=AgentCategory.LISTING,
        description="Platform rules and product knowledge retrieval.",
        capabilities=[
            AgentCapability(
                name="rules.retrieve",
                description="RAG search for listing rules and product docs.",
                tools=["rag.search"],
            ),
        ],
        graph_node="rules",
        timeout_seconds=30,
    ),
    AgentDeclaration(
        agent_id="generate_agent",
        display_name="Generate Agent",
        category=AgentCategory.LISTING,
        description="LLM listing draft generation.",
        capabilities=[
            AgentCapability(
                name="generate.listing",
                description="Produce title, bullets, and search terms.",
                tools=["llm.chat"],
            ),
        ],
        graph_node="generate",
        timeout_seconds=60,
    ),
    AgentDeclaration(
        agent_id="compliance_agent",
        display_name="Compliance Agent",
        category=AgentCategory.LISTING,
        description="Listing compliance validation and auto-fix loop.",
        capabilities=[
            AgentCapability(
                name="compliance.validate",
                description="Validate generated listing against platform rules.",
                tools=[],
            ),
        ],
        risk_level=RiskLevel.L1,
        graph_node="compliance",
        timeout_seconds=30,
    ),
    AgentDeclaration(
        agent_id="human_review",
        display_name="Human Review",
        category=AgentCategory.LISTING,
        description="HITL checkpoint before finalization.",
        capabilities=[
            AgentCapability(
                name="hitl.review",
                description="Pause for operator approve/reject.",
                tools=[],
            ),
        ],
        risk_level=RiskLevel.L1,
        graph_node="human_review",
        timeout_seconds=0,
    ),
    AgentDeclaration(
        agent_id="review_agent",
        display_name="Review Agent",
        category=AgentCategory.LISTING,
        description="Finalize listing output and metrics snapshot.",
        capabilities=[
            AgentCapability(
                name="review.finalize",
                description="Persist approved listing version.",
                tools=["db.save_listing_version"],
            ),
        ],
        graph_node="review",
        timeout_seconds=30,
    ),
    AgentDeclaration(
        agent_id="selection_agent",
        display_name="Selection Agent",
        category=AgentCategory.SELECTION,
        description="Market research, competitor analysis, and SKU selection scoring.",
        capabilities=[
            AgentCapability(
                name="selection.score",
                description="Score product candidates using 4-dimension model.",
                tools=["scoring.score_product"],
            ),
            AgentCapability(
                name="selection.competitor_research",
                description="Analyze competitor pool and market signals.",
                tools=["integrations.competitors"],
            ),
            AgentCapability(
                name="selection.report",
                description="Generate selection analysis report with recommendation.",
                tools=["llm.chat"],
            ),
        ],
        risk_level=RiskLevel.L1,
        graph_node="selection",
        timeout_seconds=90,
    ),
    AgentDeclaration(
        agent_id="image_copy_agent",
        display_name="Image Copy Agent",
        category=AgentCategory.LISTING,
        description="Main image callouts and scene image copywriting.",
        capabilities=[
            AgentCapability(
                name="generate.image_copy",
                description="Produce main image callouts, badge text, and scene image copy.",
                tools=["llm.chat"],
            ),
        ],
        timeout_seconds=60,
    ),
    AgentDeclaration(
        agent_id="tiktok_video_agent",
        display_name="TikTok Video Agent",
        category=AgentCategory.LISTING,
        description="TikTok short video script and storyboard generation.",
        capabilities=[
            AgentCapability(
                name="generate.tiktok_video",
                description="Produce video script and shot-by-shot storyboard.",
                tools=["llm.chat"],
            ),
        ],
        platforms=["tiktok"],
        timeout_seconds=60,
    ),
)

_MV_PLANNED_AGENTS: tuple[AgentDeclaration, ...] = (
    AgentDeclaration(
        agent_id="ads_agent",
        display_name="Ads Agent",
        category=AgentCategory.ADS,
        description="Campaign structure and bid recommendations.",
        status="planned",
        risk_level=RiskLevel.L1,
    ),
    AgentDeclaration(
        agent_id="operations_agent",
        display_name="Operations Agent",
        category=AgentCategory.OPERATIONS,
        description="Inventory and listing health monitoring.",
        status="planned",
        risk_level=RiskLevel.L1,
    ),
    AgentDeclaration(
        agent_id="support_agent",
        display_name="Support Agent",
        category=AgentCategory.SUPPORT,
        description="Customer message triage and draft replies.",
        status="planned",
        risk_level=RiskLevel.L1,
    ),
    AgentDeclaration(
        agent_id="analytics_agent",
        display_name="Analytics Agent",
        category=AgentCategory.ANALYTICS,
        description="GMV/ROI reporting and strategy iteration.",
        status="planned",
        risk_level=RiskLevel.L0,
    ),
)


def build_default_registry() -> AgentRegistry:
    registry = AgentRegistry()
    for declaration in (*_LISTING_AGENTS, *_MV_PLANNED_AGENTS):
        registry.register(declaration)
    return registry


@lru_cache
def get_default_registry() -> AgentRegistry:
    return build_default_registry()


def listing_graph_node_names() -> set[str]:
    registry = get_default_registry()
    return {
        item.graph_node
        for item in registry.list_agents(category=AgentCategory.LISTING, status="active")
        if item.graph_node
    }
