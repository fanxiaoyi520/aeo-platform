"""MV5-04 — Risk incident review and rule tuning SDK."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from aeo_shared.batch_metrics import SkuBatchResult


class IncidentType(StrEnum):
    TASK_FAILED = "task_failed"
    DEGRADED_MODE = "degraded_mode"
    HITL_REJECTED = "hitl_rejected"
    RULE_VIOLATION = "rule_violation"
    TIMEOUT = "timeout"


class IncidentRecord(BaseModel):
    sku_id: str
    agent: str
    platform: str
    type: IncidentType
    error: str | None = None
    risk_level: str = "L1"
    timestamp: str


class TuningSuggestion(BaseModel):
    rule_id: str
    current_effect: str
    suggested_effect: str
    reason: str
    confidence: float


class RiskReviewReport(BaseModel):
    milestone: str
    task: str
    generated_at: str
    testset_path: str
    summary: dict[str, Any]
    incidents: list[IncidentRecord]
    tuning_suggestions: list[TuningSuggestion]
    kpi_check: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "milestone": self.milestone,
            "task": self.task,
            "generated_at": self.generated_at,
            "testset_path": self.testset_path,
            "summary": self.summary,
            "incidents": [i.model_dump() for i in self.incidents],
            "tuning_suggestions": [s.model_dump() for s in self.tuning_suggestions],
            "kpi_check": self.kpi_check,
        }


def classify_incidents(results: list[SkuBatchResult]) -> list[IncidentRecord]:
    incidents: list[IncidentRecord] = []
    timestamp = datetime.now(UTC).isoformat()

    for result in results:
        for agent in result.agents:
            if agent.status == "failed":
                incidents.append(
                    IncidentRecord(
                        sku_id=result.sku_id,
                        agent=agent.agent,
                        platform=agent.platform,
                        type=IncidentType.TASK_FAILED,
                        error=agent.error,
                        risk_level="L1",
                        timestamp=timestamp,
                    )
                )
            elif agent.degraded:
                incidents.append(
                    IncidentRecord(
                        sku_id=result.sku_id,
                        agent=agent.agent,
                        platform=agent.platform,
                        type=IncidentType.DEGRADED_MODE,
                        error=agent.error,
                        risk_level="L0",
                        timestamp=timestamp,
                    )
                )

    return incidents


def analyze_incidents(incidents: list[IncidentRecord]) -> dict[str, Any]:
    if not incidents:
        return {
            "total_incidents": 0,
            "incident_rate": 0.0,
            "by_type": {},
            "by_agent": {},
            "by_platform": {},
        }

    by_type: dict[str, int] = {}
    by_agent: dict[str, int] = {}
    by_platform: dict[str, int] = {}

    for incident in incidents:
        by_type[incident.type.value] = by_type.get(incident.type.value, 0) + 1
        by_agent[incident.agent] = by_agent.get(incident.agent, 0) + 1
        by_platform[incident.platform] = by_platform.get(incident.platform, 0) + 1

    return {
        "total_incidents": len(incidents),
        "incident_rate": len(incidents) / 100.0,
        "by_type": by_type,
        "by_agent": by_agent,
        "by_platform": by_platform,
    }


def generate_tuning_suggestions(incidents: list[IncidentRecord]) -> list[TuningSuggestion]:
    if not incidents:
        return []

    suggestions: list[TuningSuggestion] = []
    agent_platform_counts: dict[str, dict[str, int]] = {}

    for incident in incidents:
        key = f"{incident.agent}_{incident.platform}"
        if key not in agent_platform_counts:
            agent_platform_counts[key] = {"degraded": 0, "failed": 0}
        if incident.type == IncidentType.DEGRADED_MODE:
            agent_platform_counts[key]["degraded"] += 1
        elif incident.type == IncidentType.TASK_FAILED:
            agent_platform_counts[key]["failed"] += 1

    for key, counts in agent_platform_counts.items():
        agent, platform = key.split("_", 1)
        rule_id = f"{agent}.{platform}"

        if counts["degraded"] >= 2:
            suggestions.append(
                TuningSuggestion(
                    rule_id=rule_id,
                    current_effect="require_hitl",
                    suggested_effect="allow",
                    reason=(
                        f"{agent} agent degraded {counts['degraded']} times on {platform}, "
                        "consider relaxing L1 to L0"
                    ),
                    confidence=0.75,
                )
            )
        elif counts["failed"] >= 3:
            suggestions.append(
                TuningSuggestion(
                    rule_id=rule_id,
                    current_effect="allow",
                    suggested_effect="require_hitl",
                    reason=(
                        f"{agent} agent failed {counts['failed']} times on {platform}, "
                        "consider adding L1 review"
                    ),
                    confidence=0.60,
                )
            )

    return suggestions


def build_review_report(
    results: list[SkuBatchResult],
    *,
    testset_path: str,
) -> RiskReviewReport:
    total_tasks = sum(len(r.agents) for r in results)
    incidents = classify_incidents(results)
    analysis = analyze_incidents(incidents)
    suggestions = generate_tuning_suggestions(incidents)

    critical_incidents = sum(
        1 for i in incidents if i.type in {IncidentType.RULE_VIOLATION, IncidentType.HITL_REJECTED}
    )

    summary = {
        "total_tasks": total_tasks,
        "total_incidents": analysis["total_incidents"],
        "incident_rate": analysis["incident_rate"],
        "critical_incidents": critical_incidents,
        "by_type": analysis["by_type"],
        "by_agent": analysis["by_agent"],
        "by_platform": analysis["by_platform"],
    }

    kpi_check = [
        {
            "metric": "critical_incidents",
            "target": 0,
            "actual": critical_incidents,
            "passed": critical_incidents == 0,
        },
        {
            "metric": "incident_rate",
            "target": 0.10,
            "actual": analysis["incident_rate"],
            "passed": analysis["incident_rate"] <= 0.10,
        },
    ]

    return RiskReviewReport(
        milestone="MV5",
        task="MV5-04",
        generated_at=datetime.now(UTC).isoformat(),
        testset_path=testset_path,
        summary=summary,
        incidents=incidents,
        tuning_suggestions=suggestions,
        kpi_check=kpi_check,
    )
