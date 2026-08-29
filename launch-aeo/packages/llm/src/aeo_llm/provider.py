from typing import Protocol

from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class LLMResponse(BaseModel):
    content: str
    tokens_in: int = 0
    tokens_out: int = 0
    model: str = ""


class LLMProvider(Protocol):
    """LLM adapter interface per M01 specification."""

    async def chat(self, messages: list[Message], **kwargs: object) -> LLMResponse: ...

    async def embed(self, texts: list[str]) -> list[list[float]]: ...
