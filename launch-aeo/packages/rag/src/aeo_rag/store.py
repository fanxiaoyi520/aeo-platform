from contextlib import suppress
from datetime import UTC, datetime
from typing import Any, cast

import chromadb
import structlog
from chromadb.api.models.Collection import Collection
from chromadb.api.types import Documents, EmbeddingFunction, Metadata
from pydantic import BaseModel

from aeo_rag.chunking import recursive_split
from aeo_rag.config import RagSettings, get_rag_settings, resolve_project_path
from aeo_rag.embeddings import HashEmbeddingFunction, LlmEmbeddingFunction
from aeo_rag.loaders import KnowledgeDocument

logger = structlog.get_logger(__name__)


class SearchResult(BaseModel):
    doc_id: str
    content: str
    score: float
    category: str
    platform: str
    source_file: str
    chunk_index: int


class KnowledgeStore:
    def __init__(
        self,
        settings: RagSettings | None = None,
        *,
        use_hash_embeddings: bool = False,
    ) -> None:
        self._settings = settings or get_rag_settings()
        chroma_dir = resolve_project_path(self._settings.chroma_path)
        chroma_dir.mkdir(parents=True, exist_ok=True)

        embed_fn: EmbeddingFunction[Documents] = (
            HashEmbeddingFunction() if use_hash_embeddings else LlmEmbeddingFunction()
        )
        self._embed_fn = embed_fn
        self._client = chromadb.PersistentClient(path=str(chroma_dir))
        self._collection: Collection = self._client.get_or_create_collection(
            name=self._settings.chroma_collection,
            embedding_function=cast(Any, embed_fn),
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def collection(self) -> Collection:
        return self._collection

    def reset(self) -> None:
        name = self._settings.chroma_collection
        with suppress(Exception):
            self._client.delete_collection(name)
        embed_fn = self._embed_fn
        self._collection = self._client.get_or_create_collection(
            name=name,
            embedding_function=cast(Any, embed_fn),
            metadata={"hnsw:space": "cosine"},
        )

    def ingest_documents(self, documents: list[KnowledgeDocument]) -> int:
        ids: list[str] = []
        texts: list[str] = []
        metadatas: list[Metadata] = []

        for doc in documents:
            chunks = recursive_split(
                doc.content,
                chunk_size=self._settings.rag_chunk_size,
                chunk_overlap=self._settings.rag_chunk_overlap,
            )
            for idx, chunk in enumerate(chunks):
                chunk_id = f"{doc.doc_id}:{idx}"
                ids.append(chunk_id)
                texts.append(chunk)
                metadatas.append(
                    {
                        "doc_id": doc.doc_id,
                        "category": doc.category,
                        "platform": doc.platform,
                        "source_file": doc.source_file,
                        "version": doc.version,
                        "chunk_index": idx,
                        "updated_at": datetime.now(UTC).isoformat(),
                    }
                )

        if not ids:
            return 0

        # Upsert for idempotent re-index
        self._collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
        logger.info("ingested chunks", count=len(ids))
        return len(ids)

    def search(
        self,
        query: str,
        *,
        platform: str | None = None,
        category: str | None = None,
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> list[SearchResult]:
        k = top_k or self._settings.rag_top_k
        threshold = (
            score_threshold if score_threshold is not None else self._settings.rag_score_threshold
        )

        where: dict[str, Any] | None = None
        filters: list[dict[str, Any]] = []
        if platform:
            filters.append({"platform": platform})
        if category:
            filters.append({"category": category})
        if len(filters) == 1:
            where = filters[0]
        elif len(filters) > 1:
            where = {"$and": filters}

        result = self._collection.query(
            query_texts=[query],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        items: list[SearchResult] = []
        raw_docs = result.get("documents")
        raw_metas = result.get("metadatas")
        raw_distances = result.get("distances")
        if not raw_docs or not raw_metas or not raw_distances:
            return items
        docs = raw_docs[0]
        metas = raw_metas[0]
        distances = raw_distances[0]

        for doc_text, meta, dist in zip(docs, metas, distances, strict=True):
            if meta is None:
                continue
            # cosine distance -> similarity
            score = 1.0 - float(dist)
            if score < threshold:
                continue
            raw_idx = meta.get("chunk_index", 0)
            chunk_index = raw_idx if isinstance(raw_idx, int) else 0
            items.append(
                SearchResult(
                    doc_id=str(meta.get("doc_id", "")),
                    content=doc_text or "",
                    score=round(score, 4),
                    category=str(meta.get("category", "")),
                    platform=str(meta.get("platform", "")),
                    source_file=str(meta.get("source_file", "")),
                    chunk_index=chunk_index,
                )
            )
        return items

    def count(self) -> int:
        return self._collection.count()
