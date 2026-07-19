"""Tests for the bbox locator + FE wire-format aliases of property_intake.

A small PDF is generated in-memory with PyMuPDF so the locator runs offline and
deterministically: known text at known positions → assert the normalized bbox
lands on it.
"""

from __future__ import annotations

import fitz

from shb.ai.plugins.property_intake.locate import locate_in_pdf
from shb.ai.plugins.property_intake.schema import (
    BBox,
    DocType,
    DocumentInfo,
    FieldStatus,
    FormField,
)


def _pdf_with(lines: list[tuple[float, float, str]]) -> bytes:
    """Build a 1-page A4 PDF with ``(x, y, text)`` lines (points, top-left)."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    for x, y, text in lines:
        page.insert_text((x, y), text, fontsize=11)
    return doc.tobytes()


def _field(**over) -> FormField:
    base = dict(
        key="land_area_sqm",
        section="C",
        label="Diện tích đất",
        target_table="property_physical_info",
        target_field="land_area_sqm",
        value="199.30",
        status=FieldStatus.DA_XAC_THUC,
        confidence_pct=92,
        source_file_id="f1",
        source_page=1,
        source_snippet="Dien tich dat: 199.30 m2",
    )
    base.update(over)
    return FormField(**base)


def test_locate_finds_snippet_position():
    """The snippet's normalized bbox lands where the text was drawn."""
    pdf = _pdf_with([(72, 400, "Dien tich dat: 199.30 m2"), (72, 100, "Khac")])
    bbox = locate_in_pdf(pdf, 1, _field())
    assert bbox is not None
    # y ≈ 400/842 ≈ 0.47 (text baseline offset ±) — generous tolerance
    assert 0.4 < bbox.y < 0.52
    assert 0.08 < bbox.x < 0.16  # x ≈ 72/595 ≈ 0.12
    assert 0 < bbox.width < 0.5 and 0 < bbox.height < 0.05


def test_locate_falls_back_to_value():
    """Snippet not present verbatim → falls back to locating the value itself."""
    pdf = _pdf_with([(100, 200, "Tong dien tich 199.30 (m2)")])
    bbox = locate_in_pdf(pdf, 1, _field(source_snippet="khong khop gi ca 199.30"))
    assert bbox is not None
    assert 0.15 < bbox.x < 0.9


def test_locate_missing_returns_none():
    """Nothing matches → None (field keeps bbox null, pipeline unaffected)."""
    pdf = _pdf_with([(72, 100, "Van ban khong lien quan")])
    assert locate_in_pdf(pdf, 1, _field(value="9999", source_snippet="9999")) is None
    assert locate_in_pdf(pdf, 99, _field()) is None  # page out of range


def test_wire_aliases_serialized():
    """FE aliases appear in the JSON dump alongside the canonical keys."""
    f = _field(bbox=BBox(x=0.1, y=0.2, width=0.3, height=0.04))
    dumped = f.model_dump()
    assert dumped["confidence"] == 0.92  # 0..1 fraction
    assert dumped["source_doc"] == "f1"  # alias of source_file_id
    assert dumped["confidence_pct"] == 92  # canonical keys still present
    assert dumped["bbox"]["w"] == 0.3 and dumped["bbox"]["h"] == 0.04
    assert dumped["bbox"]["width"] == 0.3  # canonical bbox keys intact

    d = DocumentInfo(
        file_id="f1",
        file_name="so_do.pdf",
        detected_doc_type=DocType.SO_DO_SO_HONG,
        is_scan=False,
        page_count=2,
    ).model_dump()
    assert d["doc_type"] == "so_do_so_hong" and d["is_scanned"] is False
    assert d["detected_doc_type"] == "so_do_so_hong"
