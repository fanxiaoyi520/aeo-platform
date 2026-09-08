"""MV4-05 — strategy suggestions → follow-up task auto-creation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

from aeo_shared.task_scheduler import AgentTaskScheduler, ScheduledAgentTask, TaskPriority

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ActionMappingEntry:
    """A single action → agent routing entry."""

    agent_id: str
    capability: str
    priority: TaskPriority = TaskPriority.NORMAL


class ActionMapping:
    """Static mapping from strategy action names to (agent_id, capability)."""

    def __init__(self, entries: dict[str, ActionMappingEntry] | None = None) -> None:
        self._entries = entries if entries is not None else dict(_DEFAULT_MAPPING)

    def resolve(self, action: str) -> ActionMappingEntry | None:
        return self._entries.get(action)

    def __contains__(self, action: str) -> bool:
        return action in self._entries

    def __getitem__(self, action: str) -> ActionMappingEntry:
        return self._entries[action]


_DEFAULT_MAPPING: dict[str, ActionMappingEntry] = {
    "increase_ad_spend": ActionMappingEntry(
        agent_id="ads_agent",
        capability="ads.suggest",
        priority=TaskPriority.HIGH,
    ),
    "decrease_ad_spend": ActionMappingEntry(
        agent_id="ads_agent",
        capability="ads.suggest",
        priority=TaskPriority.NORMAL,
    ),
    "restock": ActionMappingEntry(
        agent_id="operations_agent",
        capability="ops.suggest",
        priority=TaskPriority.HIGH,
    ),
    "adjust_price": ActionMappingEntry(
        agent_id="operations_agent",
        capability="ops.suggest",
        priority=TaskPriority.NORMAL,
    ),
    "optimize_listing": ActionMappingEntry(
        agent_id="generate_agent",
        capability="generate.listing",
        priority=TaskPriority.NORMAL,
    ),
    "new_listing": ActionMappingEntry(
        agent_id="selection_agent",
        capability="selection.score",
        priority=TaskPriority.LOW,
    ),
    "reply_customer": ActionMappingEntry(
        agent_id="support_agent",
        capability="support.reply_draft",
        priority=TaskPriority.HIGH,
    ),
}


def get_action_mapping() -> ActionMapping:
    return ActionMapping()


@dataclass
class StrategyTaskCreator:
    """Parse strategy suggestions and enqueue follow-up tasks."""

    scheduler: AgentTaskScheduler
    mapping: ActionMapping = field(default_factory=ActionMapping)

    def create_tasks(
        self,
        suggestions: list[dict[str, Any]],
        *,
        parent_task_id: str | None = None,
    ) -> list[ScheduledAgentTask]:
        created: list[ScheduledAgentTask] = []
        for suggestion in suggestions:
            action = suggestion.get("action", "")
            entry = self.mapping.resolve(action)
            if entry is None:
                logger.warning("unknown_strategy_action", action=action)
                continue

            task = self.scheduler.enqueue(
                entry.agent_id,
                capability=entry.capability,
                priority=entry.priority,
                payload={
                    "action": action,
                    "sku": suggestion.get("sku", ""),
                    "reason": suggestion.get("reason", ""),
                },
                parent_task_id=parent_task_id,
            )
            created.append(task)
        return created
