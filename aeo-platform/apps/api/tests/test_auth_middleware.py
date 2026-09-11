"""P5-04: Auth middleware tests — JWT + API key dual-mode."""

import os
from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")

API_KEY = "test-api-key-for-middleware"

from aeo_api.auth.context import current_tenant_id, current_user_id, current_user_role  # noqa: E402
from aeo_api.auth.jwt_service import create_access_token, create_refresh_token  # noqa: E402
from aeo_api.db.tenant_models import SYSTEM_TENANT_ID  # noqa: E402
from aeo_api.middleware.auth import AuthMiddleware  # noqa: E402


def _build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(AuthMiddleware, api_key=API_KEY)

    @app.get("/api/v1/test-auth")
    async def test_endpoint(request: Request) -> dict[str, Any]:
        return {
            "tenant_id": getattr(request.state, "tenant_id", None),
            "user_id": getattr(request.state, "user_id", None),
            "role": getattr(request.state, "user_role", None),
            "ctx_tenant": current_tenant_id.get(),
            "ctx_user": current_user_id.get(),
            "ctx_role": current_user_role.get(),
        }

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok"}

    return app


@pytest.fixture
def tenant_id() -> str:
    return str(uuid4())


@pytest.fixture
def user_id() -> str:
    return str(uuid4())


@pytest.fixture
def access_token(tenant_id: str, user_id: str) -> str:
    from uuid import UUID

    return create_access_token(UUID(user_id), UUID(tenant_id), "admin")


@pytest.fixture
def refresh_token(tenant_id: str, user_id: str) -> str:
    from uuid import UUID

    return create_refresh_token(UUID(user_id), UUID(tenant_id))


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app = _build_test_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_public_path_bypasses_auth(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_valid_jwt_sets_tenant_and_user(
    client: AsyncClient, access_token: str, tenant_id: str, user_id: str
) -> None:
    response = await client.get(
        "/api/v1/test-auth",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == tenant_id
    assert data["user_id"] == user_id
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_jwt_sets_context_vars(
    client: AsyncClient, access_token: str, tenant_id: str, user_id: str
) -> None:
    response = await client.get(
        "/api/v1/test-auth",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    data = response.json()
    assert data["ctx_tenant"] == tenant_id
    assert data["ctx_user"] == user_id
    assert data["ctx_role"] == "admin"


@pytest.mark.asyncio
async def test_refresh_token_rejected(client: AsyncClient, refresh_token: str) -> None:
    response = await client.get(
        "/api/v1/test-auth",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_key_sets_system_tenant(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/test-auth",
        headers={"Authorization": f"Bearer {API_KEY}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == SYSTEM_TENANT_ID
    assert data["user_id"] == "system"
    assert data["role"] == "owner"


@pytest.mark.asyncio
async def test_invalid_token_and_invalid_api_key(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/test-auth",
        headers={"Authorization": "Bearer totally-bogus-token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_no_auth_header(client: AsyncClient) -> None:
    response = await client.get("/api/v1/test-auth")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_empty_bearer(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/test-auth",
        headers={"Authorization": "Bearer "},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_context_vars_reset_after_request(client: AsyncClient, access_token: str) -> None:
    await client.get(
        "/api/v1/test-auth",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert current_tenant_id.get() is None
    assert current_user_id.get() is None
    assert current_user_role.get() == "member"
