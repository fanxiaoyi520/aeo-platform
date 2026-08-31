import os
from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock, patch

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
os.environ.setdefault("RAG_USE_HASH_EMBEDDINGS", "true")
os.environ.setdefault("RAG_SCORE_THRESHOLD", "0.0")

from aeo_api.db.models import get_db_session  # noqa: E402
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


@pytest.mark.asyncio
async def test_knowledge_reindex_and_search(client: AsyncClient) -> None:
    with (
        patch("aeo_api.services.knowledge_service.get_knowledge_store") as mock_store,
        patch("aeo_api.routers.knowledge._audit.record", new_callable=AsyncMock) as mock_audit,
    ):
        from aeo_rag.store import SearchResult

        mock_instance = mock_store.return_value
        mock_instance.count.return_value = 5
        mock_instance.ingest_documents.return_value = 5

        reindex_resp = await client.post("/api/v1/knowledge/reindex")
        assert reindex_resp.status_code == 200
        body = reindex_resp.json()
        assert body["code"] == 0
        mock_audit.assert_awaited_once()
        audit_call = mock_audit.await_args
        assert audit_call is not None
        assert audit_call.kwargs["action"] == "knowledge_reindex"

        mock_instance.search.return_value = [
            SearchResult(
                doc_id="test-id",
                content="Title max 200 characters",
                score=0.95,
                category="amazon_rules",
                platform="amazon",
                source_file="amazon/listing-rules.md",
                chunk_index=0,
            )
        ]

        search_resp = await client.post(
            "/api/v1/knowledge/search",
            json={"query": "Amazon title length", "platform": "amazon"},
        )
        assert search_resp.status_code == 200
        data = search_resp.json()["data"]
        assert data["total"] >= 1
        assert "200" in data["results"][0]["content"]


@pytest.mark.asyncio
async def test_knowledge_list_documents(client: AsyncClient) -> None:
    with patch("aeo_api.services.knowledge_service.KnowledgeService.list_documents") as mock_list:
        mock_list.return_value = [
            {
                "source_file": "products/sample-product.md",
                "size_bytes": 120,
                "extension": ".md",
                "updated_at": "2026-08-30T00:00:00+00:00",
            }
        ]

        response = await client.get("/api/v1/knowledge/documents")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 1
        assert data["items"][0]["source_file"] == "products/sample-product.md"


@pytest.mark.asyncio
async def test_knowledge_upload_md(client: AsyncClient, tmp_path: Path) -> None:
    knowledge_root = tmp_path / "knowledge"
    knowledge_root.mkdir()

    with (
        patch(
            "aeo_api.services.knowledge_service.resolve_project_path",
            return_value=knowledge_root,
        ),
        patch("aeo_api.services.knowledge_service.get_knowledge_store") as mock_store,
        patch("aeo_api.routers.knowledge._audit.record", new_callable=AsyncMock) as mock_audit,
    ):
        mock_instance = mock_store.return_value
        mock_instance.count.return_value = 3
        mock_instance.ingest_documents.return_value = 3

        files = {"file": ("product.md", b"# Product\nSKU DEMO-001", "text/markdown")}
        response = await client.post(
            "/api/v1/knowledge/upload",
            data={"category": "products"},
            files=files,
        )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["source_file"] == "products/product.md"
        assert (knowledge_root / "products" / "product.md").exists()
        mock_audit.assert_awaited_once()
        audit_call = mock_audit.await_args
        assert audit_call is not None
        assert audit_call.kwargs["action"] == "knowledge_upload"


@pytest.mark.asyncio
async def test_knowledge_upload_rejects_invalid_type(client: AsyncClient) -> None:
    files = {"file": ("virus.exe", b"bad", "application/octet-stream")}
    response = await client.post(
        "/api/v1/knowledge/upload",
        data={"category": "uploads"},
        files=files,
    )
    assert response.status_code == 400
