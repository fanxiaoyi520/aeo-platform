import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from aeo_llm.config import get_llm_settings
from aeo_llm.provider import LLMProvider, LLMResponse, Message


def _deepseek_v4_model(model: str) -> bool:
    return model.lower().startswith("deepseek-v4")


class OpenAICompatibleProvider:
    """OpenAI-compatible LLM gateway (supports company internal gateway)."""

    def __init__(self) -> None:
        self._settings = get_llm_settings()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def chat(self, messages: list[Message], **kwargs: object) -> LLMResponse:
        raw_timeout = kwargs.get("timeout")
        if isinstance(raw_timeout, (int, float)):
            timeout = float(raw_timeout)
        else:
            timeout = float(self._settings.llm_timeout_seconds)
        model = str(kwargs.get("model", self._settings.llm_model))

        payload: dict[str, object] = {
            "model": model,
            "messages": [m.model_dump() for m in messages],
            "temperature": kwargs.get("temperature", 0.3),
        }
        if _deepseek_v4_model(model):
            # DeepSeek V4 defaults to thinking mode; plain JSON chat needs it off.
            payload["thinking"] = {"type": "disabled"}

        async with httpx.AsyncClient(
            base_url=self._settings.llm_base_url,
            timeout=timeout,
        ) as client:
            response = await client.post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {self._settings.llm_api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            content=choice,
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            model=model,
        )

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def embed(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(
            base_url=self._settings.embed_base_url,
            timeout=float(self._settings.llm_timeout_seconds),
        ) as client:
            response = await client.post(
                "/embeddings",
                headers={"Authorization": f"Bearer {self._settings.embed_api_key}"},
                json={"model": self._settings.embed_model, "input": texts},
            )
            response.raise_for_status()
            data = response.json()

        return [item["embedding"] for item in data["data"]]


def get_llm_provider() -> LLMProvider:
    return OpenAICompatibleProvider()
