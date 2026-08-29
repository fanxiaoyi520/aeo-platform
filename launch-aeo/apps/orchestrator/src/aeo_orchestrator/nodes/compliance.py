from aeo_orchestrator.state import AgentTraceStatus, TaskState, make_trace_event


async def compliance_node(state: TaskState) -> dict[str, object]:
    """compliance_agent — S3-05 will add validation rules and retry routing."""
    retry_count = state.get("retry_count", 0)
    event = make_trace_event(
        "compliance_agent",
        AgentTraceStatus.COMPLETED,
        detail={"passed": True, "retry_count": retry_count},
    )
    return {
        "compliance": {"passed": True, "issues": [], "fixed_output": state.get("generated")},
        "trace": [event],
    }


def route_after_compliance(state: TaskState) -> str:
    compliance = state.get("compliance") or {}
    retry_count = state.get("retry_count", 0)
    if not compliance.get("passed", False) and retry_count < 3:
        return "generate"
    return "human_review"
