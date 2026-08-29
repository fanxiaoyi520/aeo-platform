from aeo_orchestrator.state import AgentTraceStatus, TaskState, TaskStatus, make_trace_event


async def human_review_node(state: TaskState) -> dict[str, object]:
    """HITL placeholder — graph interrupts before this node (S3-06)."""
    event = make_trace_event(
        "human_review",
        AgentTraceStatus.STARTED,
        detail={"awaiting": "approve_or_reject"},
    )
    return {"status": TaskStatus.WAITING_HITL, "trace": [event]}


async def review_node(state: TaskState) -> dict[str, object]:
    """review_agent — S3-07 will persist listing version."""
    generated = state.get("generated") or {}
    event = make_trace_event("review_agent", AgentTraceStatus.COMPLETED)
    return {
        "final_output": generated,
        "status": TaskStatus.COMPLETED,
        "trace": [event],
    }
