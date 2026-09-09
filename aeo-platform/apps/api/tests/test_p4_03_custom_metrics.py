"""Tests for P4-03 custom Prometheus metrics."""

from __future__ import annotations

import os

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo_dev_password@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo_dev_password@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")


def test_metrics_module_importable() -> None:
    from aeo_api.metrics import (
        AGENT_EXECUTION_DURATION_SECONDS,
        AGENT_EXECUTIONS_TOTAL,
        HTTP_REQUEST_DURATION_SECONDS,
        HTTP_REQUESTS_TOTAL,
        LLM_CALLS_TOTAL,
        RAG_QUERIES_TOTAL,
        SYSTEM_INFO,
        TASKS_TOTAL,
    )

    assert HTTP_REQUESTS_TOTAL is not None
    assert HTTP_REQUEST_DURATION_SECONDS is not None
    assert AGENT_EXECUTIONS_TOTAL is not None
    assert AGENT_EXECUTION_DURATION_SECONDS is not None
    assert LLM_CALLS_TOTAL is not None
    assert RAG_QUERIES_TOTAL is not None
    assert SYSTEM_INFO is not None
    assert TASKS_TOTAL is not None


def test_http_requests_counter() -> None:
    from aeo_api.metrics import HTTP_REQUESTS_TOTAL

    HTTP_REQUESTS_TOTAL.labels(method="GET", endpoint="/test", status="200").inc()
    HTTP_REQUESTS_TOTAL.labels(method="POST", endpoint="/api/v1/tasks", status="201").inc()


def test_agent_execution_counter() -> None:
    from aeo_api.metrics import AGENT_EXECUTION_DURATION_SECONDS, AGENT_EXECUTIONS_TOTAL

    AGENT_EXECUTIONS_TOTAL.labels(agent="research_agent", status="completed").inc()
    AGENT_EXECUTION_DURATION_SECONDS.labels(agent="research_agent").observe(1.5)


def test_llm_calls_counter() -> None:
    from aeo_api.metrics import LLM_CALL_DURATION_SECONDS, LLM_CALLS_TOTAL, LLM_TOKENS_TOTAL

    LLM_CALLS_TOTAL.labels(provider="deepseek", status="success").inc()
    LLM_CALL_DURATION_SECONDS.labels(provider="deepseek").observe(2.3)
    LLM_TOKENS_TOTAL.labels(provider="deepseek", type="input").inc(100)
    LLM_TOKENS_TOTAL.labels(provider="deepseek", type="output").inc(50)


def test_rag_metrics() -> None:
    from aeo_api.metrics import RAG_CHUNKS_TOTAL, RAG_DOCUMENTS_LOADED, RAG_QUERIES_TOTAL

    RAG_QUERIES_TOTAL.labels(status="success").inc()
    RAG_DOCUMENTS_LOADED.set(42)
    RAG_CHUNKS_TOTAL.set(1000)


def test_system_info_gauge() -> None:
    from aeo_api.metrics import SYSTEM_INFO

    SYSTEM_INFO.labels(version="0.1.0", python_version="3.11").set(1)


def test_metrics_endpoint_includes_custom_metrics() -> None:
    import pytest
    from aeo_api.main import app
    from httpx import ASGITransport, AsyncClient

    @pytest.mark.asyncio
    async def _check() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/metrics")
        assert response.status_code == 200
        body = response.text
        assert "aeo_http_requests_total" in body or "aeo_system_info" in body

    import asyncio

    asyncio.run(_check())


def test_prometheus_middleware_importable() -> None:
    from aeo_api.middleware.prometheus import PrometheusMiddleware

    assert PrometheusMiddleware is not None


def test_prometheus_middleware_normalize_path() -> None:
    from aeo_api.middleware.prometheus import PrometheusMiddleware

    assert PrometheusMiddleware._normalize_path("/health") == "/health"
    assert PrometheusMiddleware._normalize_path("/api/v1/tasks") == "/api/v1/tasks"
    path = PrometheusMiddleware._normalize_path("/api/v1/tasks/abc123def/events")
    assert ":id" in path


def test_task_metrics() -> None:
    from aeo_api.metrics import TASKS_IN_PROGRESS, TASKS_TOTAL

    TASKS_TOTAL.labels(platform="shopify", status="created").inc()
    TASKS_IN_PROGRESS.inc()
    TASKS_IN_PROGRESS.dec()


def test_database_redis_gauges() -> None:
    from aeo_api.metrics import DATABASE_CONNECTIONS_ACTIVE, REDIS_CONNECTIONS_ACTIVE

    DATABASE_CONNECTIONS_ACTIVE.set(5)
    REDIS_CONNECTIONS_ACTIVE.set(3)
