"""P7-02: Redis caching service for hot data."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger()

DEFAULT_TTL_SECONDS = 300


class CacheService:
    """Redis-based caching service for hot data."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def get(self, key: str) -> Any | None:
        """Get cached value by key. Returns None if not found or expired."""
        try:
            value = await self._redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception:
            logger.exception("cache_get_failed", key=key)
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> bool:
        """Set cached value with TTL. Returns True on success."""
        try:
            serialized = json.dumps(value, ensure_ascii=False)
            await self._redis.set(key, serialized, ex=ttl_seconds)
            return True
        except Exception:
            logger.exception("cache_set_failed", key=key)
            return False

    async def delete(self, key: str) -> bool:
        """Delete cached value. Returns True on success."""
        try:
            await self._redis.delete(key)
            return True
        except Exception:
            logger.exception("cache_delete_failed", key=key)
            return False

    async def get_or_set(
        self,
        key: str,
        factory,  # type: ignore[no-untyped-def]
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> Any:
        """Get from cache or compute and cache if missing."""
        cached = await self.get(key)
        if cached is not None:
            logger.debug("cache_hit", key=key)
            return cached

        logger.debug("cache_miss", key=key)
        value = await factory()
        await self.set(key, value, ttl_seconds)
        return value

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern. Returns count of deleted keys."""
        try:
            cursor = 0
            deleted_count = 0
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted_count += await self._redis.delete(*keys)
                if cursor == 0:
                    break
            logger.info("cache_invalidated", pattern=pattern, count=deleted_count)
            return deleted_count
        except Exception:
            logger.exception("cache_invalidate_failed", pattern=pattern)
            return 0


def cache_key(*parts: str) -> str:
    """Build cache key from parts."""
    return ":".join(parts)


def ttl_minutes(minutes: int) -> int:
    """Convert minutes to seconds."""
    return int(timedelta(minutes=minutes).total_seconds())


def ttl_hours(hours: int) -> int:
    """Convert hours to seconds."""
    return int(timedelta(hours=hours).total_seconds())
