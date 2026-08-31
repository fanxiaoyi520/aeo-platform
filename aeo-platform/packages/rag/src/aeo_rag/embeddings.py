import asyncio
from concurrent.futures import Future, ThreadPoolExecutor
from typing import cast

from aeo_llm.openai_compatible import OpenAICompatibleProvider
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="rag-embed")


def _run_async(coro: object) -> object:
    """Run async coroutine from sync context, including inside a running event loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)  # type: ignore[arg-type]
    future: Future[object] = _executor.submit(asyncio.run, coro)  # type: ignore[arg-type]
    return future.result()


class LlmEmbeddingFunction(EmbeddingFunction[Documents]):
    """Chroma embedding function backed by LLMProvider.embed()."""

    def __init__(self) -> None:
        self._provider = OpenAICompatibleProvider()

    def __call__(self, input: Documents) -> Embeddings:
        return cast(Embeddings, _run_async(self._embed_async(list(input))))

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
