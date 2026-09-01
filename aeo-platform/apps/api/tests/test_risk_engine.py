import os
from collections.abc import AsyncGenerator
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


class TestRiskEngine:
    """MV1-05: RiskEngine service tests."""

    @pytest.mark.asyncio
    async def test_evaluate_l0_research_auto_allow(self) -> None:
        """L0 research.read should be auto-allowed."""
        from aeo_api.services.risk_engine import RiskEngine

        engine = RiskEngine()
        session = AsyncMock()
        session.add = MagicMock()

        decision = await engine.evaluate(
            session,
            action="research.read",
            context={"sku": "DEMO-001"},
        )

        assert decision.allowed is True
        assert decision.risk_level == "L0"
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_l1_listing_publish_requires_hitl(self) -> None:
        """L1 listing.publish should require human approval."""
        from aeo_api.services.risk_engine import RiskEngine

        engine = RiskEngine()
        session = AsyncMock()
        session.add = MagicMock()

        decision = await engine.evaluate(
            session,
            action="listing.publish",
            context={"sku": "DEMO-001", "platform": "amazon"},
        )

        assert decision.allowed is False
        assert decision.effect == "require_hitl"
        assert decision.risk_level == "L1"
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_l2_high_budget_denied(self) -> None:
        """L2 high budget should be denied."""
        from aeo_api.services.risk_engine import RiskEngine

        engine = RiskEngine()
        session = AsyncMock()
        session.add = MagicMock()

        decision = await engine.evaluate(
            session,
            action="ads.budget_change",
            context={"daily_budget": 15000},
        )

        assert decision.allowed is False
        assert decision.effect == "deny"
        assert decision.risk_level == "L2"
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_l1_price_update_requires_hitl(self) -> None:
        """L1 price.update should require human approval."""
        from aeo_api.services.risk_engine import RiskEngine

        engine = RiskEngine()
        session = AsyncMock()
        session.add = MagicMock()

        decision = await engine.evaluate(
            session,
            action="price.update",
            context={"sku": "DEMO-001", "new_price": 29.99},
        )

        assert decision.allowed is False
        assert decision.effect == "require_hitl"
        assert decision.risk_level == "L1"

    @pytest.mark.asyncio
    async def test_audit_log_records_risk_decision(self) -> None:
        """Each evaluation should record audit log with decision details."""
        from aeo_api.services.risk_engine import RiskEngine

        engine = RiskEngine()
        session = AsyncMock()
        captured_add = MagicMock()
        session.add = captured_add

        await engine.evaluate(
            session,
            action="listing.publish",
            context={"sku": "DEMO-001"},
            actor="test_agent",
        )

        captured_add.assert_called_once()
        audit_entry = captured_add.call_args[0][0]
        assert audit_entry.action == "risk.evaluate"
        assert audit_entry.actor == "test_agent"
        assert audit_entry.detail["action"] == "listing.publish"
        assert audit_entry.detail["effect"] == "require_hitl"
        assert audit_entry.detail["rule_id"] == "l1_listing_publish"


class TestRiskAPI:
    """MV1-05: Risk API endpoint tests."""

    @pytest.mark.asyncio
    async def test_post_risk_evaluate_returns_decision(self, client: AsyncClient) -> None:
        """POST /api/v1/risk/evaluate should return risk decision."""
        from aeo_shared.agent_registry import RiskLevel
        from aeo_shared.risk_dsl import RiskDecision, RiskEffect

        with patch(
            "aeo_api.routers.risk._engine.evaluate",
            new_callable=AsyncMock,
        ) as mock_eval:
            mock_eval.return_value = RiskDecision(
                allowed=False,
                effect=RiskEffect.REQUIRE_HITL,
                risk_level=RiskLevel.L1,
                rule_id="l1_listing_publish",
                message="Listing publish requires human approval.",
            )
            response = await client.post(
                "/api/v1/risk/evaluate",
                json={"action": "listing.publish", "context": {"sku": "DEMO-001"}},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["allowed"] is False
        assert body["data"]["effect"] == "require_hitl"
        assert body["data"]["risk_level"] == "L1"

    @pytest.mark.asyncio
    async def test_get_risk_audit_returns_decisions(self, client: AsyncClient) -> None:
        """GET /api/v1/risk/audit should return risk decision history."""
        with patch(
            "aeo_api.routers.risk._service.list_risk_logs",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = [
                {
                    "id": str(uuid4()),
                    "action": "risk.evaluate",
                    "actor": "generate_agent",
                    "detail": {
                        "action": "listing.publish",
                        "effect": "require_hitl",
                        "risk_level": "L1",
                        "rule_id": "l1_listing_publish",
                    },
                    "created_at": "2026-09-01T10:00:00+00:00",
                }
            ]
            response = await client.get("/api/v1/risk/audit")

        assert response.status_code == 200
        body = response.json()
        assert body["code"] == 0
        assert body["data"]["total"] == 1
        assert body["data"]["items"][0]["detail"]["effect"] == "require_hitl"

    @pytest.mark.asyncio
    async def test_get_risk_audit_filters_by_action(self, client: AsyncClient) -> None:
        """GET /api/v1/risk/audit?action=listing.publish should filter results."""
        with patch(
            "aeo_api.routers.risk._service.list_risk_logs",
            new_callable=AsyncMock,
        ) as mock_list:
            mock_list.return_value = []
            response = await client.get("/api/v1/risk/audit?action=listing.publish")

        assert response.status_code == 200
        mock_list.assert_awaited_once()
        assert mock_list.await_args is not None
        call_kwargs = mock_list.await_args.kwargs
        assert call_kwargs["evaluated_action"] == "listing.publish"
