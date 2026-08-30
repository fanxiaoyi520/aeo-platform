from aeo_orchestrator.persistence import save_listing_version
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
    """review_agent — persist listing version and finalize task output."""
    generated = state.get("generated") or {}
    compliance = state.get("compliance") or {}
    persisted = await save_listing_version(state["task_id"], generated)
    metrics = {
        "degraded_mode": bool(state.get("degraded_mode", False)),
        "retry_count": int(state.get("retry_count", 0)),
        "compliance_passed": compliance.get("passed") if isinstance(compliance, dict) else None,
        "listing_version": persisted.get("version"),
    }
    final_output = {
        **generated,
        "metrics": metrics,
        "listing_version_id": persisted.get("id"),
    }
    event = make_trace_event(
        "review_agent",
        AgentTraceStatus.COMPLETED,
        detail={
            "listing_version": persisted.get("version"),
            "persisted": persisted.get("persisted", True),
        },
    )
    return {
        "final_output": final_output,
        "status": TaskStatus.COMPLETED,
        "trace": [event],
    }
