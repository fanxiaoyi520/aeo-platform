import pytest
from aeo_orchestrator.nodes.compliance import (
    MAX_COMPLIANCE_RETRIES,
    attempt_fix,
    compliance_node,
    route_after_compliance,
    validate_generated,
)
from aeo_orchestrator.state import TaskState, initial_state

_VALID = {
    "title": "LAUNCH X431 Pro OBD2 Scanner Diagnostic Tool",
    "bullets": [
        "FULL SYSTEM DIAGNOSIS for engine and ABS codes",
        "LIVE DATA STREAM for faster troubleshooting",
        "WIDE OBD2 COVERAGE for most 1996+ vehicles",
        "PROFESSIONAL GRADE tool trusted by mechanics",
        "EASY TO USE with intuitive menus",
    ],
    "search_terms": "obd2 scanner diagnostic x431",
    "description": "Professional OBD2 scanner for workshops.",
}


def test_validate_generated_passes_valid_listing() -> None:
    passed, issues = validate_generated(_VALID, platform="amazon")
    assert passed is True
    assert issues == []


def test_validate_generated_fails_forbidden_phrase() -> None:
    payload = {**_VALID, "title": "BEST OBD2 scanner with free shipping"}
    passed, issues = validate_generated(payload, platform="amazon")
    assert passed is False
    assert any(issue["code"] == "forbidden_phrase" for issue in issues)


def test_validate_generated_fails_insufficient_bullets() -> None:
    payload = {**_VALID, "bullets": ["Only one bullet"]}
    passed, issues = validate_generated(payload, platform="amazon")
    assert passed is False
    assert any(issue["code"] == "bullet_count" for issue in issues)


def test_attempt_fix_strips_html_and_forbidden_words() -> None:
    payload = {
        **_VALID,
        "title": "<b>BEST</b> OBD2 scanner",
        "bullets": _VALID["bullets"][:1],
    }
    fixed = attempt_fix(payload, [])
    assert "<" not in fixed["title"]
    assert "best" not in fixed["title"].lower()
    assert len(fixed["bullets"]) == 5


@pytest.mark.asyncio
async def test_compliance_node_increments_retry_count_on_failure() -> None:
    state = initial_state(task_id="c1", platform="amazon", sku="X431")
    state["generated"] = {"title": "", "bullets": [], "search_terms": "", "description": ""}

    result = await compliance_node(state)
    compliance = result["compliance"]
    assert isinstance(compliance, dict)
    assert compliance["passed"] is False
    assert result["retry_count"] == 1


def test_route_after_compliance_retries_until_limit() -> None:
    state = TaskState(
        compliance={"passed": False, "issues": [{"field": "title", "code": "x", "message": "x"}]},
        retry_count=MAX_COMPLIANCE_RETRIES,
    )
    assert route_after_compliance(state) == "human_review"

    state["retry_count"] = MAX_COMPLIANCE_RETRIES - 1
    assert route_after_compliance(state) == "generate"
