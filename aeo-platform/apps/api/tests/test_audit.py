import logging
import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")
API_KEY = os.environ["AUTH_API_KEY"]

from aeo_api.db.models import AuditLog, get_db_session  # noqa: E402
from aeo_api.logging_setup import _redact_sensitive_fields  # noqa: E402
from aeo_api.main import app  # noqa: E402


async def _override_db_session() -> AsyncGenerator[AsyncMock, None]:
    session = AsyncMock()
    yield session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db_session] = _override_db_session
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac
    app.dependency_overrides.clear()


def _audit_entry(action: str) -> AuditLog:
    return AuditLog(
        id=uuid4(),
        task_id=uuid4(),
        action=action,
        actor="api",
        detail={"api_key": "secret", "task_id": "task-1"},
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_list_audit_logs_defaults_to_hitl_actions(client: AsyncClient) -> None:
    entries = [_audit_entry("hitl_approve"), _audit_entry("hitl_reject")]
    with patch("aeo_api.routers.audit._service.list_logs", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = [
            {
                "id": str(entry.id),
                "task_id": str(entry.task_id),
                "action": entry.action,
                "actor": entry.actor,
                "detail": {"api_key": "***", "task_id": "task-1"},
                "created_at": entry.created_at.isoformat(),
            }
            for entry in entries
        ]
        response = await client.get("/api/v1/audit-logs")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 2
    mock_list.assert_awaited_once()
    list_call = mock_list.await_args
    assert list_call is not None
    assert list_call.kwargs["actions"] == ["hitl_approve", "hitl_reject"]
    assert list_call.kwargs["limit"] == 100
    assert body["data"]["items"][0]["detail"]["api_key"] == "***"


@pytest.mark.asyncio
async def test_list_audit_logs_respects_limit(client: AsyncClient) -> None:
    with patch("aeo_api.routers.audit._service.list_logs", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = []
        response = await client.get("/api/v1/audit-logs?limit=50")

    assert response.status_code == 200
    list_call = mock_list.await_args
    assert list_call is not None
    assert list_call.kwargs["limit"] == 50


@pytest.mark.asyncio
async def test_audit_service_serializes_and_redacts_detail() -> None:
    from aeo_api.services.audit_service import AuditService

    service = AuditService()
    session = AsyncMock()
    entry = _audit_entry("hitl_approve")
    session.execute = AsyncMock(
        return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=lambda: [entry])))
    )
    items = await service.list_logs(session, actions=["hitl_approve"], limit=100)
    assert items[0]["detail"]["api_key"] == "***"


def test_setup_logging_redacts_sensitive_fields() -> None:
    event = {"event": "credential check", "api_key": "top-secret", "sku": "DEMO-001"}
    redacted = _redact_sensitive_fields(logging.getLogger("test"), "info", event)
    assert redacted["api_key"] == "***"
    assert redacted["sku"] == "DEMO-001"
