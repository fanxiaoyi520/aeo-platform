"""Validate MV1-03 multi-graph orchestrator against listing catalog."""

from aeo_orchestrator.multi_graph import get_default_multi_graph
from aeo_shared.multi_graph import ParentTaskStatus
from aeo_shared.task_scheduler import ScheduledTaskStatus


def test_listing_parent_task_runs_full_agent_chain() -> None:
    orchestrator = get_default_multi_graph()
    scheduler = orchestrator._scheduler  # noqa: SLF001

    parent = orchestrator.create_parent("listing", payload={"sku": "DEMO-001"})
    orchestrator.start(parent.parent_id)

    while parent.status != ParentTaskStatus.COMPLETED:
        claimed = scheduler.claim_next()
        assert claimed is not None
        assert claimed.parent_task_id == parent.parent_id
        orchestrator.advance(
            parent.parent_id,
            claimed.task_id,
            result={"step": claimed.agent_id},
        )
        parent = orchestrator.get_parent(parent.parent_id)

    children = orchestrator.list_children(parent.parent_id)
    assert len(children) == 6
    assert children[0].agent_id == "research_agent"
    assert children[-1].agent_id == "review_agent"
    assert all(item.status == ScheduledTaskStatus.COMPLETED for item in children)
