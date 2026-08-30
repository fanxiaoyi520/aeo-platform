from aeo_orchestrator.state import AgentTraceStatus, TaskState, TaskStatus, make_trace_event


def route_after_human_review(state: TaskState) -> str:
    if state.get("hitl_decision") == "reject":
        return "generate"
    return "review"


async def human_review_node(state: TaskState) -> dict[str, object]:
    """HITL node — graph interrupts before this node; resume via hitl.approve/reject."""
    decision = state.get("hitl_decision") or "approve"
    event = make_trace_event(
        "human_review",
        AgentTraceStatus.COMPLETED,
        detail={"decision": decision},
    )
    status = TaskStatus.RUNNING if decision == "reject" else TaskStatus.WAITING_HITL
    return {"status": status, "trace": [event]}


async def review_node(state: TaskState) -> dict[str, object]:
    """review_agent — S3-07 will persist listing version."""
    generated = state.get("generated") or {}
    event = make_trace_event("review_agent", AgentTraceStatus.COMPLETED)
    return {
        "final_output": generated,
        "status": TaskStatus.COMPLETED,
        "trace": [event],
    }
