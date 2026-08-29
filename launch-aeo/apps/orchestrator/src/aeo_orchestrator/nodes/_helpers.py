from typing import Any

from aeo_orchestrator.state import AgentTraceEvent, AgentTraceStatus, TaskState, make_trace_event


def stub_node(agent: str, output_key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    event = make_trace_event(agent, AgentTraceStatus.COMPLETED, detail={"stub": True})
    return {output_key: payload or {}, "trace": [event]}


def with_started_trace(state: TaskState, agent: str) -> AgentTraceEvent:
    return make_trace_event(
        agent, AgentTraceStatus.STARTED, detail={"task_id": state.get("task_id")}
    )
