"""MS6 acceptance — production hardening per M06 §5."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from aeo_shared.redaction import SENSITIVE_KEYS
from httpx import ASGITransport, AsyncClient

_AEO_PLATFORM_ROOT = Path(__file__).resolve().parents[3]
_REPO_ROOT = _AEO_PLATFORM_ROOT.parent

_REQUIRED_MS6_ARTIFACTS = [
    "infra/compose/docker-compose.prod.yml",
    ".env.prod.example",
    "scripts/prod-up.ps1",
    "scripts/prod-down.ps1",
    "scripts/backup.sh",
    "scripts/backup.ps1",
    "scripts/demo.ps1",
    "infra/docker/Dockerfile.web",
    "infra/docker/Dockerfile.api",
    "apps/api/src/aeo_api/middleware/rate_limit.py",
    "apps/api/src/aeo_api/middleware/request_id.py",
    "packages/shared/src/aeo_shared/redaction.py",
    "apps/api/src/aeo_api/routers/audit.py",
]

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")
API_KEY = os.environ["AUTH_API_KEY"]

from aeo_api.db.models import get_db_session  # noqa: E402
from aeo_api.main import app  # noqa: E402


async def _override_db_session() -> AsyncGenerator[AsyncMock, None]:
    session = AsyncMock()
    yield session


@pytest.fixture
async def authed_client() -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db_session] = _override_db_session
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.parametrize("relative_path", _REQUIRED_MS6_ARTIFACTS)
def test_ms6_required_artifacts_exist(relative_path: str) -> None:
    path = _AEO_PLATFORM_ROOT / relative_path
    assert path.is_file(), f"missing MS6 artifact: {relative_path}"


def test_ms6_deployment_doc_exists() -> None:
    doc = _REPO_ROOT / "docs" / "DEPLOYMENT.md"
    assert doc.is_file()


def test_ms6_prod_compose_supports_offline_hash_embeddings() -> None:
    """M06 §5.1 — prod can start without external embedding API."""
    compose_path = _AEO_PLATFORM_ROOT / "infra/compose/docker-compose.prod.yml"
    env_path = _AEO_PLATFORM_ROOT / ".env.prod.example"
    compose = compose_path.read_text(encoding="utf-8")
    env_example = env_path.read_text(encoding="utf-8")
    assert 'RAG_USE_HASH_EMBEDDINGS: "true"' in compose
    assert "RAG_USE_HASH_EMBEDDINGS=true" in env_example


def test_ms6_env_prod_example_documents_security_controls() -> None:
    text = (_AEO_PLATFORM_ROOT / ".env.prod.example").read_text(encoding="utf-8")
    for key in ("AUTH_API_KEY", "CORS_ORIGINS", "RATE_LIMIT_PER_MINUTE", "POSTGRES_PASSWORD"):
        assert key in text, f"missing {key} in .env.prod.example"


def test_ms6_redaction_keys_match_m06_spec() -> None:
    assert frozenset({"api_key", "password", "supplier_price", "cost_price"}) == SENSITIVE_KEYS


@pytest.mark.asyncio
async def test_ms6_unauthenticated_api_returns_401() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/tasks")
    assert response.status_code == 401
    body = response.json()
    assert body["code"] == 10002


@pytest.mark.asyncio
async def test_ms6_audit_logs_default_hitl_and_limit_100(authed_client: AsyncClient) -> None:
    with patch("aeo_api.routers.audit._service.list_logs", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = []
        response = await authed_client.get("/api/v1/audit-logs")
        assert response.status_code == 200
        list_call = mock_list.await_args
        assert list_call is not None
        assert list_call.kwargs["limit"] == 100

    over_limit = await authed_client.get("/api/v1/audit-logs?limit=101")
    assert over_limit.status_code == 422


def test_ms6_acceptance_report_exists() -> None:
    report = _REPO_ROOT / "docs" / "reports" / "ms6-deployment-acceptance.md"
    assert report.is_file(), "missing MS6 acceptance report"
