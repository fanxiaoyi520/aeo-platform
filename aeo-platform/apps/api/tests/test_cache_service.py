"""P7-02: Cache service tests."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock

import pytest

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo_dev_password@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo_dev_password@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")


@pytest.mark.asyncio
async def test_cache_service_get_returns_none_when_missing() -> None:
    from aeo_api.services.cache import CacheService

    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)

    service = CacheService(redis)
    result = await service.get("missing-key")

    assert result is None
    redis.get.assert_awaited_once_with("missing-key")


@pytest.mark.asyncio
async def test_cache_service_get_returns_deserialized_value() -> None:
    from aeo_api.services.cache import CacheService

    redis = AsyncMock()
    redis.get = AsyncMock(return_value='{"name": "test", "value": 42}')

    service = CacheService(redis)
    result = await service.get("test-key")

    assert result == {"name": "test", "value": 42}


@pytest.mark.asyncio
async def test_cache_service_set_serializes_and_sets_ttl() -> None:
    from aeo_api.services.cache import CacheService

    redis = AsyncMock()
    redis.set = AsyncMock()

    service = CacheService(redis)
    result = await service.set("test-key", {"data": "value"}, ttl_seconds=60)

    assert result is True
    redis.set.assert_awaited_once()
    call_args = redis.set.call_args
    assert call_args[0][0] == "test-key"
    assert '"data"' in call_args[0][1]
    assert call_args[1]["ex"] == 60


@pytest.mark.asyncio
async def test_cache_service_delete_removes_key() -> None:
    from aeo_api.services.cache import CacheService

    redis = AsyncMock()
    redis.delete = AsyncMock()

    service = CacheService(redis)
    result = await service.delete("test-key")

    assert result is True
    redis.delete.assert_awaited_once_with("test-key")


@pytest.mark.asyncio
async def test_cache_service_get_or_set_returns_cached() -> None:
    from aeo_api.services.cache import CacheService

    redis = AsyncMock()
    redis.get = AsyncMock(return_value='{"cached": true}')
    redis.set = AsyncMock()

    service = CacheService(redis)
    factory = AsyncMock(return_value={"cached": False})

    result = await service.get_or_set("test-key", factory)

    assert result == {"cached": True}
    factory.assert_not_awaited()
    redis.set.assert_not_awaited()


@pytest.mark.asyncio
async def test_cache_service_get_or_set_computes_on_miss() -> None:
    from aeo_api.services.cache import CacheService

    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()

    service = CacheService(redis)
    factory = AsyncMock(return_value={"computed": True})

    result = await service.get_or_set("test-key", factory)

    assert result == {"computed": True}
    factory.assert_awaited_once()
    redis.set.assert_awaited_once()


def test_cache_key_builds_from_parts() -> None:
    from aeo_api.services.cache import cache_key

    assert cache_key("user", "123", "profile") == "user:123:profile"


def test_ttl_minutes_converts_correctly() -> None:
    from aeo_api.services.cache import ttl_minutes

    assert ttl_minutes(5) == 300
    assert ttl_minutes(60) == 3600


def test_ttl_hours_converts_correctly() -> None:
    from aeo_api.services.cache import ttl_hours

    assert ttl_hours(1) == 3600
    assert ttl_hours(24) == 86400
