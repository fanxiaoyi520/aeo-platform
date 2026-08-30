"""compliance_agent — S3-05: listing validation, auto-fix, and generate retry routing."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, TypedDict

from aeo_orchestrator.nodes._helpers import with_started_trace
from aeo_orchestrator.state import AgentTraceStatus, TaskState, make_trace_event

MAX_COMPLIANCE_RETRIES = 3
TITLE_MAX_LEN = 200
BULLET_MAX_LEN = 500
REQUIRED_BULLET_COUNT = 5
SEARCH_TERMS_MAX_BYTES = 250

FORBIDDEN_PHRASES = (
    "free shipping",
    "best seller",
    "best",
    "#1",
    "guarantee",
    "100% satisfaction",
)

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


class ComplianceIssue(TypedDict):
    field: str
    code: str
    message: str


def _as_generated(state: TaskState) -> dict[str, Any]:
    generated = state.get("generated")
    return generated if isinstance(generated, dict) else {}


def _has_html(value: str) -> bool:
    return bool(HTML_TAG_PATTERN.search(value))


def _contains_forbidden_phrase(value: str) -> str | None:
    lowered = value.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            return phrase
    return None


def _is_mostly_uppercase(value: str) -> bool:
    letters = [char for char in value if char.isalpha()]
    if len(letters) < 8:
        return False
    upper = sum(1 for char in letters if char.isupper())
    return upper / len(letters) > 0.8


def validate_generated(
    generated: dict[str, Any], *, platform: str
) -> tuple[bool, list[ComplianceIssue]]:
    issues: list[ComplianceIssue] = []
    title = str(generated.get("title", "")).strip()
    bullets_raw = generated.get("bullets", [])
    bullets = (
        [str(item).strip() for item in bullets_raw if str(item).strip()]
        if isinstance(bullets_raw, list)
        else []
    )
    search_terms = str(generated.get("search_terms", "")).strip()
    description = str(generated.get("description", "")).strip()

    if not title:
        issues.append({"field": "title", "code": "title_missing", "message": "Title is required"})
    elif len(title) > TITLE_MAX_LEN:
        issues.append(
            {
                "field": "title",
                "code": "title_too_long",
                "message": f"Title exceeds {TITLE_MAX_LEN} characters",
            }
        )
    if platform == "amazon" and title and _is_mostly_uppercase(title):
        issues.append(
            {
                "field": "title",
                "code": "title_all_caps",
                "message": "Title must not be mostly uppercase",
            }
        )

    for field_name, value in (
        ("title", title),
        ("description", description),
        *[(f"bullets[{idx}]", bullet) for idx, bullet in enumerate(bullets)],
    ):
        if not value:
            continue
        if _has_html(value):
            issues.append(
                {
                    "field": field_name,
                    "code": "html_not_allowed",
                    "message": "HTML tags are not allowed",
                }
            )
        forbidden = _contains_forbidden_phrase(value)
        if forbidden:
            issues.append(
                {
                    "field": field_name,
                    "code": "forbidden_phrase",
                    "message": f"Forbidden phrase: {forbidden}",
                }
            )

    if platform == "amazon":
        non_empty_bullets = [bullet for bullet in bullets if bullet]
        if len(non_empty_bullets) < REQUIRED_BULLET_COUNT:
            issues.append(
                {
                    "field": "bullets",
                    "code": "bullet_count",
                    "message": f"Expected {REQUIRED_BULLET_COUNT} bullet points",
                }
            )
        for idx, bullet in enumerate(bullets):
            if bullet and len(bullet) > BULLET_MAX_LEN:
                issues.append(
                    {
                        "field": f"bullets[{idx}]",
                        "code": "bullet_too_long",
                        "message": f"Bullet exceeds {BULLET_MAX_LEN} characters",
                    }
                )

    if search_terms and len(search_terms.encode("utf-8")) > SEARCH_TERMS_MAX_BYTES:
        issues.append(
            {
                "field": "search_terms",
                "code": "search_terms_too_long",
                "message": f"Search terms exceed {SEARCH_TERMS_MAX_BYTES} bytes",
            }
        )

    return len(issues) == 0, issues


def _strip_html(value: str) -> str:
    return HTML_TAG_PATTERN.sub("", value).strip()


def _remove_forbidden_phrases(value: str) -> str:
    cleaned = value
    for phrase in FORBIDDEN_PHRASES:
        cleaned = re.sub(re.escape(phrase), "", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def attempt_fix(generated: dict[str, Any], issues: list[ComplianceIssue]) -> dict[str, Any]:
    fixed = deepcopy(generated)
    title = str(fixed.get("title", ""))
    bullets_raw = fixed.get("bullets", [])
    bullets = list(bullets_raw) if isinstance(bullets_raw, list) else []
    search_terms = str(fixed.get("search_terms", ""))
    description = str(fixed.get("description", ""))

    title = _remove_forbidden_phrases(_strip_html(title))
    if len(title) > TITLE_MAX_LEN:
        title = title[:TITLE_MAX_LEN].rstrip()
    fixed["title"] = title

    cleaned_bullets: list[str] = []
    for bullet in bullets:
        text = _remove_forbidden_phrases(_strip_html(str(bullet)))
        if len(text) > BULLET_MAX_LEN:
            text = text[:BULLET_MAX_LEN].rstrip()
        cleaned_bullets.append(text)
    while len(cleaned_bullets) < REQUIRED_BULLET_COUNT:
        cleaned_bullets.append("")
    fixed["bullets"] = cleaned_bullets[:REQUIRED_BULLET_COUNT]

    fixed["search_terms"] = _remove_forbidden_phrases(_strip_html(search_terms))
    encoded = fixed["search_terms"].encode("utf-8")
    if len(encoded) > SEARCH_TERMS_MAX_BYTES:
        fixed["search_terms"] = encoded[:SEARCH_TERMS_MAX_BYTES].decode("utf-8", errors="ignore")

    fixed["description"] = _remove_forbidden_phrases(_strip_html(description))
    return fixed


async def compliance_node(state: TaskState) -> dict[str, object]:
    """Validate generated listing and attempt lightweight auto-fixes."""
    trace = [with_started_trace(state, "compliance_agent")]
    platform = str(state.get("platform", "amazon"))
    retry_count = state.get("retry_count", 0)
    generated = _as_generated(state)

    passed, issues = validate_generated(generated, platform=platform)
    fixed_output = generated if passed else attempt_fix(generated, issues)
    if not passed:
        passed, remaining = validate_generated(fixed_output, platform=platform)
        issues = remaining

    trace.append(
        make_trace_event(
            "compliance_agent",
            AgentTraceStatus.COMPLETED if passed else AgentTraceStatus.FAILED,
            detail={
                "passed": passed,
                "issue_count": len(issues),
                "retry_count": retry_count,
            },
        )
    )

    result: dict[str, object] = {
        "compliance": {
            "passed": passed,
            "issues": issues,
            "fixed_output": fixed_output,
        },
        "trace": trace,
    }
    if not passed:
        result["retry_count"] = retry_count + 1
        result["generated"] = fixed_output
    return result


def route_after_compliance(state: TaskState) -> str:
    compliance = state.get("compliance") or {}
    retry_count = state.get("retry_count", 0)
    if not compliance.get("passed", False) and retry_count < MAX_COMPLIANCE_RETRIES:
        return "generate"
    return "human_review"
