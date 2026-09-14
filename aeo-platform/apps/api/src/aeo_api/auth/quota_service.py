"""P5-08/P6-07: Tenant quota management — plan-based task limits with DB support."""

from dataclasses import dataclass
from datetime import UTC, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.db.redis import get_redis

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class PlanQuota:
    plan: str
    monthly_tasks: int | None
    max_users: int
    description: str


FALLBACK_QUOTAS: dict[str, PlanQuota] = {
    "free": PlanQuota(
        plan="free",
        monthly_tasks=10,
        max_users=3,
        description="Free tier — 10 tasks/month, 3 users",
    ),
    "pro": PlanQuota(
        plan="pro",
        monthly_tasks=100,
        max_users=10,
        description="Pro tier — 100 tasks/month, 10 users",
    ),
    "enterprise": PlanQuota(
        plan="enterprise",
        monthly_tasks=None,
        max_users=100,
        description="Enterprise tier — unlimited tasks, 100 users",
    ),
}


def get_fallback_quota(plan: str) -> PlanQuota:
    return FALLBACK_QUOTAS.get(plan, FALLBACK_QUOTAS["free"])


async def get_plan_quota_from_db(session: AsyncSession, plan: str) -> PlanQuota | None:
    from aeo_api.billing.models import Plan

    result = await session.execute(select(Plan).where(Plan.name == plan, Plan.is_active.is_(True)))
    db_plan = result.scalar_one_or_none()

    if db_plan is None:
        return None

    return PlanQuota(
        plan=db_plan.name,
        monthly_tasks=db_plan.monthly_tasks,
        max_users=db_plan.max_users,
        description=db_plan.description,
    )


async def get_plan_quota(session: AsyncSession | None, plan: str) -> PlanQuota:
    if session is not None:
        try:
            db_quota = await get_plan_quota_from_db(session, plan)
            if db_quota is not None:
                return db_quota
        except Exception as exc:
            logger.warning("quota.db_fallback", plan=plan, error=str(exc))

    return get_fallback_quota(plan)


def _usage_key(tenant_id: str) -> str:
    month = datetime.now(UTC).strftime("%Y-%m")
    return f"quota:tasks:{tenant_id}:{month}"


async def get_task_usage(tenant_id: str) -> int:
    redis = await get_redis()
    value = await redis.get(_usage_key(tenant_id))
    return int(value) if value else 0


async def check_task_quota(
    tenant_id: str, plan: str, session: AsyncSession | None = None
) -> tuple[bool, int, int | None]:
    quota = await get_plan_quota(session, plan)
    if quota.monthly_tasks is None:
        return True, await get_task_usage(tenant_id), None

    used = await get_task_usage(tenant_id)
    allowed = quota.monthly_tasks
    return used < allowed, used, allowed


async def increment_task_usage(tenant_id: str) -> int:
    redis = await get_redis()
    key = _usage_key(tenant_id)
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60 * 60 * 24 * 35)
    return count


async def reset_task_usage(tenant_id: str) -> None:
    redis = await get_redis()
    key = _usage_key(tenant_id)
    await redis.delete(key)


async def list_plans(session: AsyncSession) -> list[PlanQuota]:
    from aeo_api.billing.models import Plan

    result = await session.execute(
        select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.sort_order)
    )
    db_plans = result.scalars().all()

    if not db_plans:
        return list(FALLBACK_QUOTAS.values())

    return [
        PlanQuota(
            plan=p.name,
            monthly_tasks=p.monthly_tasks,
            max_users=p.max_users,
            description=p.description,
        )
        for p in db_plans
    ]
