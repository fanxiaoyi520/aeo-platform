"""AEO Platform shared types, errors, and utilities."""

from aeo_shared.agent_catalog import build_default_registry, get_default_registry
from aeo_shared.agent_registry import (
    AgentCapability,
    AgentCategory,
    AgentDeclaration,
    AgentRegistry,
    RiskLevel,
)

__all__ = [
    "AgentCapability",
    "AgentCategory",
    "AgentDeclaration",
    "AgentRegistry",
    "RiskLevel",
    "build_default_registry",
    "get_default_registry",
]
