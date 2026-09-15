"""P6-07: Plan model and quota service tests."""

import os
from unittest.mock import AsyncMock, MagicMock

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")

import pytest
from aeo_api.auth.quota_service import (
    FALLBACK_QUOTAS,
    PlanQuota,
    get_fallback_quota,
    get_plan_quota,
    get_plan_quota_from_db,
    list_plans,
)
from aeo_api.billing.models import Plan


def test_plan_model_fields() -> None:
    plan = Plan(
        name="pro",
        display_name="Pro Plan",
        description="Pro tier with 100 tasks/month",
        stripe_price_monthly="price_pro_monthly",
        monthly_tasks=100,
        max_users=10,
        features={"priority_support": True},
        sort_order=2,
    )
    assert plan.name == "pro"
    assert plan.display_name == "Pro Plan"
    assert plan.description == "Pro tier with 100 tasks/month"
    assert plan.stripe_price_monthly == "price_pro_monthly"
    assert plan.monthly_tasks == 100
    assert plan.max_users == 10
    assert plan.features == {"priority_support": True}
    assert plan.sort_order == 2


def test_plan_model_optional_fields() -> None:
    plan = Plan(
        name="free",
        display_name="Free Plan",
        description="Free tier",
    )
    assert plan.stripe_price_monthly is None
    assert plan.stripe_price_yearly is None
    assert plan.monthly_tasks is None
    assert plan.features is None


def test_plan_quota_dataclass() -> None:
    quota = PlanQuota(
        plan="pro",
        monthly_tasks=100,
        max_users=10,
        description="Pro tier",
    )
    assert quota.plan == "pro"
    assert quota.monthly_tasks == 100
    assert quota.max_users == 10
    assert quota.description == "Pro tier"


def test_fallback_quotas_defined() -> None:
    assert "free" in FALLBACK_QUOTAS
    assert "pro" in FALLBACK_QUOTAS
    assert "enterprise" in FALLBACK_QUOTAS


def test_fallback_quotas_free() -> None:
    quota = FALLBACK_QUOTAS["free"]
    assert quota.monthly_tasks == 10
    assert quota.max_users == 3


def test_fallback_quotas_pro() -> None:
    quota = FALLBACK_QUOTAS["pro"]
    assert quota.monthly_tasks == 100
    assert quota.max_users == 10


def test_fallback_quotas_enterprise() -> None:
    quota = FALLBACK_QUOTAS["enterprise"]
    assert quota.monthly_tasks is None
    assert quota.max_users == 100


def test_get_fallback_quota_known() -> None:
    quota = get_fallback_quota("pro")
    assert quota.plan == "pro"
    assert quota.monthly_tasks == 100


def test_get_fallback_quota_unknown() -> None:
    quota = get_fallback_quota("unknown_plan")
    assert quota.plan == "free"


@pytest.mark.asyncio
async def test_get_plan_quota_from_db_found() -> None:
    mock_plan = MagicMock()
    mock_plan.name = "pro"
    mock_plan.monthly_tasks = 100
    mock_plan.max_users = 10
    mock_plan.description = "Pro tier"

    mock_session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = mock_plan
    mock_session.execute.return_value = result_mock

    quota = await get_plan_quota_from_db(mock_session, "pro")

    assert quota is not None
    assert quota.plan == "pro"
    assert quota.monthly_tasks == 100
    assert quota.max_users == 10


@pytest.mark.asyncio
async def test_get_plan_quota_from_db_not_found() -> None:
    mock_session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = result_mock

    quota = await get_plan_quota_from_db(mock_session, "nonexistent")

    assert quota is None


@pytest.mark.asyncio
async def test_get_plan_quota_with_db() -> None:
    mock_plan = MagicMock()
    mock_plan.name = "pro"
    mock_plan.monthly_tasks = 100
    mock_plan.max_users = 10
    mock_plan.description = "Pro tier"

    mock_session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = mock_plan
    mock_session.execute.return_value = result_mock

    quota = await get_plan_quota(mock_session, "pro")

    assert quota.plan == "pro"
    assert quota.monthly_tasks == 100


@pytest.mark.asyncio
async def test_get_plan_quota_fallback_on_db_error() -> None:
    mock_session = AsyncMock()
    mock_session.execute.side_effect = Exception("DB error")

    quota = await get_plan_quota(mock_session, "pro")

    assert quota.plan == "pro"
    assert quota.monthly_tasks == 100


@pytest.mark.asyncio
async def test_get_plan_quota_fallback_on_no_session() -> None:
    quota = await get_plan_quota(None, "pro")

    assert quota.plan == "pro"
    assert quota.monthly_tasks == 100


@pytest.mark.asyncio
async def test_get_plan_quota_fallback_on_not_found() -> None:
    mock_session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = result_mock

    quota = await get_plan_quota(mock_session, "unknown")

    assert quota.plan == "free"


@pytest.mark.asyncio
async def test_list_plans_from_db() -> None:
    mock_plan1 = MagicMock()
    mock_plan1.name = "free"
    mock_plan1.monthly_tasks = 10
    mock_plan1.max_users = 3
    mock_plan1.description = "Free tier"

    mock_plan2 = MagicMock()
    mock_plan2.name = "pro"
    mock_plan2.monthly_tasks = 100
    mock_plan2.max_users = 10
    mock_plan2.description = "Pro tier"

    mock_session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [mock_plan1, mock_plan2]
    mock_session.execute.return_value = result_mock

    plans = await list_plans(mock_session)

    assert len(plans) == 2
    assert plans[0].plan == "free"
    assert plans[1].plan == "pro"


@pytest.mark.asyncio
async def test_list_plans_fallback_on_empty() -> None:
    mock_session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = result_mock

    plans = await list_plans(mock_session)

    assert len(plans) == 3
    assert plans[0].plan == "free"
    assert plans[1].plan == "pro"
    assert plans[2].plan == "enterprise"
