"""Tests for the property_intake plugin.

Covers PR3 (classifier + 4 extractors, Group-A grounding/normalizers) and PR4
(verifier, cross-document merge, validators, confidence tiering). The LLM is
replaced with fakes returning fixed extraction / classification / verification
objects so the pipeline runs deterministically offline.
"""

from __future__ import annotations

from types import SimpleNamespace

import fitz  # PyMuPDF

from shb.ai.plugins.property_intake.classify import classify_document
from shb.ai.plugins.property_intake.documents import (
    CANONICAL_FIELDS,
    classify_by_keywords,
    normalize_date,
    normalize_field,
    normalize_money,
    normalize_numeric,
    source_priority,
    tier_status,
    values_agree,
)
from shb.ai.plugins.property_intake.graph import run_intake
from shb.ai.plugins.property_intake.nodes import extract as extract_mod
from shb.ai.plugins.property_intake.nodes import ingest as ingest_mod
from shb.ai.plugins.property_intake.nodes import verify as verify_mod
from shb.ai.plugins.property_intake.nodes.assemble import assemble_node
from shb.ai.plugins.property_intake.nodes.extract import _is_grounded, extract_node
from shb.ai.plugins.property_intake.nodes.ingest import ingest_node
from shb.ai.plugins.property_intake.nodes.merge import merge_candidates, merge_node
from shb.ai.plugins.property_intake.nodes.validate import validate_node
from shb.ai.plugins.property_intake.nodes.verify import verify_node
from shb.ai.plugins.property_intake.schema import (
    BienBanBanGiaoExtraction,
    DocClassification,
    DocType,
    ExtractedField,
    FieldStatus,
    FieldValue,
    FieldVerification,
    PropertyIntakeInput,
    SoHongExtraction,
    ThongBaoThueDatExtraction,
    ToKhaiLPTBExtraction,
    VerificationResult,
)
from shb.ai.plugins.property_intake.state import IngestedDoc
from shb.ai.plugins.property_intake.validators import (
    check_areas,
    check_construction_year,
    check_frontage_depth,
    check_national_id,
)
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


def _all_supported(n: int = 16) -> VerificationResult:
    """Build a verifier verdict that passes every index."""
    return VerificationResult(checks=[FieldVerification(index=i, supported=True) for i in range(n)])


def _fake_verifier(monkeypatch, result: VerificationResult) -> None:
    monkeypatch.setattr(verify_mod, "get_chat_model", lambda: _FakeChat(result))


def _fv(
    value,
    *,
    normalized=None,
    conf=0.9,
    dt=DocType.SO_DO_SO_HONG,
    doc="a.pdf",
    status=FieldStatus.DA_XAC_THUC,
    snippet="đoạn nguồn",
) -> FieldValue:
    return FieldValue(
        value=value,
        normalized=normalized,
        confidence=conf,
        status=status,
        source_doc=doc,
        source_doc_type=dt,
        source_snippet=snippet,
    )


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
        issue_date=ExtractedField(
            value="ngày 15 tháng 03 năm 2020",
            snippet="Cấp ngày 15 tháng 03 năm 2020",
            confidence=0.9,
        ),
        address=ExtractedField(
            value="Hẻm 45 Nguyễn Văn A",
            snippet="Một đoạn không chứa giá trị",  # NOT grounded -> dropped
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


def _doc(doc_type: DocType, name: str) -> IngestedDoc:
    parsed = ParsedDocument(
        text="nội dung tài liệu đủ dài để không bị coi là scan ...",
        file_type=FileType.PDF,
        pages=[PageContent(page_number=1, text="...", is_scanned=False)],
        page_count=1,
        is_scanned=False,
    )
    return IngestedDoc("fx", name, doc_type, parsed)


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


def _fake_classify(doc_type: DocType):
    async def _inner(_text, **_kwargs):
        return doc_type

    return _inner


# --------------------------------------------------------------------------- #
# Pure helpers: grounding + keyword classifier
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
# Typed normalizers (documents.py) — Group-A (3)
# --------------------------------------------------------------------------- #
def test_normalize_numeric():
    """Areas parse to float across VN/EN notations; junk -> None."""
    assert normalize_numeric("62") == 62.0
    assert normalize_numeric("62,5 m²") == 62.5
    assert normalize_numeric("1.234") == 1234.0
    assert normalize_numeric("1.234,5") == 1234.5
    assert normalize_numeric("Diện tích: 80 m2") == 80.0
    assert normalize_numeric("không có số") is None


def test_normalize_money():
    """Money parses to an integer VND amount, honoring multiplier words."""
    assert normalize_money("1.500.000.000 đồng") == 1_500_000_000
    assert normalize_money("1,5 tỷ") == 1_500_000_000
    assert normalize_money("800 triệu") == 800_000_000
    assert normalize_money("2000000000") == 2_000_000_000
    assert normalize_money("miễn phí") is None


def test_normalize_date():
    """Dates normalize to ISO YYYY-MM-DD; unparseable -> None."""
    assert normalize_date("01/02/2023") == "2023-02-01"
    assert normalize_date("ngày 15 tháng 03 năm 2020") == "2020-03-15"
    assert normalize_date("5-6-2021") == "2021-06-05"
    assert normalize_date("32/13/2020") is None  # invalid day/month
    assert normalize_date("không có ngày") is None


def test_normalize_field_routing():
    """normalize_field dispatches by canonical key type (matches DB column types)."""
    assert normalize_field("loan_amount_vnd", "1,5 tỷ") == 1_500_000_000  # BIGINT
    assert normalize_field("land_area_sqm", "62,5") == 62.5  # NUMERIC
    assert normalize_field("frontage_m", "4,5 m") == 4.5  # NUMERIC (PR4.1)
    assert normalize_field("depth_m", "13") == 13.0  # NUMERIC (PR4.1)
    assert normalize_field("construction_year", "Năm 2015") == 2015  # SMALLINT int (PR4.1)
    assert normalize_field("loan_term_years", "20 năm") == 20  # SMALLINT int (PR4.1)
    assert normalize_field("issue_date", "01/02/2023") == "2023-02-01"  # DATE
    assert normalize_field("owner_full_name", "Nguyễn Văn A") is None  # no normalizer


# --------------------------------------------------------------------------- #
# LLM classifier (mocked)
# --------------------------------------------------------------------------- #
async def test_classify_document_uses_llm():
    """classify_document returns the LLM verdict when text is present."""
    fake = _FakeStructured(DocClassification(doc_type=DocType.TO_KHAI_LPTB, confidence=0.9))
    result = await classify_document("Tờ khai lệ phí trước bạ ...", classifier=fake)
    assert result == DocType.TO_KHAI_LPTB


async def test_classify_document_empty_falls_back_to_keywords():
    """Empty text (e.g. un-OCR'd scan) uses the keyword classifier."""
    result = await classify_document("", classifier=_FakeStructured(None))
    assert result == DocType.KHAC


async def test_classify_document_error_falls_back_to_keywords():
    """A failing LLM call falls back to keyword classification, not a crash."""

    class _Boom:
        async def ainvoke(self, _messages):
            raise RuntimeError("model down")

    result = await classify_document("Biên bản bàn giao căn hộ", classifier=_Boom())
    assert result == DocType.BIEN_BAN_BAN_GIAO


# --------------------------------------------------------------------------- #
# extract_node (mocked LLM) — now emits per-field candidate lists
# --------------------------------------------------------------------------- #
async def test_extract_node_maps_grounds_and_normalizes(monkeypatch):
    """extract_node maps fields, drops ungrounded, and adds typed normalized values."""
    monkeypatch.setattr(extract_mod, "get_chat_model", lambda: _FakeChat(_sample_extraction()))
    state = {"docs": [_so_hong_doc()], "candidates": {}, "warnings": [], "ctx": None}

    result = await extract_node(state)
    cand = result["candidates"]

    owner = cand["owner_full_name"][0]
    assert owner.value == "Nguyễn Văn A"
    assert owner.source_doc_type == DocType.SO_DO_SO_HONG
    assert owner.confidence == 0.95

    # Verbatim value preserved; typed normalized value added.
    assert cand["land_area_sqm"][0].value == "62"
    assert cand["land_area_sqm"][0].normalized == 62.0
    assert cand["issue_date"][0].normalized == "2020-03-15"

    # Group-A: mandatory grounding — ungrounded value is dropped entirely.
    assert "address" not in cand

    # Relationship is derived (inferred) when an owner name exists.
    assert cand["relationship_to_asset"][0].status == FieldStatus.SUY_LUAN


async def test_extract_node_to_khai_lptb(monkeypatch):
    """Tờ khai LPTB routes to its extractor and maps to canonical keys."""
    extraction = ToKhaiLPTBExtraction(
        owner_full_name=ExtractedField(
            value="Trần Thị B", snippet="Người nộp: Trần Thị B", confidence=0.9
        ),
        land_area_sqm=ExtractedField(value="80", snippet="Diện tích 80 m2", confidence=0.9),
    )
    monkeypatch.setattr(extract_mod, "get_chat_model", lambda: _FakeChat(extraction))
    result = await extract_node(
        {
            "docs": [_doc(DocType.TO_KHAI_LPTB, "tokhai.pdf")],
            "candidates": {},
            "warnings": [],
            "ctx": None,
        }
    )
    cand = result["candidates"]
    assert cand["owner_full_name"][0].value == "Trần Thị B"
    assert cand["land_area_sqm"][0].normalized == 80.0
    assert "relationship_to_asset" not in cand  # so_hong-only derivation


async def test_extract_node_bien_ban_ban_giao(monkeypatch):
    """Biên bản bàn giao routes to its extractor."""
    extraction = BienBanBanGiaoExtraction(
        owner_full_name=ExtractedField(
            value="Lê Văn C", snippet="Bên nhận: Lê Văn C", confidence=0.88
        ),
        current_usage_status=ExtractedField(
            value="đã hoàn thiện", snippet="Hiện trạng: đã hoàn thiện", confidence=0.8
        ),
    )
    monkeypatch.setattr(extract_mod, "get_chat_model", lambda: _FakeChat(extraction))
    result = await extract_node(
        {
            "docs": [_doc(DocType.BIEN_BAN_BAN_GIAO, "bbbg.pdf")],
            "candidates": {},
            "warnings": [],
            "ctx": None,
        }
    )
    cand = result["candidates"]
    assert cand["owner_full_name"][0].value == "Lê Văn C"
    assert cand["current_usage_status"][0].value == "đã hoàn thiện"


async def test_extract_node_thong_bao_thue_dat(monkeypatch):
    """Thông báo thuế đất routes to its extractor."""
    extraction = ThongBaoThueDatExtraction(
        owner_full_name=ExtractedField(
            value="Phạm Thị D", snippet="Người nộp thuế: Phạm Thị D", confidence=0.9
        ),
        land_use_purpose=ExtractedField(
            value="Đất ở tại đô thị", snippet="Mục đích: Đất ở tại đô thị", confidence=0.9
        ),
    )
    monkeypatch.setattr(extract_mod, "get_chat_model", lambda: _FakeChat(extraction))
    result = await extract_node(
        {
            "docs": [_doc(DocType.THONG_BAO_THUE_DAT, "thue.pdf")],
            "candidates": {},
            "warnings": [],
            "ctx": None,
        }
    )
    cand = result["candidates"]
    assert cand["owner_full_name"][0].value == "Phạm Thị D"
    assert cand["land_use_purpose"][0].value == "Đất ở tại đô thị"


async def test_extract_node_warns_on_unsupported_type():
    """Unknown document types (KHAC) are skipped with a warning."""
    parsed = ParsedDocument(text="văn bản linh tinh", file_type=FileType.PDF, page_count=1)
    doc = IngestedDoc("f2", "khac.pdf", DocType.KHAC, parsed)
    result = await extract_node({"docs": [doc], "candidates": {}, "warnings": [], "ctx": None})
    assert result["candidates"] == {}
    assert any("chưa được hỗ trợ" in w for w in result["warnings"])


async def test_extract_node_warns_on_scanned():
    """Scanned Sổ hồng (no text) defers to vision extraction with a warning."""
    parsed = ParsedDocument(text="", file_type=FileType.PDF, page_count=1, is_scanned=True)
    doc = IngestedDoc("f3", "scan.pdf", DocType.SO_DO_SO_HONG, parsed)
    result = await extract_node({"docs": [doc], "candidates": {}, "warnings": [], "ctx": None})
    assert result["candidates"] == {}
    assert any("scan" in w.lower() for w in result["warnings"])


# --------------------------------------------------------------------------- #
# verify_node (feature #5)
# --------------------------------------------------------------------------- #
async def test_verify_node_rejects_and_caps_confidence(monkeypatch):
    """A value the judge rejects gets verifier_passed=False and capped confidence."""
    _fake_verifier(
        monkeypatch, VerificationResult(checks=[FieldVerification(index=0, supported=False)])
    )
    candidates = {"owner_full_name": [_fv("Nguyễn Văn A", conf=0.95)]}
    result = await verify_node({"candidates": candidates, "warnings": [], "ctx": None})
    fv = result["candidates"]["owner_full_name"][0]
    assert fv.verifier_passed is False
    assert fv.confidence <= 0.40


async def test_verify_node_accepts(monkeypatch):
    """A supported value keeps its confidence and is marked passed."""
    _fake_verifier(monkeypatch, _all_supported())
    candidates = {"certificate_number": [_fv("CS 01234567", conf=0.9)]}
    result = await verify_node({"candidates": candidates, "warnings": [], "ctx": None})
    fv = result["candidates"]["certificate_number"][0]
    assert fv.verifier_passed is True
    assert fv.confidence == 0.9


async def test_verify_node_fail_open(monkeypatch):
    """A verifier outage leaves values unjudged (fail-open), not blanked."""

    class _Boom(_FakeChat):
        def with_structured_output(self, _schema):
            class _R:
                async def ainvoke(self, _messages):
                    raise RuntimeError("down")

            return _R()

    monkeypatch.setattr(verify_mod, "get_chat_model", lambda: _Boom(None))
    candidates = {"owner_full_name": [_fv("Nguyễn Văn A", conf=0.9)]}
    result = await verify_node({"candidates": candidates, "warnings": [], "ctx": None})
    fv = result["candidates"]["owner_full_name"][0]
    assert fv.verifier_passed is None
    assert fv.confidence == 0.9
    assert any("verifier" in w.lower() for w in result["warnings"])


# --------------------------------------------------------------------------- #
# Merge — source priority + conflict detection (PR4)
# --------------------------------------------------------------------------- #
def test_source_priority_order():
    """GCN outranks tax notice, which outranks tờ khai and biên bản."""
    assert source_priority(_fv("x", dt=DocType.SO_DO_SO_HONG)) > source_priority(
        _fv("x", dt=DocType.THONG_BAO_THUE_DAT)
    )
    assert source_priority(_fv("x", dt=DocType.TO_KHAI_LPTB)) > source_priority(
        _fv("x", dt=DocType.BIEN_BAN_BAN_GIAO)
    )


def test_values_agree():
    """Numeric within tolerance agree; dates equal; text lenient."""
    assert values_agree(_fv("62", normalized=62.0), _fv("63", normalized=63.0)) is True  # <5%
    assert values_agree(_fv("62", normalized=62.0), _fv("80", normalized=80.0)) is False
    assert (
        values_agree(_fv("a", normalized="2020-03-15"), _fv("b", normalized="2020-03-15")) is True
    )
    assert values_agree(_fv("Nguyễn Văn A"), _fv("nguyễn  văn a")) is True  # casefold+ws
    assert values_agree(_fv("Nguyễn Văn A"), _fv("Trần Thị B")) is False


def test_merge_candidates_conflict_keeps_alternatives():
    """Conflicting sources -> mau_thuan; GCN wins; other value kept."""
    gcn = _fv("62", normalized=62.0, dt=DocType.SO_DO_SO_HONG, doc="gcn.pdf")
    tax = _fv("80", normalized=80.0, dt=DocType.THONG_BAO_THUE_DAT, doc="thue.pdf")
    merged = merge_candidates([tax, gcn])  # order shouldn't matter
    assert merged.value == "62"  # GCN priority wins
    assert merged.status == FieldStatus.MAU_THUAN
    assert [a.value for a in merged.alternatives] == ["80"]


def test_merge_candidates_agreement_corroborates():
    """Agreeing sources -> single value with a confidence bump."""
    gcn = _fv("62", normalized=62.0, conf=0.80, dt=DocType.SO_DO_SO_HONG)
    tax = _fv("62.5", normalized=62.5, conf=0.70, dt=DocType.THONG_BAO_THUE_DAT)
    merged = merge_candidates([gcn, tax])
    assert merged.status != FieldStatus.MAU_THUAN
    assert merged.confidence > 0.80  # corroboration bonus applied
    assert merged.alternatives == []


async def test_merge_node_flags_conflict_warning():
    """merge_node reconciles candidates and warns on conflicts."""
    candidates = {
        "address": [
            _fv("123 Lê Lợi", dt=DocType.SO_DO_SO_HONG, doc="gcn.pdf"),
            _fv("456 Trần Hưng Đạo", dt=DocType.TO_KHAI_LPTB, doc="tk.pdf"),
        ],
        "owner_full_name": [_fv("Nguyễn Văn A", dt=DocType.SO_DO_SO_HONG)],
    }
    result = await merge_node({"candidates": candidates, "warnings": [], "ctx": None})
    canon = result["canonical"]
    assert canon["address"].value == "123 Lê Lợi"
    assert canon["address"].status == FieldStatus.MAU_THUAN
    assert canon["owner_full_name"].status != FieldStatus.MAU_THUAN
    assert any("mâu thuẫn" in w for w in result["warnings"])


# --------------------------------------------------------------------------- #
# Validators (feature 4)
# --------------------------------------------------------------------------- #
def test_check_national_id():
    """CCCD(12)/CMND(9) pass; other lengths flag."""
    assert check_national_id({"owner_national_id": _fv("001099012345")}) == []  # 12
    assert check_national_id({"owner_national_id": _fv("012345678")}) == []  # 9
    issues = check_national_id({"owner_national_id": _fv("12345")})
    assert issues and issues[0].key == "owner_national_id"


def test_check_construction_year():
    """Year within range passes; out-of-range flags."""
    assert check_construction_year({"construction_year": _fv("2015")}) == []
    assert check_construction_year({"construction_year": _fv("1850")})
    assert check_construction_year({"construction_year": _fv("năm 3000")})


def test_check_areas_arithmetic():
    """Floor ≈ land × số tầng passes; large mismatch flags; negatives flag."""
    ok = {
        "land_area_sqm": _fv("60", normalized=60.0),
        "floor_area_sqm": _fv("180", normalized=180.0),
        "num_floors_desc": _fv("3 tầng"),
    }
    assert check_areas(ok) == []

    bad = {
        "land_area_sqm": _fv("60", normalized=60.0),
        "floor_area_sqm": _fv("300", normalized=300.0),
        "num_floors_desc": _fv("3 tầng"),
    }
    assert any(i.key == "floor_area_sqm" for i in check_areas(bad))

    assert any(check_areas({"land_area_sqm": _fv("-5", normalized=-5.0)}))


def test_check_frontage_depth():
    """Mặt tiền × chiều sâu ≈ diện tích passes; large mismatch flags (PR4.1)."""
    ok = {
        "land_area_sqm": _fv("60", normalized=60.0),
        "frontage_m": _fv("5", normalized=5.0),
        "depth_m": _fv("12", normalized=12.0),
    }
    assert check_frontage_depth(ok) == []

    bad = {
        "land_area_sqm": _fv("60", normalized=60.0),
        "frontage_m": _fv("4", normalized=4.0),
        "depth_m": _fv("30", normalized=30.0),  # 120 m² vs 60 m²
    }
    assert any(i.key == "land_area_sqm" for i in check_frontage_depth(bad))


async def test_validate_node_attaches_flags():
    """validate_node attaches validation flags that downgrade tiering later."""
    canonical = {"owner_national_id": _fv("12345", conf=0.95)}
    result = await validate_node({"canonical": canonical, "warnings": [], "ctx": None})
    fv = result["canonical"]["owner_national_id"]
    assert fv.validation_flags
    assert tier_status(fv) == FieldStatus.CAN_XAC_MINH


# --------------------------------------------------------------------------- #
# Confidence tiering (#9)
# --------------------------------------------------------------------------- #
def test_tier_status():
    """Tiering combines conflict, verifier, validation and confidence signals."""
    assert tier_status(_fv("x", status=FieldStatus.MAU_THUAN)) == FieldStatus.MAU_THUAN
    assert tier_status(_fv("x", status=FieldStatus.SUY_LUAN)) == FieldStatus.SUY_LUAN
    assert tier_status(FieldValue(value=None)) == FieldStatus.NHAP_TAY
    assert tier_status(_fv("x", conf=0.95)) == FieldStatus.DA_XAC_THUC
    assert tier_status(_fv("x", conf=0.70)) == FieldStatus.CAN_XAC_MINH

    failed = _fv("x", conf=0.95)
    failed.verifier_passed = False
    assert tier_status(failed) == FieldStatus.CAN_XAC_MINH

    flagged = _fv("x", conf=0.95)
    flagged.validation_flags = ["bad"]
    assert tier_status(flagged) == FieldStatus.CAN_XAC_MINH


# --------------------------------------------------------------------------- #
# assemble_node (extract -> merge -> assemble)
# --------------------------------------------------------------------------- #
async def test_assemble_node_full_registry(monkeypatch):
    """assemble_node emits every registry field; missing ones are manual-entry."""
    monkeypatch.setattr(extract_mod, "get_chat_model", lambda: _FakeChat(_sample_extraction()))
    extracted = await extract_node(
        {"docs": [_so_hong_doc()], "candidates": {}, "warnings": [], "ctx": None}
    )
    merged = await merge_node({"candidates": extracted["candidates"], "warnings": [], "ctx": None})
    state = {
        "input": PropertyIntakeInput(file_ids=["f1"], case_id="REQ-2026-0001"),
        "canonical": merged["canonical"],
        "documents_info": [],
        "warnings": [],
    }
    out = (await assemble_node(state))["output"]

    assert out.case_id == "REQ-2026-0001"
    assert len(out.fields) == len(CANONICAL_FIELDS)
    by_key = {f.key: f for f in out.fields}
    assert by_key["owner_full_name"].value == "Nguyễn Văn A"
    assert by_key["owner_full_name"].status == FieldStatus.DA_XAC_THUC
    assert by_key["land_area_sqm"].normalized == 62.0
    # Loan fields are never in property documents -> manual entry
    assert by_key["loan_amount_vnd"].value is None
    assert by_key["loan_amount_vnd"].status == FieldStatus.NHAP_TAY


async def test_assemble_emits_contract_shape():
    """Assemble projects a conflict into contract shape: confidence_pct + AlternativeValue."""
    candidates = {
        "land_area_sqm": [
            _fv("62", normalized=62.0, conf=0.9, dt=DocType.SO_DO_SO_HONG, doc="gcn.pdf"),
            _fv("80", normalized=80.0, conf=0.85, dt=DocType.THONG_BAO_THUE_DAT, doc="thue.pdf"),
        ]
    }
    merged = await merge_node({"candidates": candidates, "warnings": [], "ctx": None})
    state = {
        "input": PropertyIntakeInput(file_ids=["f1"]),
        "canonical": merged["canonical"],
        "documents_info": [],
        "warnings": [],
    }
    out = (await assemble_node(state))["output"]
    field = {f.key: f for f in out.fields}["land_area_sqm"]

    assert field.target_table == "property_physical_info"
    assert field.target_field == "land_area_sqm"
    assert field.status == FieldStatus.MAU_THUAN
    assert isinstance(field.confidence_pct, int) and 0 <= field.confidence_pct <= 100
    # Competing value kept in contract's AlternativeValue shape
    assert len(field.alternatives) == 1
    alt = field.alternatives[0]
    assert alt.value == "80"
    assert alt.status == FieldStatus.MAU_THUAN
    assert alt.confidence_pct == 85
    assert alt.source_doc_type == DocType.THONG_BAO_THUE_DAT


# --------------------------------------------------------------------------- #
# ingest_node
# --------------------------------------------------------------------------- #
async def test_ingest_node_reads_and_parses(monkeypatch):
    """ingest_node loads bytes via storage, parses, classifies, records info."""
    monkeypatch.setattr(ingest_mod, "classify_document", _fake_classify(DocType.SO_DO_SO_HONG))
    storage = _FakeStorage()
    storage.add("f1", "so-hong.pdf", "application/pdf", _text_pdf(_SO_HONG_TEXT))
    ctx = SimpleNamespace(storage_service=storage, update_progress=None)
    state = {"input": PropertyIntakeInput(file_ids=["f1"]), "ctx": ctx, "warnings": []}

    result = await ingest_node(state)
    assert len(result["docs"]) == 1
    doc = result["docs"][0]
    assert doc.file_name == "so-hong.pdf"
    assert doc.doc_type == DocType.SO_DO_SO_HONG
    assert doc.parsed.has_text
    assert result["documents_info"][0].page_count == 1
    assert result["documents_info"][0].is_scan is False
    assert result["documents_info"][0].detected_doc_type == DocType.SO_DO_SO_HONG


async def test_ingest_node_missing_file_warns():
    """A missing file id produces a warning and no document."""
    ctx = SimpleNamespace(storage_service=_FakeStorage(), update_progress=None)
    state = {"input": PropertyIntakeInput(file_ids=["nope"]), "ctx": ctx, "warnings": []}
    result = await ingest_node(state)
    assert result["docs"] == []
    assert any("Không tìm thấy" in w for w in result["warnings"])


# --------------------------------------------------------------------------- #
# End-to-end graph (mocked LLM across every node)
# --------------------------------------------------------------------------- #
async def test_run_intake_end_to_end(monkeypatch):
    """Full pipeline: ingest -> extract -> verify -> merge -> validate -> assemble."""
    monkeypatch.setattr(extract_mod, "get_chat_model", lambda: _FakeChat(_sample_extraction()))
    _fake_verifier(monkeypatch, _all_supported())
    monkeypatch.setattr(ingest_mod, "classify_document", _fake_classify(DocType.SO_DO_SO_HONG))
    storage = _FakeStorage()
    storage.add("f1", "so-hong.pdf", "application/pdf", _text_pdf(_SO_HONG_TEXT))
    ctx = SimpleNamespace(storage_service=storage, update_progress=None)

    out = await run_intake(PropertyIntakeInput(file_ids=["f1"]), ctx)

    assert len(out.documents) == 1
    assert out.documents[0].detected_doc_type == DocType.SO_DO_SO_HONG
    by_key = {f.key: f for f in out.fields}
    owner = by_key["owner_full_name"]
    assert owner.value == "Nguyễn Văn A"
    assert owner.status == FieldStatus.DA_XAC_THUC
    # PR4.1: contract fields present for backend persistence
    assert owner.target_table == "case_borrower"
    assert owner.target_field == "full_name"
    assert owner.source_file_id == "f1"
    assert owner.source_page == 1
    assert owner.confidence_pct == 95
    assert by_key["owner_full_name"].verifier_passed is True


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
