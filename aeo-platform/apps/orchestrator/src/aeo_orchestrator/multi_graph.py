"""Orchestrator integration with MV1-03 multi-graph parent tasks."""

from __future__ import annotations

from functools import lru_cache

from aeo_shared.agent_catalog import get_default_registry
from aeo_shared.graph_catalog import get_graph_catalog
from aeo_shared.multi_graph import MultiGraphOrchestrator

from aeo_orchestrator.task_scheduler import get_default_scheduler

__all__ = ["build_default_multi_graph", "get_default_multi_graph"]


def build_default_multi_graph() -> MultiGraphOrchestrator:
    return MultiGraphOrchestrator(
        get_default_scheduler(),
        get_default_registry(),
        graphs=get_graph_catalog(),
    )


@lru_cache
def get_default_multi_graph() -> MultiGraphOrchestrator:
    return build_default_multi_graph()
