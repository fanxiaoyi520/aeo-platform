"""MV1-02 — cross-agent task scheduler with priority queue (MV-M01)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from typing import Any

from pydantic import BaseModel, Field

from aeo_shared.agent_registry import AgentRegistry


class TaskPriority(IntEnum):
    """Lower value = higher priority."""

    CRITICAL = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    BACKGROUND = 100


class ScheduledTaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SchedulerConfig(BaseModel):
    """Concurrency quotas for cross-agent scheduling."""

    max_concurrent_global: int = 10
    default_max_concurrent_per_agent: int = 2
    max_concurrent_per_agent: dict[str, int] = Field(default_factory=dict)


class ScheduledAgentTask(BaseModel):
    """Unit of work routed to a registered agent."""

    task_id: str
    agent_id: str
    capability: str | None = None
    priority: TaskPriority = TaskPriority.NORMAL
    status: ScheduledTaskStatus = ScheduledTaskStatus.QUEUED
    payload: dict[str, Any] = Field(default_factory=dict)
    parent_task_id: str | None = None
    sequence: int = 0
    result: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    finished_at: datetime | None = None


class AgentTaskScheduler:
    """In-memory priority scheduler validated against an agent registry."""

    def __init__(
        self,
        registry: AgentRegistry,
        *,
        config: SchedulerConfig | None = None,
    ) -> None:
        self._registry = registry
        self._config = config or SchedulerConfig()
        self._tasks: dict[str, ScheduledAgentTask] = {}
        self._sequence = 0

    @property
    def config(self) -> SchedulerConfig:
        return self._config

    def enqueue(
        self,
        agent_id: str,
        *,
        capability: str | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        payload: dict[str, Any] | None = None,
        parent_task_id: str | None = None,
        task_id: str | None = None,
    ) -> ScheduledAgentTask:
        declaration = self._registry.get(agent_id)
        if declaration.status != "active":
            msg = f"Agent is not active: {agent_id} ({declaration.status})"
            raise ValueError(msg)
        if capability is not None:
            capability_names = {item.name for item in declaration.capabilities}
            if capability not in capability_names:
                msg = f"Capability not declared on agent {agent_id}: {capability}"
                raise ValueError(msg)

        self._sequence += 1
        task = ScheduledAgentTask(
            task_id=task_id or str(uuid.uuid4()),
            agent_id=agent_id,
            capability=capability,
            priority=priority,
            payload=payload or {},
            parent_task_id=parent_task_id,
            sequence=self._sequence,
        )
        self._tasks[task.task_id] = task
        return task

    def get(self, task_id: str) -> ScheduledAgentTask:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            msg = f"Scheduled task not found: {task_id}"
            raise KeyError(msg) from exc

    def list_tasks(
        self,
        *,
        status: ScheduledTaskStatus | None = None,
        agent_id: str | None = None,
    ) -> list[ScheduledAgentTask]:
        items = list(self._tasks.values())
        if status is not None:
            items = [item for item in items if item.status == status]
        if agent_id is not None:
            items = [item for item in items if item.agent_id == agent_id]
        return sorted(items, key=lambda item: (item.priority, item.sequence))

    def claim_next(self) -> ScheduledAgentTask | None:
        if self._running_count() >= self._config.max_concurrent_global:
            return None

        for task in self._queued_by_priority():
            if self._running_count(agent_id=task.agent_id) >= self._agent_limit(task.agent_id):
                continue
            return self._mark_running(task)
        return None

    def complete(self, task_id: str, *, result: dict[str, Any] | None = None) -> ScheduledAgentTask:
        task = self.get(task_id)
        if task.status != ScheduledTaskStatus.RUNNING:
            msg = f"Task is not running: {task_id} ({task.status})"
            raise ValueError(msg)
        task.status = ScheduledTaskStatus.COMPLETED
        task.result = result
        task.finished_at = datetime.now(UTC)
        return task

    def fail(self, task_id: str, *, error_message: str) -> ScheduledAgentTask:
        task = self.get(task_id)
        if task.status != ScheduledTaskStatus.RUNNING:
            msg = f"Task is not running: {task_id} ({task.status})"
            raise ValueError(msg)
        task.status = ScheduledTaskStatus.FAILED
        task.error_message = error_message
        task.finished_at = datetime.now(UTC)
        return task

    def cancel(self, task_id: str) -> ScheduledAgentTask:
        task = self.get(task_id)
        if task.status != ScheduledTaskStatus.QUEUED:
            msg = f"Only queued tasks can be cancelled: {task_id} ({task.status})"
            raise ValueError(msg)
        task.status = ScheduledTaskStatus.CANCELLED
        task.finished_at = datetime.now(UTC)
        return task

    def running_count(self, *, agent_id: str | None = None) -> int:
        return self._running_count(agent_id=agent_id)

    def _queued_by_priority(self) -> list[ScheduledAgentTask]:
        return sorted(
            (item for item in self._tasks.values() if item.status == ScheduledTaskStatus.QUEUED),
            key=lambda item: (item.priority, item.sequence),
        )

    def _running_count(self, *, agent_id: str | None = None) -> int:
        running = (
            item for item in self._tasks.values() if item.status == ScheduledTaskStatus.RUNNING
        )
        if agent_id is None:
            return sum(1 for _ in running)
        return sum(1 for item in running if item.agent_id == agent_id)

    def _agent_limit(self, agent_id: str) -> int:
        return self._config.max_concurrent_per_agent.get(
            agent_id,
            self._config.default_max_concurrent_per_agent,
        )

    def _mark_running(self, task: ScheduledAgentTask) -> ScheduledAgentTask:
        task.status = ScheduledTaskStatus.RUNNING
        task.started_at = datetime.now(UTC)
        return task
