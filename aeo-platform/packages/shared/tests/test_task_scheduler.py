"""Tests for MV1-02 cross-agent task scheduler."""

from __future__ import annotations

import pytest
from aeo_shared.agent_catalog import get_default_registry
from aeo_shared.agent_registry import AgentCategory, AgentDeclaration, AgentRegistry
from aeo_shared.task_scheduler import (
    AgentTaskScheduler,
    ScheduledTaskStatus,
    SchedulerConfig,
    TaskPriority,
)


def _scheduler(
    *,
    max_global: int = 10,
    default_per_agent: int = 2,
    per_agent: dict[str, int] | None = None,
) -> AgentTaskScheduler:
    return AgentTaskScheduler(
        get_default_registry(),
        config=SchedulerConfig(
            max_concurrent_global=max_global,
            default_max_concurrent_per_agent=default_per_agent,
            max_concurrent_per_agent=per_agent or {},
        ),
    )


def test_enqueue_active_listing_agent() -> None:
    scheduler = _scheduler()
    task = scheduler.enqueue("research_agent", capability="research.competitors")
    assert task.agent_id == "research_agent"
    assert task.status == ScheduledTaskStatus.QUEUED
    assert task.capability == "research.competitors"


def test_enqueue_rejects_planned_agent() -> None:
    scheduler = _scheduler()
    with pytest.raises(ValueError, match="not active"):
        scheduler.enqueue("selection_agent")


def test_enqueue_rejects_unknown_capability() -> None:
    scheduler = _scheduler()
    with pytest.raises(ValueError, match="Capability not declared"):
        scheduler.enqueue("research_agent", capability="research.unknown")


def test_claim_next_respects_priority() -> None:
    scheduler = _scheduler()
    low = scheduler.enqueue("research_agent", priority=TaskPriority.LOW)
    high = scheduler.enqueue("rules_agent", priority=TaskPriority.HIGH)
    normal = scheduler.enqueue("generate_agent", priority=TaskPriority.NORMAL)

    first = scheduler.claim_next()
    second = scheduler.claim_next()
    third = scheduler.claim_next()

    assert first is not None and first.task_id == high.task_id
    assert second is not None and second.task_id == normal.task_id
    assert third is not None and third.task_id == low.task_id


def test_claim_next_fifo_within_same_priority() -> None:
    scheduler = _scheduler()
    first = scheduler.enqueue("research_agent", priority=TaskPriority.NORMAL)
    second = scheduler.enqueue("rules_agent", priority=TaskPriority.NORMAL)

    claimed_first = scheduler.claim_next()
    claimed_second = scheduler.claim_next()

    assert claimed_first is not None and claimed_first.task_id == first.task_id
    assert claimed_second is not None and claimed_second.task_id == second.task_id


def test_global_concurrency_limit() -> None:
    scheduler = _scheduler(max_global=1, default_per_agent=2)
    scheduler.enqueue("research_agent")
    scheduler.enqueue("rules_agent")

    first = scheduler.claim_next()
    assert first is not None
    assert scheduler.claim_next() is None


def test_per_agent_concurrency_limit() -> None:
    scheduler = _scheduler(max_global=10, default_per_agent=1)
    scheduler.enqueue("research_agent")
    scheduler.enqueue("research_agent")

    first = scheduler.claim_next()
    assert first is not None
    assert scheduler.claim_next() is None


def test_per_agent_override_limit() -> None:
    scheduler = _scheduler(
        max_global=10,
        default_per_agent=1,
        per_agent={"research_agent": 2},
    )
    scheduler.enqueue("research_agent")
    scheduler.enqueue("research_agent")

    assert scheduler.claim_next() is not None
    assert scheduler.claim_next() is not None
    assert scheduler.claim_next() is None


def test_complete_and_fail_lifecycle() -> None:
    scheduler = _scheduler()
    scheduler.enqueue("research_agent")
    claimed = scheduler.claim_next()
    assert claimed is not None

    completed = scheduler.complete(claimed.task_id, result={"ok": True})
    assert completed.status == ScheduledTaskStatus.COMPLETED
    assert completed.result == {"ok": True}
    assert completed.finished_at is not None

    another = scheduler.enqueue("rules_agent")
    running = scheduler.claim_next()
    assert running is not None
    assert running.task_id == another.task_id
    failed = scheduler.fail(running.task_id, error_message="boom")
    assert failed.status == ScheduledTaskStatus.FAILED
    assert failed.error_message == "boom"
    assert scheduler.running_count() == 0


def test_cancel_queued_task() -> None:
    scheduler = _scheduler()
    task = scheduler.enqueue("research_agent")
    cancelled = scheduler.cancel(task.task_id)
    assert cancelled.status == ScheduledTaskStatus.CANCELLED
    assert scheduler.claim_next() is None


def test_cancel_running_task_raises() -> None:
    scheduler = _scheduler()
    task = scheduler.enqueue("research_agent")
    scheduler.claim_next()
    with pytest.raises(ValueError, match="Only queued tasks"):
        scheduler.cancel(task.task_id)


def test_list_tasks_filters_by_status_and_agent() -> None:
    scheduler = _scheduler()
    scheduler.enqueue("research_agent")
    rules_task = scheduler.enqueue("rules_agent")
    scheduler.claim_next()

    queued = scheduler.list_tasks(status=ScheduledTaskStatus.QUEUED)
    running = scheduler.list_tasks(status=ScheduledTaskStatus.RUNNING)
    rules_only = scheduler.list_tasks(agent_id="rules_agent")

    assert len(queued) == 1
    assert len(running) == 1
    assert {item.task_id for item in rules_only} == {rules_task.task_id}


def test_custom_registry_scheduler() -> None:
    registry = AgentRegistry()
    registry.register(
        AgentDeclaration(
            agent_id="demo_agent",
            display_name="Demo",
            category=AgentCategory.LISTING,
            status="active",
        )
    )
    scheduler = AgentTaskScheduler(registry)
    task = scheduler.enqueue("demo_agent")
    assert task.agent_id == "demo_agent"
