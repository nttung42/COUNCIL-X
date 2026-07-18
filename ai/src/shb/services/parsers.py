"""Extract text and page images from uploaded documents.

This module implements a **hybrid** strategy required by the property-intake
pipeline (PR1):

* **Text-based PDF pages** -> text is extracted directly with PyMuPDF.
* **Scanned / image-only PDF pages** -> rasterized to PNG so a downstream
  OCR / vision LLM step can read them.
* **DOCX / CSV / XLSX** -> text-only via LangChain community loaders.

A single PDF may mix text and scanned pages; each page is classified
independently and only scanned pages are rendered (to save memory/tokens).

Design notes
------------
* Functions are **pure** (no dependency on global settings) so they are easy to
  unit-test; thresholds are passed in with sensible module-level defaults that
  mirror :class:`shb.core.config.Settings`. Callers (plugins) wire settings in.
* PDF parsing uses **PyMuPDF** exclusively — it is self-contained (no Poppler
  system binary needed) and gives us text extraction *and* rasterization from a
  single in-memory open, avoiding temp files for PDFs.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

import fitz  # PyMuPDF

# NOTE: LangChain community loaders (used only for DOCX/CSV/XLSX) are imported
# lazily inside ``_parse_with_loader`` so the PDF path — the core of the intake
# pipeline — does not require ``langchain_community`` to be installed.

# --------------------------------------------------------------------------- #
# Defaults (mirror shb.core.config.Settings so behaviour is consistent)
# --------------------------------------------------------------------------- #
DEFAULT_SCAN_CHAR_THRESHOLD = 50
"""Chars of extractable text per page below which a PDF page is 'scanned'."""

DEFAULT_SCAN_DOC_FRACTION = 0.5
"""Fraction of scanned pages at/above which the whole PDF is 'scanned'."""

DEFAULT_RENDER_DPI = 200
"""DPI used when rasterizing scanned pages to PNG."""

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class FileType(StrEnum):
    """Supported document types for parsing."""

    PDF = "pdf"
    DOCX = "docx"
    CSV = "csv"
    XLSX = "xlsx"


SUPPORTED_MIME_TYPES: dict[str, FileType] = {
    "application/pdf": FileType.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileType.DOCX,
    "text/csv": FileType.CSV,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": FileType.XLSX,
}

SUPPORTED_EXTENSIONS: dict[str, FileType] = {
    ".pdf": FileType.PDF,
    ".docx": FileType.DOCX,
    ".csv": FileType.CSV,
    ".xlsx": FileType.XLSX,
}


class UnsupportedFileTypeError(ValueError):
    """Raised when a file's type cannot be mapped to a supported loader."""


class DocumentParseError(RuntimeError):
    """Raised when a supported file cannot be parsed (corrupt / unreadable)."""


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #
@dataclass
class PageContent:
    """A single page of a parsed document."""

    page_number: int  # 1-indexed
    text: str
    is_scanned: bool
    image_png: bytes | None = None  # populated only for scanned pages when rendered

    @property
    def char_count(self) -> int:
        """Return the count of non-whitespace-trimmed characters."""
        return len(self.text.strip())


@dataclass
class ParsedDocument:
    """Result of parsing an uploaded document.

    ``text`` holds the concatenated text of all text-bearing pages (kept as the
    first field for backward compatibility with the previous API). ``pages``
    exposes per-page detail used by the hybrid OCR routing.
    """

    text: str
    file_type: FileType | None = None
    pages: list[PageContent] = field(default_factory=list)
    page_count: int = 0
    is_scanned: bool = False  # document-level verdict

    @property
    def has_text(self) -> bool:
        """Return True when any text was extracted from the document."""
        return bool(self.text.strip())

    @property
    def scanned_pages(self) -> list[PageContent]:
        """Return the pages classified as scanned (image-only)."""
        return [p for p in self.pages if p.is_scanned]

    @property
    def rendered_pages(self) -> list[PageContent]:
        """Return the pages that have a rendered PNG image."""
        return [p for p in self.pages if p.image_png is not None]


@dataclass
class RenderedPage:
    """A rasterized PDF page."""

    page_number: int  # 1-indexed
    image_png: bytes
    width: int
    height: int


# --------------------------------------------------------------------------- #
# Type detection
# --------------------------------------------------------------------------- #
def detect_file_type(filename: str, content_type: str | None = None) -> FileType:
    """Detect a supported :class:`FileType` from filename extension or MIME type.

    Extension wins over MIME type (uploaders frequently send generic
    ``application/octet-stream``). Raises :class:`UnsupportedFileTypeError`
    when neither can be mapped.
    """
    ext = Path(filename).suffix.lower()
    if ext in SUPPORTED_EXTENSIONS:
        return SUPPORTED_EXTENSIONS[ext]
    if content_type and content_type.split(";")[0].strip() in SUPPORTED_MIME_TYPES:
        return SUPPORTED_MIME_TYPES[content_type.split(";")[0].strip()]
    raise UnsupportedFileTypeError(
        f"Cannot parse '{filename}': unsupported type. "
        f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
    )


# --------------------------------------------------------------------------- #
# PDF handling (PyMuPDF)
# --------------------------------------------------------------------------- #
def _open_pdf(data: bytes) -> fitz.Document:
    if not data:
        raise DocumentParseError("Cannot parse an empty PDF byte stream.")
    try:
        return fitz.open(stream=data, filetype="pdf")
    except Exception as exc:  # pragma: no cover - defensive
        raise DocumentParseError(f"Failed to open PDF: {exc}") from exc


def _page_is_scanned(text: str, scan_char_threshold: int) -> bool:
    """Return True when a page yields little/no extractable text (image-only)."""
    return len(text.strip()) < scan_char_threshold


def parse_pdf(
    data: bytes,
    *,
    render_scanned: bool = True,
    scan_char_threshold: int = DEFAULT_SCAN_CHAR_THRESHOLD,
    scan_doc_fraction: float = DEFAULT_SCAN_DOC_FRACTION,
    dpi: int = DEFAULT_RENDER_DPI,
) -> ParsedDocument:
    """Parse a PDF, classifying each page as text or scanned.

    Args:
        data: Raw PDF bytes.
        render_scanned: When True, rasterize scanned pages to PNG (``image_png``).
        scan_char_threshold: Per-page text length below which a page is scanned.
        scan_doc_fraction: Fraction of scanned pages that flips the whole document
            to ``is_scanned=True``.
        dpi: Rasterization DPI for scanned pages.

    Returns:
        A :class:`ParsedDocument` with populated ``pages``.
    """
    pages: list[PageContent] = []
    with _open_pdf(data) as doc:
        for index in range(doc.page_count):
            page = doc.load_page(index)
            try:
                text = page.get_text("text")
            except Exception as exc:  # pragma: no cover - defensive
                raise DocumentParseError(f"Failed to read PDF page {index + 1}: {exc}") from exc

            scanned = _page_is_scanned(text, scan_char_threshold)
            image_png: bytes | None = None
            if scanned and render_scanned:
                image_png = _render_page_png(page, dpi=dpi)

            pages.append(
                PageContent(
                    page_number=index + 1,
                    text=text.strip(),
                    is_scanned=scanned,
                    image_png=image_png,
                )
            )

    full_text = "\n\n".join(p.text for p in pages if p.text)
    is_scanned = _document_is_scanned(pages, scan_doc_fraction)
    return ParsedDocument(
        text=full_text,
        file_type=FileType.PDF,
        pages=pages,
        page_count=len(pages),
        is_scanned=is_scanned,
    )


def _document_is_scanned(pages: list[PageContent], scan_doc_fraction: float) -> bool:
    if not pages:
        return False
    scanned = sum(1 for p in pages if p.is_scanned)
    return (scanned / len(pages)) >= scan_doc_fraction


def is_text_pdf(
    data: bytes,
    *,
    scan_char_threshold: int = DEFAULT_SCAN_CHAR_THRESHOLD,
    scan_doc_fraction: float = DEFAULT_SCAN_DOC_FRACTION,
) -> bool:
    """Return True when a PDF is predominantly text-based (not a scan).

    Lightweight helper for routing: it never rasterizes pages.
    """
    with _open_pdf(data) as doc:
        pages = [
            PageContent(
                page_number=i + 1,
                text=doc.load_page(i).get_text("text").strip(),
                is_scanned=False,  # placeholder; recomputed below
            )
            for i in range(doc.page_count)
        ]
    for p in pages:
        p.is_scanned = _page_is_scanned(p.text, scan_char_threshold)
    return not _document_is_scanned(pages, scan_doc_fraction)


def _render_page_png(page: fitz.Page, *, dpi: int) -> bytes:
    try:
        pix = page.get_pixmap(dpi=dpi)
        return pix.tobytes("png")
    except Exception as exc:  # pragma: no cover - defensive
        raise DocumentParseError(
            f"Failed to render PDF page {page.number + 1} at {dpi} DPI: {exc}"
        ) from exc


def render_pdf_pages(
    data: bytes,
    *,
    pages: list[int] | None = None,
    dpi: int = DEFAULT_RENDER_DPI,
) -> list[RenderedPage]:
    """Rasterize selected PDF pages to PNG.

    Args:
        data: Raw PDF bytes.
        pages: 1-indexed page numbers to render. ``None`` renders all pages.
        dpi: Rasterization DPI.

    Returns:
        Rendered pages in ascending page order.

    Raises:
        ValueError: If a requested page number is out of range.
    """
    rendered: list[RenderedPage] = []
    with _open_pdf(data) as doc:
        total = doc.page_count
        targets = sorted(set(pages)) if pages is not None else list(range(1, total + 1))
        for page_no in targets:
            if page_no < 1 or page_no > total:
                raise ValueError(f"Page {page_no} out of range (1..{total}).")
            page = doc.load_page(page_no - 1)
            pix = page.get_pixmap(dpi=dpi)
            rendered.append(
                RenderedPage(
                    page_number=page_no,
                    image_png=pix.tobytes("png"),
                    width=pix.width,
                    height=pix.height,
                )
            )
    return rendered


# --------------------------------------------------------------------------- #
# Office / tabular formats (text-only via LangChain loaders)
# --------------------------------------------------------------------------- #
def _parse_with_loader(data: bytes, file_type: FileType) -> str:
    """Extract text from DOCX/CSV/XLSX using LangChain community loaders."""
    try:
        from langchain_community.document_loaders import (
            CSVLoader,
            Docx2txtLoader,
            UnstructuredExcelLoader,
        )
    except ImportError as exc:
        raise DocumentParseError(
            f"Parsing {file_type} requires 'langchain_community' (and its loader "
            "dependencies). Install it to enable DOCX/CSV/XLSX support."
        ) from exc

    with tempfile.NamedTemporaryFile(delete=True, suffix=f".{file_type}") as tmp:
        tmp.write(data)
        tmp.flush()

        if file_type == FileType.DOCX:
            loader = Docx2txtLoader(tmp.name)
        elif file_type == FileType.CSV:
            loader = CSVLoader(tmp.name, encoding="utf-8-sig")
        elif file_type == FileType.XLSX:
            loader = UnstructuredExcelLoader(tmp.name)
        else:  # pragma: no cover - guarded by callers
            raise UnsupportedFileTypeError(str(file_type))

        try:
            docs = loader.load()
        except Exception as exc:
            raise DocumentParseError(f"Failed to parse {file_type} document: {exc}") from exc

    return "\n\n".join(
        doc.page_content.strip() for doc in docs if doc.page_content and doc.page_content.strip()
    )


# --------------------------------------------------------------------------- #
# Public dispatch
# --------------------------------------------------------------------------- #
def parse_bytes(
    data: bytes,
    file_type: FileType,
    *,
    render_scanned: bool = True,
    scan_char_threshold: int = DEFAULT_SCAN_CHAR_THRESHOLD,
    scan_doc_fraction: float = DEFAULT_SCAN_DOC_FRACTION,
    dpi: int = DEFAULT_RENDER_DPI,
) -> ParsedDocument:
    """Parse raw bytes into a :class:`ParsedDocument`.

    PDFs are routed through the hybrid text/scan parser; other supported types
    are text-only and returned as a single synthetic page.
    """
    if file_type == FileType.PDF:
        return parse_pdf(
            data,
            render_scanned=render_scanned,
            scan_char_threshold=scan_char_threshold,
            scan_doc_fraction=scan_doc_fraction,
            dpi=dpi,
        )

    text = _parse_with_loader(data, file_type)
    return ParsedDocument(
        text=text,
        file_type=file_type,
        pages=[PageContent(page_number=1, text=text, is_scanned=False)],
        page_count=1,
        is_scanned=False,
    )


def parse_upload(
    data: bytes,
    filename: str,
    content_type: str | None = None,
    **kwargs,
) -> ParsedDocument:
    """Detect the file type from metadata, then parse the raw bytes.

    Extra keyword arguments are forwarded to :func:`parse_bytes`.
    """
    file_type = detect_file_type(filename, content_type)
    return parse_bytes(data, file_type, **kwargs)
