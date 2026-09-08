"""MV5-02: batch metrics aggregation for 50-SKU pilot."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class AgentExecRecord:
    agent: str
    status: str
    duration_ms: int
    platform: str = "amazon"
    degraded: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "agent": self.agent,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "platform": self.platform,
            "degraded": self.degraded,
        }
        if self.error:
            result["error"] = self.error
        return result


@dataclass(frozen=True)
class SkuBatchResult:
    sku_id: str
    sku: str
    platform: str
    market: str
    agents: list[AgentExecRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku_id": self.sku_id,
            "sku": self.sku,
            "platform": self.platform,
            "market": self.market,
            "agents": [a.to_dict() for a in self.agents],
        }


@dataclass(frozen=True)
class KpiTarget:
    target: Decimal
    operator: str  # "gte" | "lte" | "eq"


class BatchMetricsAggregator:
    def __init__(self) -> None:
        self._results: list[SkuBatchResult] = []

    def add(self, result: SkuBatchResult) -> None:
        self._results.append(result)

    def build_summary(self) -> dict[str, Any]:
        all_agents: list[AgentExecRecord] = []
        for r in self._results:
            all_agents.extend(r.agents)

        completed = sum(1 for a in all_agents if a.status == "completed")
        failed = sum(1 for a in all_agents if a.status == "failed")
        total_duration = sum(a.duration_ms for a in all_agents)
        degraded = sum(1 for a in all_agents if a.degraded)

        per_platform: dict[str, dict[str, Any]] = {}
        for r in self._results:
            p = r.platform
            if p not in per_platform:
                per_platform[p] = {
                    "total_skus": 0,
                    "agent_runs": 0,
                    "completed": 0,
                    "failed": 0,
                    "total_duration_ms": 0,
                }
            per_platform[p]["total_skus"] += 1
            for a in r.agents:
                per_platform[p]["agent_runs"] += 1
                per_platform[p]["total_duration_ms"] += a.duration_ms
                if a.status == "completed":
                    per_platform[p]["completed"] += 1
                else:
                    per_platform[p]["failed"] += 1

        return {
            "total_skus": len(self._results),
            "total_agent_runs": len(all_agents),
            "completed": completed,
            "failed": failed,
            "degraded_runs": degraded,
            "total_duration_ms": total_duration,
            "avg_duration_ms": total_duration // len(all_agents) if all_agents else 0,
            "per_platform": per_platform,
        }

    def check_kpis(
        self,
        kpis: dict[str, KpiTarget],
        values: dict[str, Decimal],
    ) -> list[dict[str, Any]]:
        checks: list[dict[str, Any]] = []
        for metric, target in kpis.items():
            actual = values.get(metric)
            if actual is None:
                checks.append(
                    {
                        "metric": metric,
                        "target": str(target.target),
                        "actual": None,
                        "passed": False,
                    }
                )
                continue

            if target.operator == "gte":
                passed = actual >= target.target
            elif target.operator == "lte":
                passed = actual <= target.target
            elif target.operator == "eq":
                passed = actual == target.target
            else:
                passed = False

            checks.append(
                {
                    "metric": metric,
                    "target": str(target.target),
                    "operator": target.operator,
                    "actual": str(actual),
                    "passed": passed,
                }
            )
        return checks
