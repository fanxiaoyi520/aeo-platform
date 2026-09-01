"""MV1-03 — parent task orchestration over sub-agent graphs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from aeo_shared.agent_registry import AgentRegistry
from aeo_shared.graph_catalog import SubGraphDefinition, get_subgraph
from aeo_shared.task_scheduler import (
    AgentTaskScheduler,
    ScheduledAgentTask,
    ScheduledTaskStatus,
    TaskPriority,
)


class ParentTaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ParentTask(BaseModel):
    """Top-level workflow spanning one registered sub-graph."""

    parent_id: str
    graph_id: str
    status: ParentTaskStatus = ParentTaskStatus.PENDING
    payload: dict[str, Any] = Field(default_factory=dict)
    current_step: int = 0
    child_task_ids: list[str] = Field(default_factory=list)
    error_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class MultiGraphOrchestrator:
    """Dispatch parent tasks as sequential child jobs on the MV1-02 scheduler."""

    def __init__(
        self,
        scheduler: AgentTaskScheduler,
        registry: AgentRegistry,
        *,
        graphs: dict[str, SubGraphDefinition] | None = None,
    ) -> None:
        self._scheduler = scheduler
        self._registry = registry
        self._graphs = graphs or {}
        self._parents: dict[str, ParentTask] = {}

    def create_parent(
        self,
        graph_id: str,
        *,
        payload: dict[str, Any] | None = None,
        parent_id: str | None = None,
    ) -> ParentTask:
        graph = self._resolve_graph(graph_id)
        for agent_id in graph.agent_ids:
            declaration = self._registry.get(agent_id)
            if declaration.status != "active":
                msg = f"Agent is not active: {agent_id} ({declaration.status})"
                raise ValueError(msg)

        now = datetime.now(UTC)
        parent = ParentTask(
            parent_id=parent_id or str(uuid.uuid4()),
            graph_id=graph.graph_id,
            payload=payload or {},
            created_at=now,
            updated_at=now,
        )
        self._parents[parent.parent_id] = parent
        return parent

    def start(
        self, parent_id: str, *, priority: TaskPriority = TaskPriority.NORMAL
    ) -> ScheduledAgentTask:
        parent = self.get_parent(parent_id)
        if parent.status != ParentTaskStatus.PENDING:
            msg = f"Parent task already started: {parent_id} ({parent.status})"
            raise ValueError(msg)

        parent.status = ParentTaskStatus.RUNNING
        parent.updated_at = datetime.now(UTC)
        return self._dispatch_step(parent, priority=priority)

    def advance(
        self,
        parent_id: str,
        child_task_id: str,
        *,
        result: dict[str, Any] | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> ScheduledAgentTask | ParentTask:
        parent = self.get_parent(parent_id)
        child = self._scheduler.get(child_task_id)
        if child.parent_task_id != parent_id:
            msg = f"Child task {child_task_id} does not belong to parent {parent_id}"
            raise ValueError(msg)
        if child.status != ScheduledTaskStatus.RUNNING:
            msg = f"Child task is not running: {child_task_id} ({child.status})"
            raise ValueError(msg)

        self._scheduler.complete(child_task_id, result=result)
        parent.current_step += 1
        parent.updated_at = datetime.now(UTC)

        graph = self._resolve_graph(parent.graph_id)
        if parent.current_step >= len(graph.agent_ids):
            parent.status = ParentTaskStatus.COMPLETED
            parent.completed_at = datetime.now(UTC)
            return parent

        return self._dispatch_step(parent, priority=priority)

    def fail_parent(self, parent_id: str, *, child_task_id: str, error_message: str) -> ParentTask:
        parent = self.get_parent(parent_id)
        child = self._scheduler.get(child_task_id)
        if child.status == ScheduledTaskStatus.RUNNING:
            self._scheduler.fail(child_task_id, error_message=error_message)
        parent.status = ParentTaskStatus.FAILED
        parent.error_message = error_message
        parent.updated_at = datetime.now(UTC)
        parent.completed_at = datetime.now(UTC)
        return parent

    def get_parent(self, parent_id: str) -> ParentTask:
        try:
            return self._parents[parent_id]
        except KeyError as exc:
            msg = f"Parent task not found: {parent_id}"
            raise KeyError(msg) from exc

    def list_children(self, parent_id: str) -> list[ScheduledAgentTask]:
        self.get_parent(parent_id)
        return self._scheduler.list_tasks(parent_task_id=parent_id)

    def _resolve_graph(self, graph_id: str) -> SubGraphDefinition:
        if graph_id in self._graphs:
            return self._graphs[graph_id]
        return get_subgraph(graph_id)

    def _dispatch_step(
        self,
        parent: ParentTask,
        *,
        priority: TaskPriority,
    ) -> ScheduledAgentTask:
        graph = self._resolve_graph(parent.graph_id)
        agent_id = graph.agent_ids[parent.current_step]
        child = self._scheduler.enqueue(
            agent_id,
            priority=priority,
            payload=dict(parent.payload),
            parent_task_id=parent.parent_id,
        )
        parent.child_task_ids.append(child.task_id)
        parent.updated_at = datetime.now(UTC)
        return child
