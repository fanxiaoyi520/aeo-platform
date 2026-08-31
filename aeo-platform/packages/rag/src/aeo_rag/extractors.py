"""Extract plain text from binary document formats for RAG ingestion."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path


def extract_pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text.strip())
    return "\n\n".join(parts)


def extract_docx_text(data: bytes) -> str:
    from docx import Document

    document = Document(BytesIO(data))
    parts: list[str] = []
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def extract_text_from_bytes(data: bytes, suffix: str) -> str:
    normalized = suffix.lower()
    if normalized == ".pdf":
        return extract_pdf_text(data)
    if normalized == ".docx":
        return extract_docx_text(data)
    raise ValueError(f"unsupported binary format: {suffix}")


def extract_text_from_path(path: Path) -> str:
    return extract_text_from_bytes(path.read_bytes(), path.suffix)
