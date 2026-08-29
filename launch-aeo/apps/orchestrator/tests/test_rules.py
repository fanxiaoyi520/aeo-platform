from unittest.mock import MagicMock, patch

import pytest
from aeo_orchestrator.nodes.rules import rules_node
from aeo_orchestrator.state import initial_state
from aeo_rag.store import SearchResult


def _hit(
    *,
    doc_id: str,
    content: str,
    category: str,
    platform: str = "amazon",
) -> SearchResult:
    return SearchResult(
        doc_id=doc_id,
        content=content,
        score=0.9,
        category=category,
        platform=platform,
        source_file=f"{category}.md",
        chunk_index=0,
    )


@pytest.mark.asyncio
async def test_rules_node_aggregates_rag_hits() -> None:
    state = initial_state(
        task_id="t1",
        platform="amazon",
        sku="X431",
        product_info={"category": "OBD2 scanner"},
    )
    state["research"] = {"keywords": ["obd2", "scanner"]}

    mock_store = MagicMock()
    mock_store.search.side_effect = [
        [_hit(doc_id="r1", content="Title max 200 chars", category="amazon_rules")],
        [_hit(doc_id="p1", content="Launch X431 features", category="product", platform="general")],
        [_hit(doc_id="e1", content="Example listing", category="example")],
    ]

    with patch("aeo_orchestrator.nodes.rules._get_knowledge_store", return_value=mock_store):
        result = await rules_node(state)

    rules = result["rules"]
    assert isinstance(rules, dict)
    assert "Title max 200" in rules["rule_summary"]
    assert len(rules["references"]) == 3
    assert mock_store.search.call_count == 3


@pytest.mark.asyncio
async def test_rules_node_records_failure() -> None:
    state = initial_state(task_id="t2", platform="tiktok", sku="CRP123")
    with patch(
        "aeo_orchestrator.nodes.rules._get_knowledge_store",
        side_effect=RuntimeError("chroma unavailable"),
    ):
        result = await rules_node(state)

    rules = result["rules"]
    assert isinstance(rules, dict)
    assert rules["references"] == []
    assert rules["error"] == "chroma unavailable"
    trace = result["trace"]
    assert isinstance(trace, list)
    assert trace[-1]["status"] == "failed"
