"""Tests for the property_intake plugin (PR2 skeleton).

The LLM is replaced with a fake that returns a fixed ``SoHongExtraction`` so the
pipeline (ingest -> extract -> assemble) is exercised deterministically offline.
"""

from __future__ import annotations

from types import SimpleNamespace

import fitz  # PyMuPDF
import pytest

from shb.ai.plugins.property_intake.documents import CANONICAL_FIELDS, classify_by_keywords
from shb.ai.plugins.property_intake.graph import run_intake
from shb.ai.plugins.property_intake.nodes import extract as extract_mod
from shb.ai.plugins.property_intake.nodes import ingest as ingest_mod
from shb.ai.plugins.property_intake.nodes.assemble import assemble_node
from shb.ai.plugins.property_intake.nodes.extract import _is_grounded, extract_node
from shb.ai.plugins.property_intake.nodes.ingest import ingest_node
from shb.ai.plugins.property_intake.schema import (
    DocType,
    ExtractedField,
    FieldStatus,
    PropertyIntakeInput,
    SoHongExtraction,
)
from shb.ai.plugins.property_intake.state import IngestedDoc
from shb.ai.plugins.registry import AIServiceRegistry
from shb.services.parsers import FileType, PageContent, ParsedDocument


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #
class _FakeStructured:
    def __init__(self, result):
        self._result = result

    async def ainvoke(self, _messages):
        return self._result


class _FakeChat:
    def __init__(self, result):
        self._result = result

    def with_structured_output(self, _schema):
        return _FakeStructured(self._result)


class _FakeFile:
    def __init__(self, name, path, content_type):
        self.original_name = name
        self.stored_path = path
        self.content_type = content_type


class _FakeStorage:
    def __init__(self):
        self._files: dict = {}
        self._blobs: dict = {}

    def add(self, file_id, name, content_type, data):
        path = f"/mem/{file_id}"
        self._files[file_id] = _FakeFile(name, path, content_type)
        self._blobs[path] = data

    async def get_file(self, file_id):
        return self._files.get(file_id)

    async def read_file(self, path):
        return self._blobs[path]


def _sample_extraction() -> SoHongExtraction:
    return SoHongExtraction(
        owner_full_name=ExtractedField(
            value="Nguyễn Văn A",
            snippet="Người sử dụng đất: Ông Nguyễn Văn A",
            confidence=0.95,
        ),
        certificate_number=ExtractedField(
            value="CS 01234567", snippet="Số phát hành: CS 01234567", confidence=0.9
        ),
        land_area_sqm=ExtractedField(value="62", snippet="Diện tích: 62 m2", confidence=0.8),
        address=ExtractedField(
            value="Hẻm 45 Nguyễn Văn A",
            snippet="Một đoạn không chứa giá trị",  # NOT grounded
            confidence=0.9,
        ),
    )


def _so_hong_doc() -> IngestedDoc:
    parsed = ParsedDocument(
        text="GIẤY CHỨNG NHẬN ... Người sử dụng đất: Ông Nguyễn Văn A ...",
        file_type=FileType.PDF,
        pages=[PageContent(page_number=1, text="...", is_scanned=False)],
        page_count=1,
        is_scanned=False,
    )
    return IngestedDoc("f1", "so-hong.pdf", DocType.SO_DO_SO_HONG, parsed)


def _text_pdf(text: str) -> bytes:
    """Build a simple text PDF (ASCII) for ingest plumbing tests."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


# Long enough (> scan threshold) so the page is treated as text, not scanned.
_SO_HONG_TEXT = (
    "GIAY CHUNG NHAN QUYEN SU DUNG DAT - So phat hanh CS 01234567 - "
    "Nguoi su dung dat: Ong Nguyen Van A - Dia chi Hem 45"
)


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #
def test_is_grounded():
    """A value is grounded only when it appears within the snippet."""
    assert _is_grounded("CS 01234567", "Số phát hành: CS 01234567") is True
    assert _is_grounded("62 m2", "Diện tích  62   m2 tại thửa") is True  # whitespace-normalized
    assert _is_grounded("Hẻm 45", "đoạn khác") is False
    assert _is_grounded("x", None) is False


def test_classify_by_keywords():
    """Keyword classification routes each document to the right DocType."""
    assert classify_by_keywords("GIẤY CHỨNG NHẬN QUYỀN SỬ DỤNG ĐẤT") == DocType.SO_DO_SO_HONG
    assert classify_by_keywords("Tờ khai lệ phí trước bạ nhà đất") == DocType.TO_KHAI_LPTB
    assert classify_by_keywords("Biên bản bàn giao căn hộ") == DocType.BIEN_BAN_BAN_GIAO
    assert classify_by_keywords("Thông báo nộp thuế sử dụng đất") == DocType.THONG_BAO_THUE_DAT
    assert classify_by_keywords("một văn bản bất kỳ") == DocType.KHAC


# --------------------------------------------------------------------------- #
# extract_node (mocked LLM)
# --------------------------------------------------------------------------- #
async def test_extract_node_maps_and_grounds(monkeypatch):
    """extract_node maps fields, normalizes, and applies grounding + tiering."""
    monkeypatch.setattr(extract_mod, "get_chat_model", lambda: _FakeChat(_sample_extraction()))
    state = {"docs": [_so_hong_doc()], "canonical": {}, "warnings": [], "ctx": None}

    result = await extract_node(state)
    canon = result["canonical"]

    # High-confidence grounded value -> auto-filled
    assert canon["owner_full_name"].value == "Nguyễn Văn A"
    assert canon["owner_full_name"].status == FieldStatus.DA_XAC_THUC
    assert canon["certificate_number"].status == FieldStatus.DA_XAC_THUC

    # Area normalized to "<n> m²"; 0.8 confidence -> needs review (< 0.85)
    assert canon["land_area_sqm"].value == "62 m²"
    assert canon["land_area_sqm"].status == FieldStatus.CAN_XAC_MINH

    # Not grounded -> confidence capped -> needs review
    assert canon["address"].confidence <= 0.55
    assert canon["address"].status == FieldStatus.CAN_XAC_MINH

    # Relationship is derived (inferred) when an owner name exists
    assert canon["relationship_to_asset"].status == FieldStatus.SUY_LUAN


async def test_extract_node_warns_on_unsupported_type():
    """Non-Sổ hồng documents are skipped with a warning (PR2 scope)."""
    parsed = ParsedDocument(text="tax notice", file_type=FileType.PDF, page_count=1)
    doc = IngestedDoc("f2", "thue.pdf", DocType.THONG_BAO_THUE_DAT, parsed)
    result = await extract_node({"docs": [doc], "canonical": {}, "warnings": [], "ctx": None})
    assert result["canonical"] == {}
    assert any("chưa được hỗ trợ" in w for w in result["warnings"])


async def test_extract_node_warns_on_scanned():
    """Scanned Sổ hồng (no text) defers to vision extraction with a warning."""
    parsed = ParsedDocument(text="", file_type=FileType.PDF, page_count=1, is_scanned=True)
    doc = IngestedDoc("f3", "scan.pdf", DocType.SO_DO_SO_HONG, parsed)
    result = await extract_node({"docs": [doc], "canonical": {}, "warnings": [], "ctx": None})
    assert result["canonical"] == {}
    assert any("scan" in w.lower() for w in result["warnings"])


# --------------------------------------------------------------------------- #
# assemble_node
# --------------------------------------------------------------------------- #
async def test_assemble_node_full_registry(monkeypatch):
    """assemble_node emits every registry field; missing ones are manual-entry."""
    monkeypatch.setattr(extract_mod, "get_chat_model", lambda: _FakeChat(_sample_extraction()))
    extracted = await extract_node(
        {"docs": [_so_hong_doc()], "canonical": {}, "warnings": [], "ctx": None}
    )
    state = {
        "input": PropertyIntakeInput(file_ids=["f1"], case_id="REQ-2026-0001"),
        "canonical": extracted["canonical"],
        "documents_info": [],
        "warnings": [],
    }
    out = (await assemble_node(state))["output"]

    assert out.case_id == "REQ-2026-0001"
    assert len(out.fields) == len(CANONICAL_FIELDS)
    by_key = {f.key: f for f in out.fields}
    assert by_key["owner_full_name"].value == "Nguyễn Văn A"
    # Loan fields are never in property documents -> manual entry
    assert by_key["loan_amount_vnd"].value is None
    assert by_key["loan_amount_vnd"].status == FieldStatus.NHAP_TAY


# --------------------------------------------------------------------------- #
# ingest_node
# --------------------------------------------------------------------------- #
async def test_ingest_node_reads_and_parses():
    """ingest_node loads bytes via storage, parses, and records document info."""
    storage = _FakeStorage()
    storage.add("f1", "so-hong.pdf", "application/pdf", _text_pdf(_SO_HONG_TEXT))
    ctx = SimpleNamespace(storage_service=storage, update_progress=None)
    state = {"input": PropertyIntakeInput(file_ids=["f1"]), "ctx": ctx, "warnings": []}

    result = await ingest_node(state)
    assert len(result["docs"]) == 1
    doc = result["docs"][0]
    assert doc.file_name == "so-hong.pdf"
    assert doc.parsed.has_text
    assert result["documents_info"][0].page_count == 1
    assert result["documents_info"][0].is_scanned is False


async def test_ingest_node_missing_file_warns():
    """A missing file id produces a warning and no document."""
    ctx = SimpleNamespace(storage_service=_FakeStorage(), update_progress=None)
    state = {"input": PropertyIntakeInput(file_ids=["nope"]), "ctx": ctx, "warnings": []}
    result = await ingest_node(state)
    assert result["docs"] == []
    assert any("Không tìm thấy" in w for w in result["warnings"])


# --------------------------------------------------------------------------- #
# End-to-end graph (mocked LLM)
# --------------------------------------------------------------------------- #
async def test_run_intake_end_to_end(monkeypatch):
    """Full pipeline: ingest a Vietnamese Sổ hồng PDF, extract, assemble output."""
    monkeypatch.setattr(extract_mod, "get_chat_model", lambda: _FakeChat(_sample_extraction()))
    # Classification is unit-tested separately; stub it here so the e2e test does
    # not depend on Vietnamese font round-tripping through the PDF renderer.
    monkeypatch.setattr(ingest_mod, "classify_by_keywords", lambda _text: DocType.SO_DO_SO_HONG)
    storage = _FakeStorage()
    storage.add("f1", "so-hong.pdf", "application/pdf", _text_pdf(_SO_HONG_TEXT))
    ctx = SimpleNamespace(storage_service=storage, update_progress=None)

    out = await run_intake(PropertyIntakeInput(file_ids=["f1"]), ctx)

    assert len(out.documents) == 1
    assert out.documents[0].doc_type == DocType.SO_DO_SO_HONG
    by_key = {f.key: f for f in out.fields}
    assert by_key["owner_full_name"].value == "Nguyễn Văn A"
    assert by_key["owner_full_name"].status == FieldStatus.DA_XAC_THUC


# --------------------------------------------------------------------------- #
# Registry discovery
# --------------------------------------------------------------------------- #
def test_registry_discovers_property_intake():
    """The plugin is auto-discovered with async + file-accepting metadata."""
    registry = AIServiceRegistry()
    registry.discover_and_register()
    service = registry.get("property_intake")
    assert service is not None
    assert service.meta.is_async is True
    assert service.meta.accepts_file is True
    assert "pdf" in service.meta.file_types
