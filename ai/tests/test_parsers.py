"""Tests for the hybrid document parser (PR1).

PDFs are synthesized in-memory with PyMuPDF so the suite needs no fixture files:
* a *text* PDF (extractable text),
* a *scanned* PDF (text rasterized into an image -> no extractable text),
* a *mixed* PDF (one text page + one scanned page).
"""

from __future__ import annotations

import fitz  # PyMuPDF
import pytest

from shb.services.parsers import (
    PNG_MAGIC,
    DocumentParseError,
    FileType,
    ParsedDocument,
    UnsupportedFileTypeError,
    detect_file_type,
    is_text_pdf,
    parse_bytes,
    parse_upload,
    render_pdf_pages,
)

LONG_TEXT = (
    "GIAY CHUNG NHAN QUYEN SU DUNG DAT - So phat hanh CS 01234567 - "
    "Dia chi Hem 45 Nguyen Van A, Phuong B, Quan C - Dien tich 62 m2"
)


# --------------------------------------------------------------------------- #
# PDF builders
# --------------------------------------------------------------------------- #
def _text_pdf(text: str = LONG_TEXT) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def _image_only_pdf(text: str = "SCANNED IMAGE CONTENT WITHOUT SELECTABLE TEXT") -> bytes:
    """Render text to a pixmap, then embed it as an image -> no extractable text."""
    src = fitz.open()
    sp = src.new_page()
    sp.insert_text((72, 72), text)
    pix = sp.get_pixmap(dpi=100)
    src.close()

    out = fitz.open()
    op = out.new_page(width=pix.width, height=pix.height)
    op.insert_image(op.rect, pixmap=pix)
    data = out.tobytes()
    out.close()
    return data


def _mixed_pdf() -> bytes:
    """Build a PDF whose page 1 is text and page 2 is image-only (scanned)."""
    tmp = fitz.open()
    tp = tmp.new_page()
    tp.insert_text((72, 72), "SCAN ONLY PAGE")
    pix = tp.get_pixmap(dpi=100)
    tmp.close()

    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_text((72, 72), LONG_TEXT)
    p2 = doc.new_page(width=pix.width, height=pix.height)
    p2.insert_image(p2.rect, pixmap=pix)
    data = doc.tobytes()
    doc.close()
    return data


# --------------------------------------------------------------------------- #
# detect_file_type
# --------------------------------------------------------------------------- #
def test_detect_file_type_by_extension():
    """Extension maps to the correct FileType (case-insensitive)."""
    assert detect_file_type("so-hong.pdf") == FileType.PDF
    assert detect_file_type("tokhai.DOCX") == FileType.DOCX
    assert detect_file_type("data.csv") == FileType.CSV
    assert detect_file_type("sheet.xlsx") == FileType.XLSX


def test_detect_file_type_by_mime_when_extension_missing():
    """MIME type resolves the FileType when there is no extension."""
    assert detect_file_type("noext", "application/pdf") == FileType.PDF
    assert detect_file_type("noext", "text/csv; charset=utf-8") == FileType.CSV


def test_detect_file_type_extension_wins_over_mime():
    """A known extension takes precedence over a generic MIME type."""
    assert detect_file_type("real.pdf", "application/octet-stream") == FileType.PDF


def test_detect_file_type_unsupported_raises():
    """An unsupported type raises UnsupportedFileTypeError."""
    with pytest.raises(UnsupportedFileTypeError):
        detect_file_type("photo.tiff", "image/tiff")


# --------------------------------------------------------------------------- #
# Text PDF
# --------------------------------------------------------------------------- #
def test_parse_text_pdf():
    """A text PDF is parsed with extractable text and no rendered image."""
    doc = parse_bytes(_text_pdf(), FileType.PDF)
    assert isinstance(doc, ParsedDocument)
    assert doc.file_type == FileType.PDF
    assert doc.page_count == 1
    assert doc.is_scanned is False
    assert doc.has_text
    assert "CS 01234567" in doc.text
    page = doc.pages[0]
    assert page.is_scanned is False
    assert page.image_png is None
    assert page.char_count > 50


def test_is_text_pdf_true_for_text():
    """is_text_pdf returns True for a text-based PDF."""
    assert is_text_pdf(_text_pdf()) is True


# --------------------------------------------------------------------------- #
# Scanned PDF
# --------------------------------------------------------------------------- #
def test_parse_scanned_pdf_renders_image():
    """A scanned PDF is flagged scanned and its page rendered to PNG."""
    doc = parse_bytes(_image_only_pdf(), FileType.PDF)
    assert doc.is_scanned is True
    assert doc.has_text is False
    assert len(doc.scanned_pages) == 1
    assert len(doc.rendered_pages) == 1
    page = doc.pages[0]
    assert page.is_scanned is True
    assert page.image_png is not None
    assert page.image_png.startswith(PNG_MAGIC)


def test_parse_scanned_pdf_without_rendering():
    """render_scanned=False detects a scan but skips rasterization."""
    doc = parse_bytes(_image_only_pdf(), FileType.PDF, render_scanned=False)
    assert doc.is_scanned is True
    assert doc.pages[0].is_scanned is True
    assert doc.pages[0].image_png is None


def test_is_text_pdf_false_for_scan():
    """is_text_pdf returns False for a scanned PDF."""
    assert is_text_pdf(_image_only_pdf()) is False


# --------------------------------------------------------------------------- #
# Mixed PDF
# --------------------------------------------------------------------------- #
def test_parse_mixed_pdf():
    """A mixed PDF classifies each page and renders only the scanned one."""
    doc = parse_bytes(_mixed_pdf(), FileType.PDF)
    assert doc.page_count == 2
    assert doc.pages[0].is_scanned is False
    assert doc.pages[1].is_scanned is True
    assert len(doc.scanned_pages) == 1
    assert len(doc.rendered_pages) == 1
    assert doc.is_scanned is True  # 1/2 == default fraction 0.5
    assert "CS 01234567" in doc.text


def test_parse_mixed_pdf_high_fraction_not_scanned():
    """A higher scan fraction keeps a half-scanned document as text."""
    doc = parse_bytes(_mixed_pdf(), FileType.PDF, scan_doc_fraction=0.75)
    assert doc.is_scanned is False


# --------------------------------------------------------------------------- #
# render_pdf_pages
# --------------------------------------------------------------------------- #
def test_render_pdf_pages_all():
    """Rendering all pages yields one PNG per page in order."""
    rendered = render_pdf_pages(_mixed_pdf())
    assert len(rendered) == 2
    assert [r.page_number for r in rendered] == [1, 2]
    for r in rendered:
        assert r.image_png.startswith(PNG_MAGIC)
        assert r.width > 0 and r.height > 0


def test_render_pdf_pages_subset():
    """Rendering a subset returns only the requested pages."""
    rendered = render_pdf_pages(_mixed_pdf(), pages=[2])
    assert len(rendered) == 1
    assert rendered[0].page_number == 2


def test_render_pdf_pages_out_of_range():
    """An out-of-range page number raises ValueError."""
    with pytest.raises(ValueError):
        render_pdf_pages(_text_pdf(), pages=[5])


def test_render_pdf_pages_dpi_affects_size():
    """Higher DPI produces a larger raster image."""
    low = render_pdf_pages(_text_pdf(), dpi=72)[0]
    high = render_pdf_pages(_text_pdf(), dpi=200)[0]
    assert high.width > low.width and high.height > low.height


# --------------------------------------------------------------------------- #
# Error handling & dispatch
# --------------------------------------------------------------------------- #
def test_parse_empty_pdf_raises():
    """Empty PDF bytes raise DocumentParseError."""
    with pytest.raises(DocumentParseError):
        parse_bytes(b"", FileType.PDF)


def test_parse_corrupt_pdf_raises():
    """Corrupt PDF bytes raise DocumentParseError."""
    with pytest.raises(DocumentParseError):
        parse_bytes(b"%PDF-1.4 totally broken", FileType.PDF)


def test_parse_corrupt_docx_raises():
    """Unparseable DOCX bytes raise DocumentParseError."""
    with pytest.raises(DocumentParseError):
        parse_bytes(b"this is not a docx", FileType.DOCX)


def test_parse_upload_dispatches_by_name():
    """parse_upload detects the type from the filename and parses."""
    doc = parse_upload(_text_pdf(), "so-hong.pdf")
    assert doc.file_type == FileType.PDF
    assert doc.has_text


# --------------------------------------------------------------------------- #
# DOCX happy path (only when loaders are available)
# --------------------------------------------------------------------------- #
def test_parse_docx_text():
    """A real DOCX is parsed to text when loader backends are installed."""
    pytest.importorskip("langchain_community")
    docx = pytest.importorskip("docx")  # python-docx
    import io

    document = docx.Document()
    document.add_paragraph("Bien ban ban giao tai san")
    document.add_paragraph("Dien tich san 98 m2")
    buffer = io.BytesIO()
    document.save(buffer)

    result = parse_bytes(buffer.getvalue(), FileType.DOCX)
    assert result.file_type == FileType.DOCX
    assert result.page_count == 1
    assert result.is_scanned is False
    assert "Bien ban ban giao" in result.text
