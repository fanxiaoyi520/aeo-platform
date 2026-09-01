"""Validate MV1-02 scheduler against default agent catalog."""

from aeo_orchestrator.task_scheduler import get_default_scheduler
from aeo_shared.task_scheduler import TaskPriority


def test_default_scheduler_can_queue_listing_chain() -> None:
    scheduler = get_default_scheduler()
    tasks = [
        scheduler.enqueue(
            agent_id,
            priority=TaskPriority.NORMAL,
            payload={"step": index},
        )
        for index, agent_id in enumerate(
            (
                "research_agent",
                "rules_agent",
                "generate_agent",
                "compliance_agent",
            )
        )
    ]

    claimed = [scheduler.claim_next() for _ in range(len(tasks))]
    assert all(item is not None for item in claimed)
    assert {item.agent_id for item in claimed if item is not None} == {
        task.agent_id for task in tasks
    }
