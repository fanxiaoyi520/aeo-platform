from io import BytesIO
from pathlib import Path

import pytest
from aeo_rag.extractors import extract_docx_text, extract_pdf_text, extract_text_from_bytes
from aeo_rag.loaders import load_file, load_knowledge_dir
from docx import Document

MINIMAL_PDF_WITH_TEXT = (
    b"%PDF-1.1\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 200 200]/Parent 2 0 R/Contents 4 0 R"
    b"/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 44>>stream\n"
    b"BT /F1 12 Tf 50 150 Td (Hello PDF) Tj ET\n"
    b"endstream\n"
    b"endobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"xref\n0 6\n"
    b"0000000000 65535 f\n"
    b"0000000009 00000 n\n"
    b"0000000052 00000 n\n"
    b"0000000101 00000 n\n"
    b"0000000244 00000 n\n"
    b"0000000341 00000 n\n"
    b"trailer<</Size 6/Root 1 0 R>>\n"
    b"startxref\n409\n%%EOF"
)


def _make_docx_bytes(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_extract_docx_text() -> None:
    content = _make_docx_bytes("Acme Wireless Earbuds Pro product")
    text = extract_docx_text(content)
    assert "Acme Wireless Earbuds Pro" in text


def test_extract_pdf_text() -> None:
    text = extract_pdf_text(MINIMAL_PDF_WITH_TEXT)
    assert "Hello PDF" in text


def test_extract_text_from_bytes_docx() -> None:
    content = _make_docx_bytes("Wireless earbuds with ANC")
    text = extract_text_from_bytes(content, ".docx")
    assert "Wireless earbuds" in text


def test_extract_text_from_bytes_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="unsupported binary format"):
        extract_text_from_bytes(b"data", ".zip")


def test_load_docx_file_via_loader(tmp_path: Path) -> None:
    products = tmp_path / "products"
    products.mkdir(parents=True)
    docx_path = products / "sample-product.docx"
    docx_path.write_bytes(_make_docx_bytes("Acme sample product parameters"))

    doc = load_file(docx_path, tmp_path)
    assert doc is not None
    assert doc.category == "product"
    assert "Acme sample product" in doc.content


def test_load_knowledge_dir_includes_docx(tmp_path: Path) -> None:
    uploads = tmp_path / "uploads"
    uploads.mkdir(parents=True)
    (uploads / "notes.docx").write_bytes(_make_docx_bytes("Upload folder document"))

    docs = load_knowledge_dir(tmp_path)
    assert len(docs) == 1
    assert docs[0].category == "upload"
