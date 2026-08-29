import asyncio
from typing import cast

from aeo_llm.openai_compatible import OpenAICompatibleProvider
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings


class LlmEmbeddingFunction(EmbeddingFunction[Documents]):
    """Chroma embedding function backed by LLMProvider.embed()."""

    def __init__(self) -> None:
        self._provider = OpenAICompatibleProvider()

    def __call__(self, input: Documents) -> Embeddings:
        return asyncio.run(self._embed_async(list(input)))

    async def _embed_async(self, texts: list[str]) -> Embeddings:
        if not texts:
            return []
        vectors = await self._provider.embed(texts)
        return cast(Embeddings, vectors)


class HashEmbeddingFunction(EmbeddingFunction[Documents]):
    """Deterministic local embeddings for tests (no API calls)."""

    def __call__(self, input: Documents) -> Embeddings:
        import hashlib

        result: list[list[float]] = []
        for text in input:
            digest = hashlib.sha256(text.encode()).digest()
            vec = [((b / 255.0) * 2 - 1) for b in digest[:32]]
            while len(vec) < 64:
                vec.extend(vec[: min(64 - len(vec), len(vec))])
            result.append(vec[:64])
        return cast(Embeddings, result)
