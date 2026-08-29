from aeo_orchestrator.nodes._helpers import stub_node
from aeo_orchestrator.state import TaskState


async def rules_node(state: TaskState) -> dict[str, object]:
    """rules_agent — S3-03 will add RAG tool calls."""
    return stub_node(
        "rules_agent",
        "rules",
        {
            "platform": state.get("platform"),
            "rule_summary": "",
            "references": [],
        },
    )
