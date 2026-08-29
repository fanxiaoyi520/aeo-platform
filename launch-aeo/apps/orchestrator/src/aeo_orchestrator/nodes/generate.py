from aeo_orchestrator.nodes._helpers import stub_node
from aeo_orchestrator.state import TaskState


async def generate_node(state: TaskState) -> dict[str, object]:
    """generate_agent — S3-04 will add LLM prompts."""
    return stub_node(
        "generate_agent",
        "generated",
        {
            "title": "",
            "bullets": [],
            "search_terms": "",
            "description": "",
        },
    )
