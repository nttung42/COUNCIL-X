"""Locate extracted values on the source PDF page → normalized bounding boxes.

Deterministic post-step for feature "vùng trích xuất": for every output field
that has provenance (``source_file_id`` + ``source_page`` + snippet/value) but no
``bbox`` yet, find the snippet's exact position in the PDF text layer with
PyMuPDF ``page.search_for`` and emit a :class:`~.schema.BBox` normalized to
``0..1`` (origin top-left) — the same convention as ``field_provenance.bbox_*``
and the frontend document-viewer overlay.

No LLM involved — the coordinates come from the PDF itself, so the highlight the
reviewer sees is exactly where the value was read from (audit trail). Scanned
(image-only) pages have no text layer and are skipped. Best-effort: any failure
leaves ``bbox = None`` and never breaks the pipeline.
"""

from __future__ import annotations

import logging
import re

import fitz  # PyMuPDF

from shb.ai.plugins.property_intake.schema import BBox, FormField
from shb.ai.plugins.property_intake.state import IngestedDoc

logger = logging.getLogger(__name__)

# A needle at least this long is considered unique enough to union multi-line
# hits; shorter needles (e.g. "82") take only their first occurrence.
_UNIQUE_NEEDLE_LEN = 20
_MAX_NEEDLE_LEN = 120  # search_for gets slow/fragile beyond this


def _normalize_needle(text: str) -> str:
    """Collapse whitespace/newlines so the needle matches the page text layout."""
    return re.sub(r"\s+", " ", text).strip()[:_MAX_NEEDLE_LEN]


def _candidates(field: FormField) -> list[str]:
    """Ordered search needles: full snippet → verbatim value → snippet head."""
    out: list[str] = []
    if field.source_snippet:
        out.append(_normalize_needle(field.source_snippet))
    if field.value:
        out.append(_normalize_needle(field.value))
    if field.source_snippet and len(field.source_snippet) > 40:
        out.append(_normalize_needle(field.source_snippet)[:40])
    # dedupe, keep order, drop empties/too-short
    seen: set[str] = set()
    return [c for c in out if len(c) >= 2 and not (c in seen or seen.add(c))]


def _search_page(page: fitz.Page, needle: str) -> fitz.Rect | None:
    """Return the bounding rect for ``needle`` on ``page`` (None if not found)."""
    try:
        rects = page.search_for(needle)
        if not rects and " " in needle:
            # PDFs frequently encode spaces as NBSP internally; the pipeline
            # normalizes snippets to regular spaces, so retry the NBSP variant.
            rects = page.search_for(needle.replace(" ", "\N{NO-BREAK SPACE}"))
    except Exception:  # pragma: no cover - malformed needle
        return None
    if not rects:
        return None
    if len(needle) >= _UNIQUE_NEEDLE_LEN:
        # long needle → single logical occurrence, possibly wrapped on 2+ lines
        union = fitz.Rect(rects[0])
        for r in rects[1:]:
            union |= r
        return union
    return fitz.Rect(rects[0])  # short needle → first occurrence only


def _to_bbox(rect: fitz.Rect, page: fitz.Page) -> BBox | None:
    """Normalize a fitz rect to 0..1 page coordinates (top-left origin)."""
    pw, ph = page.rect.width, page.rect.height
    if pw <= 0 or ph <= 0:
        return None
    return BBox(
        x=max(0.0, round(rect.x0 / pw, 4)),
        y=max(0.0, round(rect.y0 / ph, 4)),
        width=min(1.0, round((rect.x1 - rect.x0) / pw, 4)),
        height=min(1.0, round((rect.y1 - rect.y0) / ph, 4)),
    )


def locate_in_pdf(pdf_bytes: bytes, page_number: int, field: FormField) -> BBox | None:
    """Locate one field's evidence on ``page_number`` (1-indexed) of a PDF."""
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            if not 1 <= page_number <= doc.page_count:
                return None
            page = doc[page_number - 1]
            for needle in _candidates(field):
                rect = _search_page(page, needle)
                if rect is not None:
                    return _to_bbox(rect, page)
    except Exception as exc:  # pragma: no cover - corrupt bytes etc.
        logger.debug("bbox locate failed: %s", exc)
    return None


async def locate_missing_bboxes(fields: list[FormField], docs: list[IngestedDoc], storage) -> int:
    """Fill ``bbox`` in-place for fields that have provenance but no box yet.

    Re-reads each involved PDF once through the storage service (bytes are not
    kept in the graph state). Scanned documents and non-PDFs are skipped.
    Returns the number of boxes located. Never raises.
    """
    if storage is None:
        return 0
    by_file: dict[str, IngestedDoc] = {d.file_id: d for d in docs}
    bytes_cache: dict[str, bytes | None] = {}
    located = 0

    for field in fields:
        if field.bbox is not None or not field.value or not field.source_file_id:
            continue
        doc = by_file.get(field.source_file_id)
        if doc is None or doc.parsed.is_scanned:
            continue
        fid = field.source_file_id
        if fid not in bytes_cache:
            try:
                rec = await storage.get_file(fid)
                bytes_cache[fid] = await storage.read_file(rec.stored_path) if rec else None
            except Exception as exc:  # pragma: no cover - storage hiccup
                logger.debug("bbox read failed for %s: %s", fid, exc)
                bytes_cache[fid] = None
        data = bytes_cache[fid]
        if not data:
            continue
        bbox = locate_in_pdf(data, field.source_page or 1, field)
        if bbox is not None:
            field.bbox = bbox
            located += 1
    return located
