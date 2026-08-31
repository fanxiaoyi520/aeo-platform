import re
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

from aeo_rag.config import get_rag_settings, resolve_project_path
from aeo_rag.loaders import SUPPORTED_EXTENSIONS, load_knowledge_dir
from aeo_rag.store import KnowledgeStore, SearchResult

UPLOAD_MAX_BYTES = 10 * 1024 * 1024
UPLOAD_CATEGORIES = frozenset({"products", "amazon", "tiktok", "sop", "examples", "uploads"})


class KnowledgeDocumentRecord(TypedDict):
    source_file: str
    size_bytes: int
    extension: str
    updated_at: str


class KnowledgeUploadResult(TypedDict):
    source_file: str
    size_bytes: int
    category: str
    reindex: dict[str, int]


def _use_hash_embeddings() -> bool:
    import os

    explicit = os.environ.get("RAG_USE_HASH_EMBEDDINGS", "").strip().lower()
    if explicit in ("true", "1", "yes"):
        return True
    if explicit in ("false", "0", "no"):
        return False
    # Dev fallback: placeholder embed key cannot call a real embedding API.
    key = os.environ.get("EMBED_API_KEY", "").strip()
    return not key or key == "your-api-key-here"


@lru_cache
def get_knowledge_store() -> KnowledgeStore:
    return KnowledgeStore(use_hash_embeddings=_use_hash_embeddings())


class KnowledgeService:
    def search(
        self,
        query: str,
        *,
        platform: str | None = None,
        category: str | None = None,
        top_k: int | None = None,
    ) -> list[SearchResult]:
        # Hash embeddings are deterministic, not semantic — scores stay near zero.
        score_threshold = 0.0 if _use_hash_embeddings() else None
        return get_knowledge_store().search(
            query,
            platform=platform,
            category=category,
            top_k=top_k,
            score_threshold=score_threshold,
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

    def knowledge_root(self) -> Path:
        settings = get_rag_settings()
        return resolve_project_path(settings.knowledge_path)

    def list_documents(self) -> list[KnowledgeDocumentRecord]:
        knowledge_root = self.knowledge_root()
        items: list[KnowledgeDocumentRecord] = []
        if not knowledge_root.exists():
            return items

        for path in sorted(knowledge_root.rglob("*")):
            if not path.is_file() or path.name.startswith("."):
                continue
            stat = path.stat()
            items.append(
                {
                    "source_file": str(path.relative_to(knowledge_root)).replace("\\", "/"),
                    "size_bytes": stat.st_size,
                    "extension": path.suffix.lower(),
                    "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                }
            )
        return items

    def upload_document(
        self,
        filename: str,
        content: bytes,
        *,
        category: str = "uploads",
    ) -> KnowledgeUploadResult:
        if category not in UPLOAD_CATEGORIES:
            raise ValueError(f"invalid category: {category}")
        if len(content) > UPLOAD_MAX_BYTES:
            raise ValueError("file exceeds 10MB limit")
        if not content:
            raise ValueError("empty file")

        safe_name = _sanitize_filename(filename)
        suffix = Path(safe_name).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise ValueError(f"unsupported file type; allowed: {allowed}")

        knowledge_root = self.knowledge_root()
        target_dir = knowledge_root / category
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = _resolve_unique_path(target_dir / safe_name)
        target_path.write_bytes(content)

        reindex_result = self.reindex(reset=True)
        relative = str(target_path.relative_to(knowledge_root)).replace("\\", "/")
        return {
            "source_file": relative,
            "size_bytes": len(content),
            "category": category,
            "reindex": reindex_result,
        }


def _sanitize_filename(filename: str) -> str:
    base = Path(filename).name.strip()
    if not base or base in {".", ".."}:
        raise ValueError("invalid filename")
    safe = re.sub(r"[^\w.\- ]+", "_", base, flags=re.UNICODE).strip(" .")
    if not safe or safe.startswith("."):
        raise ValueError("invalid filename")
    return safe


def _resolve_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 1
    while True:
        candidate = path.with_name(f"{stem}-{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
