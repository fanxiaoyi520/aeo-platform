import json
import uuid
from dataclasses import dataclass
from pathlib import Path

import structlog

from aeo_rag.extractors import extract_text_from_path

logger = structlog.get_logger(__name__)

SUPPORTED_EXTENSIONS = {".md", ".json", ".txt", ".pdf", ".docx"}


@dataclass
class KnowledgeDocument:
    doc_id: str
    content: str
    category: str
    platform: str
    source_file: str
    version: str = "1.0"


def _infer_metadata(path: Path, knowledge_root: Path) -> tuple[str, str]:
    rel = path.relative_to(knowledge_root)
    parts = rel.parts
    platform = "general"
    category = "sop"

    if len(parts) >= 1:
        top = parts[0].lower()
        if top in ("amazon", "tiktok"):
            platform = top
            category = "amazon_rules" if top == "amazon" else "tiktok_rules"
        elif top == "products":
            category = "product"
            platform = "general"
        elif top == "examples":
            category = "example"
        elif top == "sop":
            category = "sop"
        elif top == "uploads":
            category = "upload"

    return category, platform


def load_file(path: Path, knowledge_root: Path) -> KnowledgeDocument | None:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        logger.warning("skip unsupported file", path=str(path))
        return None

    category, platform = _infer_metadata(path, knowledge_root)

    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        content = json.dumps(data, ensure_ascii=False, indent=2)
    elif suffix in (".pdf", ".docx"):
        content = extract_text_from_path(path)
    else:
        content = path.read_text(encoding="utf-8")

    if not content.strip():
        return None

    return KnowledgeDocument(
        doc_id=str(uuid.uuid5(uuid.NAMESPACE_URL, str(path.resolve()))),
        content=content,
        category=category,
        platform=platform,
        source_file=str(path.relative_to(knowledge_root)),
    )


def load_knowledge_dir(knowledge_root: Path) -> list[KnowledgeDocument]:
    documents: list[KnowledgeDocument] = []
    if not knowledge_root.exists():
        logger.warning("knowledge directory missing", path=str(knowledge_root))
        return documents

    for path in sorted(knowledge_root.rglob("*")):
        if path.is_file() and not path.name.startswith("."):
            doc = load_file(path, knowledge_root)
            if doc:
                documents.append(doc)
    return documents
