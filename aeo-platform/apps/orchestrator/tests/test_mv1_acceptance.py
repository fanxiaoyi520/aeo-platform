"""MV1-09 acceptance — 3 Agent chain (generate → compliance → review) + audit trail."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest
from aeo_llm.provider import LLMResponse
from aeo_orchestrator.nodes.compliance import compliance_node, validate_generated
from aeo_orchestrator.nodes.generate import generate_node
from aeo_orchestrator.nodes.review import review_node
from aeo_orchestrator.state import AgentTraceStatus, TaskState, TaskStatus

_LLM_PATCH = "aeo_orchestrator.nodes.generate.get_llm_provider"

_VALID_LISTING_JSON = """{
  "title": "Premium Wireless Earbuds Bluetooth 5.3 Noise Cancelling",
  "bullets": [
    "Active Noise Cancelling for immersive audio experience",
    "Bluetooth 5.3 with stable connection and low latency",
    "32 hours total playtime with charging case",
    "IPX5 water resistant for workouts and outdoor use",
    "Comfortable fit with three ear tip sizes included"
  ],
  "search_terms": "wireless earbuds bluetooth noise cancelling",
  "description": "Premium wireless earbuds with hybrid ANC technology."
}"""


def _mock_llm(content: str) -> AsyncMock:
    provider = AsyncMock()
    provider.chat.return_value = LLMResponse(content=content, model="test")
    return provider


def _base_state(task_id: str = "mv1-09-test") -> TaskState:
    return {
        "task_id": task_id,
        "platform": "amazon",
        "sku": "DEMO-001",
        "market": "US",
        "product_info": {"keywords": ["wireless earbuds"]},
        "research": None,
        "rules": {"rule_summary": "No HTML, max 200 chars title, 5 bullets required"},
        "generated": None,
        "compliance": None,
        "human_feedback": None,
        "final_output": None,
        "retry_count": 0,
        "degraded_mode": False,
        "trace": [],
        "status": TaskStatus.RUNNING,
    }


class TestMV1_09_ThreeAgentChain:
    """MV1-09: 3 Agent chain acceptance tests."""

    @pytest.mark.asyncio
    async def test_generate_agent_produces_valid_listing(self) -> None:
        """generate_agent should produce valid listing JSON."""
        state = _base_state()
        mock = _mock_llm(_VALID_LISTING_JSON)

        with patch(_LLM_PATCH, return_value=mock):
            result = await generate_node(state)

        generated = result.get("generated")
        assert isinstance(generated, dict)
        assert generated.get("title")
        assert len(cast(list[str], generated.get("bullets", []))) == 5
        assert generated.get("platform") == "amazon"

        trace = result.get("trace", [])
        assert any(
            isinstance(e, dict) and e.get("agent") == "generate_agent"
            for e in cast("list[dict[str, Any]]", trace)
        )

    @pytest.mark.asyncio
    async def test_compliance_agent_validates_listing(self) -> None:
        """compliance_agent should validate and pass valid listing."""
        state = _base_state()
        state["generated"] = {
            "title": "Valid Product Title",
            "bullets": ["Bullet 1", "Bullet 2", "Bullet 3", "Bullet 4", "Bullet 5"],
            "search_terms": "product keywords",
            "description": "Product description",
            "platform": "amazon",
        }

        result = await compliance_node(state)

        compliance = result.get("compliance")
        assert isinstance(compliance, dict)
        assert compliance.get("passed") is True
        assert compliance.get("issues") == []

    @pytest.mark.asyncio
    async def test_compliance_agent_detects_and_fixes_forbidden_phrases(self) -> None:
        """compliance_agent should detect and auto-fix forbidden phrases."""
        state = _base_state()
        state["generated"] = {
            "title": "BEST free shipping product",
            "bullets": ["Bullet 1", "Bullet 2", "Bullet 3", "Bullet 4", "Bullet 5"],
            "search_terms": "",
            "description": "",
            "platform": "amazon",
        }

        passed, issues = validate_generated(
            cast(dict[str, Any], state["generated"]),
            platform="amazon",
        )

        assert passed is False
        assert any(issue.get("code") == "forbidden_phrase" for issue in issues)

        result = await compliance_node(state)
        compliance = result.get("compliance")
        assert isinstance(compliance, dict)
        fixed = compliance.get("fixed_output", {})
        assert "best" not in str(fixed.get("title", "")).lower()
        assert "free shipping" not in str(fixed.get("title", "")).lower()

    @pytest.mark.asyncio
    async def test_review_agent_persists_listing(self) -> None:
        """review_agent should persist listing version."""
        state = _base_state()
        state["generated"] = {
            "title": "Final Product Title",
            "bullets": ["B1", "B2", "B3", "B4", "B5"],
            "search_terms": "keywords",
            "description": "Description",
            "platform": "amazon",
        }
        state["compliance"] = {"passed": True, "issues": []}

        result = await review_node(state)

        assert result.get("status") == TaskStatus.COMPLETED
        final_output = result.get("final_output")
        assert isinstance(final_output, dict)
        assert final_output.get("title") == "Final Product Title"

        metrics = cast("dict[str, Any]", final_output.get("metrics", {}))
        assert metrics.get("compliance_passed") is True
        assert metrics.get("listing_version") is not None

    @pytest.mark.asyncio
    async def test_full_chain_generate_compliance_review(self) -> None:
        """Full 3 Agent chain: generate → compliance → review."""
        state = _base_state(task_id="mv1-09-chain")
        mock = _mock_llm(_VALID_LISTING_JSON)

        all_trace: list[dict[str, Any]] = []

        with patch(_LLM_PATCH, return_value=mock):
            gen_result = await generate_node(state)

        cast(Any, state).update({k: v for k, v in gen_result.items() if k != "trace"})
        all_trace.extend(cast("list[dict[str, Any]]", gen_result.get("trace", [])))

        comp_result = await compliance_node(state)
        cast(Any, state).update({k: v for k, v in comp_result.items() if k != "trace"})
        all_trace.extend(cast("list[dict[str, Any]]", comp_result.get("trace", [])))

        compliance = state.get("compliance")
        assert isinstance(compliance, dict)
        assert compliance.get("passed") is True

        review_result = await review_node(state)
        all_trace.extend(cast("list[dict[str, Any]]", review_result.get("trace", [])))

        assert review_result.get("status") == TaskStatus.COMPLETED
        final_output = review_result.get("final_output")
        assert isinstance(final_output, dict)

        metrics = cast("dict[str, Any]", final_output.get("metrics", {}))
        assert metrics.get("listing_version") is not None

        agents_in_trace = {
            e.get("agent") for e in all_trace if isinstance(e, dict) and e.get("agent")
        }
        assert "generate_agent" in agents_in_trace
        assert "compliance_agent" in agents_in_trace
        assert "review_agent" in agents_in_trace


class TestMV1_09_AuditTrail:
    """MV1-09: Audit trail verification."""

    def test_trace_events_have_required_fields(self) -> None:
        """Trace events should have agent, status, timestamp fields."""
        from aeo_orchestrator.state import make_trace_event

        event = make_trace_event(
            "test_agent",
            AgentTraceStatus.COMPLETED,
            detail={"key": "value"},
        )

        assert event.get("agent") == "test_agent"
        assert event.get("status") == AgentTraceStatus.COMPLETED.value
        assert event.get("timestamp") is not None
        assert event.get("detail") == {"key": "value"}

    @pytest.mark.asyncio
    async def test_chain_produces_queryable_trace(self) -> None:
        """3 Agent chain should produce queryable trace."""
        state = _base_state(task_id="mv1-09-trace")
        mock = _mock_llm(_VALID_LISTING_JSON)

        all_trace: list[dict[str, Any]] = []

        with patch(_LLM_PATCH, return_value=mock):
            gen_result = await generate_node(state)
            all_trace.extend(cast("list[dict[str, Any]]", gen_result.get("trace", [])))

        state["generated"] = cast("dict[str, Any] | None", gen_result.get("generated"))
        comp_result = await compliance_node(state)
        all_trace.extend(cast("list[dict[str, Any]]", comp_result.get("trace", [])))

        state["compliance"] = cast("dict[str, Any] | None", comp_result.get("compliance"))
        review_result = await review_node(state)
        all_trace.extend(cast("list[dict[str, Any]]", review_result.get("trace", [])))

        assert len(all_trace) >= 3

        agent_events = [e for e in all_trace if e.get("agent")]
        assert len(agent_events) >= 3

        for event in agent_events:
            assert "agent" in event
            assert "status" in event
            assert "timestamp" in event
