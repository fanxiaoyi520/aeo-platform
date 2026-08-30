import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch
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

from aeo_api.main import app  # noqa: E402


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer dev-api-key-change-in-production"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac


def _task_payload(task_id: str | None = None) -> dict[str, object]:
    return {
        "id": task_id or str(uuid4()),
        "sku": "X431",
        "platform": "amazon",
        "market": "US",
        "status": "waiting_hitl",
        "product_info": {"competitor_asins": ["B001"]},
        "trace": [{"agent": "research_agent", "status": "completed"}],
        "final_output": None,
        "error_message": None,
        "created_at": "2026-08-30T00:00:00+00:00",
        "updated_at": "2026-08-30T00:00:00+00:00",
    }


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient) -> None:
    payload = _task_payload()
    with patch("aeo_api.routers.tasks._service.create_task", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = payload
        response = await client.post(
            "/api/v1/tasks",
            json={
                "sku": "X431",
                "platform": "amazon",
                "product_info": {"competitor_asins": ["B001"]},
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "waiting_hitl"


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient) -> None:
    with patch("aeo_api.routers.tasks._service.list_tasks", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = {
            "items": [_task_payload()],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }
        response = await client.get("/api/v1/tasks")
    assert response.status_code == 200
    assert response.json()["data"]["total"] == 1


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient) -> None:
    from aeo_api.services.task_service import TaskNotFoundError

    with patch("aeo_api.routers.tasks._service.get_task", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = TaskNotFoundError("missing")
        response = await client.get(f"/api/v1/tasks/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["code"] == 20001


@pytest.mark.asyncio
async def test_get_task_includes_generated(client: AsyncClient) -> None:
    task_id = str(uuid4())
    payload = _task_payload(task_id)
    payload["generated"] = {
        "title": "Draft Title",
        "bullets": ["Point A", "Point B"],
        "search_terms": "keyword",
        "description": "Draft body",
    }

    with patch("aeo_api.routers.tasks._service.get_task", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = payload
        response = await client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["generated"]["title"] == "Draft Title"
    assert len(data["generated"]["bullets"]) == 2


@pytest.mark.asyncio
async def test_approve_task_with_listing(client: AsyncClient) -> None:
    task_id = str(uuid4())
    completed = _task_payload(task_id)
    completed["status"] = "completed"
    completed["final_output"] = {"title": "Edited", "metrics": {"listing_version": 1}}
    listing = {"title": "Edited", "bullets": ["A"], "search_terms": "x", "description": "y"}

    with patch(
        "aeo_api.routers.tasks._service.approve_task", new_callable=AsyncMock
    ) as mock_approve:
        mock_approve.return_value = completed
        response = await client.post(
            f"/api/v1/tasks/{task_id}/approve",
            json={"listing": listing},
        )
    assert response.status_code == 200
    mock_approve.assert_awaited_once()
    call = mock_approve.await_args
    assert call is not None
    assert call.kwargs["listing"] == listing


@pytest.mark.asyncio
async def test_approve_task(client: AsyncClient) -> None:
    task_id = str(uuid4())
    completed = _task_payload(task_id)
    completed["status"] = "completed"
    completed["final_output"] = {"title": "Done", "metrics": {"listing_version": 1}}

    with patch(
        "aeo_api.routers.tasks._service.approve_task", new_callable=AsyncMock
    ) as mock_approve:
        mock_approve.return_value = completed
        response = await client.post(f"/api/v1/tasks/{task_id}/approve")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_reject_task_invalid_state(client: AsyncClient) -> None:
    from aeo_api.services.task_service import TaskStateError

    task_id = str(uuid4())
    with patch("aeo_api.routers.tasks._service.reject_task", new_callable=AsyncMock) as mock_reject:
        mock_reject.side_effect = TaskStateError("reject")
        response = await client.post(
            f"/api/v1/tasks/{task_id}/reject",
            json={"feedback": "Title too long"},
        )
    assert response.status_code == 409
    assert response.json()["code"] == 20020
