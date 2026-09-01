"""Tests for MV1-03 parent task multi-graph orchestration."""

from __future__ import annotations

import pytest
from aeo_shared.agent_catalog import build_default_registry, get_default_registry
from aeo_shared.agent_registry import AgentCategory
from aeo_shared.graph_catalog import SubGraphDefinition
from aeo_shared.multi_graph import MultiGraphOrchestrator, ParentTaskStatus
from aeo_shared.task_scheduler import AgentTaskScheduler, ScheduledTaskStatus


def _orchestrator() -> MultiGraphOrchestrator:
    registry = get_default_registry()
    scheduler = AgentTaskScheduler(registry)
    return MultiGraphOrchestrator(scheduler, registry)


def _run_child(scheduler: AgentTaskScheduler, child_task_id: str) -> None:
    claimed = scheduler.claim_next()
    assert claimed is not None
    assert claimed.task_id == child_task_id


def test_create_parent_for_listing_graph() -> None:
    orchestrator = _orchestrator()
    parent = orchestrator.create_parent("listing", payload={"sku": "SKU-001"})
    assert parent.status == ParentTaskStatus.PENDING
    assert parent.graph_id == "listing"
    assert parent.payload["sku"] == "SKU-001"


def test_start_dispatches_first_agent_with_parent_link() -> None:
    orchestrator = _orchestrator()
    parent = orchestrator.create_parent("listing", payload={"sku": "SKU-001"})
    child = orchestrator.start(parent.parent_id)

    assert child.agent_id == "research_agent"
    assert child.parent_task_id == parent.parent_id
    assert child.status == ScheduledTaskStatus.QUEUED
    assert orchestrator.get_parent(parent.parent_id).status == ParentTaskStatus.RUNNING


def test_advance_steps_through_listing_graph() -> None:
    orchestrator = _orchestrator()
    scheduler = orchestrator._scheduler  # noqa: SLF001
    parent = orchestrator.create_parent("listing", payload={"sku": "SKU-001"})
    child = orchestrator.start(parent.parent_id)
    _run_child(scheduler, child.task_id)

    expected_agents = [
        "rules_agent",
        "generate_agent",
        "compliance_agent",
        "human_review",
        "review_agent",
    ]
    for agent_id in expected_agents:
        next_step = orchestrator.advance(parent.parent_id, child.task_id, result={"ok": True})
        assert isinstance(next_step, type(child))
        child = next_step
        assert child.agent_id == agent_id
        _run_child(scheduler, child.task_id)

    completed = orchestrator.advance(parent.parent_id, child.task_id, result={"final": True})
    assert completed.status == ParentTaskStatus.COMPLETED
    assert orchestrator.list_children(parent.parent_id)
    assert len(orchestrator.list_children(parent.parent_id)) == 6


def test_start_twice_raises() -> None:
    orchestrator = _orchestrator()
    parent = orchestrator.create_parent("listing")
    orchestrator.start(parent.parent_id)
    with pytest.raises(ValueError, match="already started"):
        orchestrator.start(parent.parent_id)


def test_fail_parent_marks_child_failed() -> None:
    orchestrator = _orchestrator()
    scheduler = orchestrator._scheduler  # noqa: SLF001
    parent = orchestrator.create_parent("listing")
    child = orchestrator.start(parent.parent_id)
    _run_child(scheduler, child.task_id)

    failed = orchestrator.fail_parent(
        parent.parent_id, child_task_id=child.task_id, error_message="boom"
    )
    assert failed.status == ParentTaskStatus.FAILED
    assert scheduler.get(child.task_id).status == ScheduledTaskStatus.FAILED


def test_create_parent_rejects_unknown_graph() -> None:
    orchestrator = _orchestrator()
    with pytest.raises(KeyError, match="Sub-graph not found"):
        orchestrator.create_parent("missing_graph")


def test_custom_graph_definition() -> None:
    registry = build_default_registry()
    scheduler = AgentTaskScheduler(registry)
    mini_graph = SubGraphDefinition(
        graph_id="mini",
        display_name="Mini",
        category=AgentCategory.LISTING,
        agent_ids=["research_agent", "rules_agent"],
    )
    orchestrator = MultiGraphOrchestrator(scheduler, registry, graphs={"mini": mini_graph})
    parent = orchestrator.create_parent("mini")
    child = orchestrator.start(parent.parent_id)
    assert child.agent_id == "research_agent"


def test_create_parent_rejects_inactive_agent_in_graph() -> None:
    registry = build_default_registry()
    scheduler = AgentTaskScheduler(registry)
    bad_graph = SubGraphDefinition(
        graph_id="bad",
        display_name="Bad",
        category=AgentCategory.SELECTION,
        agent_ids=["selection_agent"],
    )
    orchestrator = MultiGraphOrchestrator(scheduler, registry, graphs={"bad": bad_graph})
    with pytest.raises(ValueError, match="not active"):
        orchestrator.create_parent("bad")
