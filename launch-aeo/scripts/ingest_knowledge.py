"""Knowledge base ingestion CLI."""

from __future__ import annotations

import argparse
import sys

import structlog
from aeo_rag.config import get_rag_settings, resolve_project_path
from aeo_rag.loaders import load_knowledge_dir
from aeo_rag.store import KnowledgeStore

logger = structlog.get_logger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest knowledge documents into Chroma")
    parser.add_argument("--reset", action="store_true", help="Clear collection before ingest")
    parser.add_argument(
        "--hash-embeddings",
        action="store_true",
        help="Use local hash embeddings (no LLM API, for dev/test)",
    )
    args = parser.parse_args()

    settings = get_rag_settings()
    knowledge_root = resolve_project_path(settings.knowledge_path)
    logger.info("loading knowledge", path=str(knowledge_root))

    documents = load_knowledge_dir(knowledge_root)
    if not documents:
        logger.error("no documents found")
        return 1

    store = KnowledgeStore(use_hash_embeddings=args.hash_embeddings)
    if args.reset:
        store.reset()
        logger.info("collection reset")

    count = store.ingest_documents(documents)
    logger.info("ingest complete", documents=len(documents), chunks=count, total=store.count())
    return 0


if __name__ == "__main__":
    sys.exit(main())
