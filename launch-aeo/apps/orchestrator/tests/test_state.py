from aeo_orchestrator.state import TaskStatus, initial_state, make_trace_event


def test_initial_state_defaults() -> None:
    state = initial_state(task_id="t-1", platform="amazon", sku="X431")
    assert state["task_id"] == "t-1"
    assert state["platform"] == "amazon"
    assert state["sku"] == "X431"
    assert state["market"] == "US"
    assert state["retry_count"] == 0
    assert state["degraded_mode"] is False
    assert state["status"] == TaskStatus.RUNNING
    assert state["trace"] == []


def test_make_trace_event_shape() -> None:
    event = make_trace_event("research_agent", "completed", detail={"ok": True})
    assert event["agent"] == "research_agent"
    assert event["status"] == "completed"
    assert event["detail"] == {"ok": True}
    assert event["timestamp"]
