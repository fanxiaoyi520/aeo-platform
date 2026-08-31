"""Redis helper tests."""

from unittest.mock import AsyncMock, patch

import pytest
from aeo_api.db import redis as redis_module


@pytest.mark.asyncio
async def test_check_redis_success() -> None:
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    with patch.object(redis_module, "get_redis", AsyncMock(return_value=client)):
        assert await redis_module.check_redis() is True


@pytest.mark.asyncio
async def test_check_redis_failure() -> None:
    with patch.object(redis_module, "get_redis", AsyncMock(side_effect=ConnectionError("down"))):
        assert await redis_module.check_redis() is False


@pytest.mark.asyncio
async def test_close_redis_clears_client() -> None:
    client = AsyncMock()
    redis_module._redis_client = client
    await redis_module.close_redis()
    assert redis_module._redis_client is None
    client.aclose.assert_awaited_once()
