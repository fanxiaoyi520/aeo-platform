from unittest.mock import AsyncMock, patch

import pytest
from aeo_orchestrator.nodes.review import review_node
from aeo_orchestrator.state import TaskStatus, initial_state


@pytest.mark.asyncio
async def test_review_node_persists_listing_version() -> None:
    state = initial_state(task_id="r1", platform="amazon", sku="DEMO-001")
    state["generated"] = {"title": "Test title", "bullets": ["a"] * 5}
    state["compliance"] = {"passed": True}
    state["retry_count"] = 1

    with patch(
        "aeo_orchestrator.nodes.review.save_listing_version",
        new_callable=AsyncMock,
        return_value={"id": "lv-1", "version": 2, "persisted": True},
    ) as mock_save:
        result = await review_node(state)

    mock_save.assert_awaited_once_with("r1", state["generated"])
    final_output = result["final_output"]
    assert isinstance(final_output, dict)
    assert final_output["listing_version_id"] == "lv-1"
    assert final_output["metrics"]["listing_version"] == 2
    assert result["status"] == TaskStatus.COMPLETED
