import redis.asyncio as aioredis
import structlog

from aeo_api.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def check_redis() -> bool:
    try:
        client = await get_redis()
        return bool(await client.ping())
    except Exception:
        logger.exception("redis health check failed")
        return False


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
