"""Orchestrator integration with MV1-02 cross-agent scheduler."""

from __future__ import annotations

from functools import lru_cache

from aeo_shared.agent_catalog import get_default_registry
from aeo_shared.task_scheduler import AgentTaskScheduler, SchedulerConfig

__all__ = ["build_default_scheduler", "get_default_scheduler"]


def build_default_scheduler(
    *,
    config: SchedulerConfig | None = None,
) -> AgentTaskScheduler:
    return AgentTaskScheduler(get_default_registry(), config=config)


@lru_cache
def get_default_scheduler() -> AgentTaskScheduler:
    return build_default_scheduler()
