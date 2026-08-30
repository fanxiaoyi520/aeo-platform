"""Chunking edge cases for RAG pipeline."""

from aeo_rag.chunking import recursive_split


def test_recursive_split_empty_text() -> None:
    assert recursive_split("   ") == []


def test_recursive_split_short_text() -> None:
    assert recursive_split("hello") == ["hello"]


def test_recursive_split_paragraph_separator() -> None:
    text = "Paragraph one.\n\nParagraph two is longer and should split."
    chunks = recursive_split(text, chunk_size=20, chunk_overlap=4)
    assert len(chunks) >= 2
    assert all(chunk.strip() for chunk in chunks)


def test_recursive_split_character_fallback() -> None:
    text = "x" * 30
    chunks = recursive_split(text, chunk_size=10, chunk_overlap=2, separators=[""])
    assert len(chunks) >= 2
    assert all(len(chunk) <= 10 for chunk in chunks)
