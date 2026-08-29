import os

import pytest

os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")

from aeo_llm.provider import Message  # noqa: E402


def test_message_model() -> None:
    msg = Message(role="user", content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"


@pytest.mark.asyncio
async def test_openai_provider_chat_mock() -> None:
    from unittest.mock import AsyncMock, MagicMock, patch

    from aeo_llm.openai_compatible import OpenAICompatibleProvider

    provider = OpenAICompatibleProvider()

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "test output"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("aeo_llm.openai_compatible.httpx.AsyncClient", return_value=mock_client):
        result = await provider.chat([Message(role="user", content="hi")])

    assert result.content == "test output"
    assert result.tokens_in == 10
    assert result.tokens_out == 5
