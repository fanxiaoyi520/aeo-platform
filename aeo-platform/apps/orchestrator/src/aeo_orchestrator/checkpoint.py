"""Checkpoint factory — MemorySaver (dev/test) or AsyncPostgresSaver (production)."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from langgraph.checkpoint.memory import MemorySaver

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


def normalize_postgres_conn_string(url: str) -> str:
    """Convert SQLAlchemy-style URLs to psycopg connection strings."""
    return (
        url.replace("postgresql+psycopg://", "postgresql://")
        .replace("postgresql+asyncpg://", "postgresql://")
        .replace("postgres+psycopg://", "postgresql://")
    )


def get_checkpoint_db_url() -> str | None:
    """Resolve Postgres URL for LangGraph checkpoints."""
    raw = os.environ.get("CHECKPOINT_DB_URL") or os.environ.get("DB_URL_SYNC")
    if not raw:
        return None
    return normalize_postgres_conn_string(raw)


def create_memory_checkpointer() -> MemorySaver:
    return MemorySaver()


def create_checkpointer(*, use_postgres: bool | None = None) -> BaseCheckpointSaver[Any]:
    """Return MemorySaver unless Postgres is explicitly enabled and configured."""
    if use_postgres is None:
        use_postgres = os.environ.get("ORCHESTRATOR_CHECKPOINT_POSTGRES", "false").lower() == "true"
    if use_postgres:
        conn = get_checkpoint_db_url()
        if not conn:
            raise ValueError(
                "ORCHESTRATOR_CHECKPOINT_POSTGRES=true but no CHECKPOINT_DB_URL/DB_URL_SYNC"
            )
        msg = (
            "Use AsyncPostgresSaver.from_conn_string() as an async context manager "
            "and pass the saver to build_graph(checkpointer=...)."
        )
        raise RuntimeError(msg)
    return create_memory_checkpointer()


@asynccontextmanager
async def postgres_checkpointer(
    conn_string: str | None = None,
) -> AsyncIterator[AsyncPostgresSaver]:
    """Async context manager that sets up LangGraph Postgres checkpoint tables."""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    url = conn_string or get_checkpoint_db_url()
    if not url:
        raise ValueError("CHECKPOINT_DB_URL or DB_URL_SYNC is required for Postgres checkpoints")
    async with AsyncPostgresSaver.from_conn_string(url) as saver:
        await saver.setup()
        yield saver
