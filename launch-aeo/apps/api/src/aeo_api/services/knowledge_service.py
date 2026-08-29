from functools import lru_cache

from aeo_rag.config import get_rag_settings, resolve_project_path
from aeo_rag.loaders import load_knowledge_dir
from aeo_rag.store import KnowledgeStore, SearchResult


@lru_cache
def get_knowledge_store() -> KnowledgeStore:
    import os

    use_hash = os.environ.get("RAG_USE_HASH_EMBEDDINGS", "false").lower() == "true"
    return KnowledgeStore(use_hash_embeddings=use_hash)


class KnowledgeService:
    def search(
        self,
        query: str,
        *,
        platform: str | None = None,
        category: str | None = None,
        top_k: int | None = None,
    ) -> list[SearchResult]:
        return get_knowledge_store().search(
            query, platform=platform, category=category, top_k=top_k
        )

    def reindex(self, *, reset: bool = True) -> dict[str, int]:
        get_knowledge_store.cache_clear()
        settings = get_rag_settings()
        knowledge_root = resolve_project_path(settings.knowledge_path)
        documents = load_knowledge_dir(knowledge_root)
        store = get_knowledge_store()
        if reset:
            store.reset()
        chunks = store.ingest_documents(documents)
        return {"documents": len(documents), "chunks": chunks, "total": store.count()}

    def stats(self) -> dict[str, int]:
        return {"total_chunks": get_knowledge_store().count()}
