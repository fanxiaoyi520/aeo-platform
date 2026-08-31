import gc
import os
import tempfile
from pathlib import Path

os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test")

from aeo_rag.chunking import recursive_split
from aeo_rag.loaders import load_knowledge_dir
from aeo_rag.store import KnowledgeStore


def test_recursive_split() -> None:
    text = "A" * 600
    chunks = recursive_split(text, chunk_size=200, chunk_overlap=20)
    assert len(chunks) >= 2
    assert all(len(c) <= 200 for c in chunks)


def test_load_and_search_knowledge(tmp_path: Path) -> None:
    knowledge = tmp_path / "knowledge"
    amazon = knowledge / "amazon"
    amazon.mkdir(parents=True)
    content = "# Amazon Rules\nTitle max 200 characters for OBD2 scanner listings."
    (amazon / "rules.md").write_text(content, encoding="utf-8")

    docs = load_knowledge_dir(knowledge)
    assert len(docs) == 1
    assert docs[0].platform == "amazon"

    chroma_dir = tempfile.mkdtemp()
    try:
        os.environ["CHROMA_PATH"] = chroma_dir
        from aeo_rag.config import get_rag_settings

        get_rag_settings.cache_clear()
        store = KnowledgeStore(use_hash_embeddings=True)
        store.reset()
        count = store.ingest_documents(docs)
        assert count > 0
        # Hash embeddings: query with exact ingested text for reliable match
        results = store.search(content, platform="amazon", score_threshold=0.0)
        assert len(results) >= 1
        del store
        gc.collect()
    finally:
        import shutil

        shutil.rmtree(chroma_dir, ignore_errors=True)
