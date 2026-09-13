"""P5-08: Tenant quota management — plan-based task limits."""

from dataclasses import dataclass
from datetime import UTC, datetime

import structlog

from aeo_api.db.redis import get_redis

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class PlanQuota:
    plan: str
    monthly_tasks: int | None
    max_users: int
    description: str


PLAN_QUOTAS: dict[str, PlanQuota] = {
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


def get_plan_quota(plan: str) -> PlanQuota:
    return PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"])


def _usage_key(tenant_id: str) -> str:
    month = datetime.now(UTC).strftime("%Y-%m")
    return f"quota:tasks:{tenant_id}:{month}"


async def get_task_usage(tenant_id: str) -> int:
    redis = await get_redis()
    value = await redis.get(_usage_key(tenant_id))
    return int(value) if value else 0


async def check_task_quota(tenant_id: str, plan: str) -> tuple[bool, int, int | None]:
    quota = get_plan_quota(plan)
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
