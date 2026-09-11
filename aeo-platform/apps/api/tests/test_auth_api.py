"""P5-03: Auth API endpoint tests."""

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
API_KEY = os.environ["AUTH_API_KEY"]

from aeo_api.main import app  # noqa: E402


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac


@pytest.fixture
async def public_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _mock_user(**overrides: object) -> object:
    defaults = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "email": "test@example.com",
        "display_name": "Test User",
        "role": "owner",
        "hashed_password": "fake",
        "is_active": True,
    }
    defaults.update(overrides)
    return type("MockUser", (), defaults)()


@pytest.mark.asyncio
async def test_signup_success(public_client: AsyncClient) -> None:
    mock_user = _mock_user()
    with (
        patch("aeo_api.routers.auth.signup", new_callable=AsyncMock) as mock_signup,
        patch("aeo_api.auth.jwt_service.create_access_token", return_value="access-token"),
        patch("aeo_api.auth.jwt_service.create_refresh_token", return_value="refresh-token"),
    ):
        mock_signup.return_value = (mock_user, type("MockTenant", (), {"id": uuid4()})())
        response = await public_client.post(
            "/api/v1/auth/signup",
            json={
                "email": "test@example.com",
                "password": "secure123",
                "tenant_name": "Test Corp",
                "tenant_slug": "test-corp",
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["access_token"] == "access-token"
    assert body["data"]["user"]["email"] == "test@example.com"
    assert body["data"]["user"]["role"] == "owner"


@pytest.mark.asyncio
async def test_signup_duplicate_slug(public_client: AsyncClient) -> None:
    from aeo_api.auth.auth_service import AuthError

    with patch("aeo_api.routers.auth.signup", new_callable=AsyncMock) as mock_signup:
        mock_signup.side_effect = AuthError("Tenant slug 'test' already exists")
        response = await public_client.post(
            "/api/v1/auth/signup",
            json={
                "email": "test@example.com",
                "password": "secure123",
                "tenant_name": "Test",
                "tenant_slug": "test",
            },
        )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(public_client: AsyncClient) -> None:
    mock_user = _mock_user()
    with patch("aeo_api.routers.auth.login", new_callable=AsyncMock) as mock_login:
        mock_login.return_value = (mock_user, "access-token", "refresh-token")
        response = await public_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "secure123"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["access_token"] == "access-token"
    assert body["data"]["refresh_token"] == "refresh-token"


@pytest.mark.asyncio
async def test_login_invalid_credentials(public_client: AsyncClient) -> None:
    from aeo_api.auth.auth_service import AuthError

    with patch("aeo_api.routers.auth.login", new_callable=AsyncMock) as mock_login:
        mock_login.side_effect = AuthError("Invalid credentials")
        response = await public_client.post(
            "/api/v1/auth/login",
            json={"email": "wrong@example.com", "password": "wrong"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_success(public_client: AsyncClient) -> None:
    with patch("aeo_api.routers.auth.refresh_tokens", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = ("new-access", "new-refresh")
        response = await public_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "valid-refresh-token"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["access_token"] == "new-access"


@pytest.mark.asyncio
async def test_refresh_invalid_token(public_client: AsyncClient) -> None:
    from aeo_api.auth.auth_service import AuthError

    with patch("aeo_api.routers.auth.refresh_tokens", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.side_effect = AuthError("Invalid refresh token")
        response = await public_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_api_key_returns_system_identity(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user_id"] == "system"
    assert data["role"] == "owner"


@pytest.mark.asyncio
async def test_me_requires_auth(public_client: AsyncClient) -> None:
    response = await public_client.post("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_signup_validation_error(public_client: AsyncClient) -> None:
    response = await public_client.post(
        "/api/v1/auth/signup",
        json={"email": "not-an-email", "password": "123"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_rbac_role_hierarchy() -> None:
    from aeo_api.auth.rbac import ROLE_HIERARCHY

    assert ROLE_HIERARCHY["owner"] > ROLE_HIERARCHY["admin"]
    assert ROLE_HIERARCHY["admin"] > ROLE_HIERARCHY["member"]
    assert ROLE_HIERARCHY["member"] > 0
