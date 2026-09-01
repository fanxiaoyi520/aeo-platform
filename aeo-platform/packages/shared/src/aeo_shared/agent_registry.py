"""Agent registry schema — MV1-01 / MV-M01."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentCategory(StrEnum):
    """Six production agent families from MV plan §3."""

    SELECTION = "A01"
    ADS = "A02"
    LISTING = "A03"
    OPERATIONS = "A04"
    SUPPORT = "A05"
    ANALYTICS = "A06"


class RiskLevel(StrEnum):
    """Default risk tier for agent outputs (MV-M02)."""

    L0 = "L0"
    L1 = "L1"
    L2 = "L2"


AgentStatus = Literal["active", "planned", "deprecated", "disabled"]


class AgentCapability(BaseModel):
    """Single callable capability exposed by an agent."""

    name: str
    description: str = ""
    tools: list[str] = Field(default_factory=list)


class AgentDeclaration(BaseModel):
    """Registered agent metadata for orchestration and future scheduling."""

    agent_id: str
    display_name: str
    category: AgentCategory
    description: str = ""
    version: str = "1.0.0"
    capabilities: list[AgentCapability] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.L0
    platforms: list[str] = Field(default_factory=lambda: ["amazon", "tiktok"])
    status: AgentStatus = "active"
    graph_node: str | None = None
    timeout_seconds: int = 60


class AgentRegistry:
    """In-memory agent registry (DB persistence deferred to MV1-02+)."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentDeclaration] = {}

    def register(self, declaration: AgentDeclaration) -> None:
        if declaration.agent_id in self._agents:
            msg = f"Agent already registered: {declaration.agent_id}"
            raise ValueError(msg)
        self._agents[declaration.agent_id] = declaration

    def get(self, agent_id: str) -> AgentDeclaration:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            msg = f"Agent not found: {agent_id}"
            raise KeyError(msg) from exc

    def list_agents(
        self,
        *,
        status: AgentStatus | None = None,
        category: AgentCategory | None = None,
    ) -> list[AgentDeclaration]:
        items = list(self._agents.values())
        if status is not None:
            items = [item for item in items if item.status == status]
        if category is not None:
            items = [item for item in items if item.category == category]
        return sorted(items, key=lambda item: item.agent_id)

    def to_catalog(self) -> list[dict[str, Any]]:
        return [item.model_dump(mode="json") for item in self.list_agents()]
