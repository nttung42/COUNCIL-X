"""Pydantic schemas for the property_intake plugin.

Three layers of models:

* **Extraction** (``ExtractedField`` / ``SoHongExtraction``) — what the LLM
  returns per document. Every value carries its own evidence (``snippet``) and
  self-reported ``confidence`` to enable grounding checks.
* **Canonical** (``FieldValue``) — a reconciled value for one form field with
  provenance + status, independent of which document it came from.
* **I/O** (``PropertyIntakeInput`` / ``PropertyIntakeOutput`` / ``FormField`` /
  ``DocumentInfo``) — the service contract; ``PropertyIntakeOutput`` maps 1:1 to
  the mockup's "Nhập thông tin" tab.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class DocType(StrEnum):
    """Recognized property document types."""

    SO_DO_SO_HONG = "so_do_so_hong"
    TO_KHAI_LPTB = "to_khai_lptb"
    BIEN_BAN_BAN_GIAO = "bien_ban_ban_giao"
    THONG_BAO_THUE_DAT = "thong_bao_thue_dat"
    KHAC = "khac"


class FieldStatus(StrEnum):
    """Per-field extraction status (mirrors the mockup's field states)."""

    DA_XAC_THUC = "da_xac_thuc"  # high confidence, grounded -> auto-filled
    CAN_XAC_MINH = "can_xac_minh"  # medium/low or weak grounding -> needs review
    MAU_THUAN = "mau_thuan"  # multiple documents disagree
    NHAP_TAY = "nhap_tay"  # not found in documents -> manual entry
    SUY_LUAN = "suy_luan"  # inferred, no direct source span


# --------------------------------------------------------------------------- #
# Extraction layer (LLM output)
# --------------------------------------------------------------------------- #
class ExtractedField(BaseModel):
    """One field extracted from a document, with grounding evidence."""

    value: str | None = Field(
        default=None,
        description="Giá trị trích NGUYÊN VĂN từ tài liệu; null nếu tài liệu không nêu.",
    )
    snippet: str | None = Field(
        default=None,
        description="Đoạn văn bản gốc (nguyên văn) chứa giá trị, để đối chiếu.",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Độ tin cậy 0..1 do mô hình tự đánh giá.",
    )


class SoHongExtraction(BaseModel):
    """Structured fields extracted from a Sổ đỏ / Sổ hồng (GCN).

    Every field is optional: when the certificate does not state a value the
    model must return ``null`` (never guess). Field names match canonical keys.
    """

    owner_full_name: ExtractedField | None = None
    owner_national_id: ExtractedField | None = None
    certificate_type: ExtractedField | None = None
    certificate_number: ExtractedField | None = None
    issue_date: ExtractedField | None = None
    issuing_authority: ExtractedField | None = None
    land_plot_number: ExtractedField | None = None
    map_sheet_number: ExtractedField | None = None
    land_use_purpose: ExtractedField | None = None
    use_term: ExtractedField | None = None
    ownership_form: ExtractedField | None = None
    address: ExtractedField | None = None
    land_area_sqm: ExtractedField | None = None
    floor_area_sqm: ExtractedField | None = None
    num_floors_desc: ExtractedField | None = None
    frontage_m: ExtractedField | None = None
    depth_m: ExtractedField | None = None
    alley_width_m: ExtractedField | None = None
    construction_year: ExtractedField | None = None
    structure_material: ExtractedField | None = None
    house_direction: ExtractedField | None = None


class ToKhaiLPTBExtraction(BaseModel):
    """Fields extracted from a Tờ khai lệ phí trước bạ nhà, đất.

    The declaration restates the taxpayer/owner, the property address and its
    physical characteristics used to compute the registration fee. Every field
    is optional; return ``null`` when the form does not state it.
    """

    owner_full_name: ExtractedField | None = None
    owner_national_id: ExtractedField | None = None
    address: ExtractedField | None = None
    property_type: ExtractedField | None = None
    certificate_number: ExtractedField | None = None
    land_plot_number: ExtractedField | None = None
    map_sheet_number: ExtractedField | None = None
    land_area_sqm: ExtractedField | None = None
    floor_area_sqm: ExtractedField | None = None
    construction_year: ExtractedField | None = None


class BienBanBanGiaoExtraction(BaseModel):
    """Fields extracted from a Biên bản bàn giao (nhà/căn hộ).

    The handover record identifies the receiving party and describes the
    delivered property (address, area, floors, condition). Every field is
    optional; return ``null`` when the record does not state it.
    """

    owner_full_name: ExtractedField | None = None
    address: ExtractedField | None = None
    property_type: ExtractedField | None = None
    land_area_sqm: ExtractedField | None = None
    floor_area_sqm: ExtractedField | None = None
    num_floors_desc: ExtractedField | None = None
    construction_year: ExtractedField | None = None
    current_usage_status: ExtractedField | None = None


class ThongBaoThueDatExtraction(BaseModel):
    """Fields extracted from a Thông báo nộp thuế sử dụng đất.

    The tax notice names the taxpayer and the taxed land parcel (address, area,
    use purpose, parcel/map numbers). Every field is optional; return ``null``
    when the notice does not state it.
    """

    owner_full_name: ExtractedField | None = None
    owner_national_id: ExtractedField | None = None
    address: ExtractedField | None = None
    land_area_sqm: ExtractedField | None = None
    land_use_purpose: ExtractedField | None = None
    land_plot_number: ExtractedField | None = None
    map_sheet_number: ExtractedField | None = None


class DocClassification(BaseModel):
    """LLM verdict on which property document type a text belongs to."""

    doc_type: DocType = Field(
        ...,
        description="Loại tài liệu phù hợp nhất trong danh sách cho phép.",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Độ tin cậy phân loại 0..1.",
    )


# --------------------------------------------------------------------------- #
# Verification layer (LLM-judge output, feature #5)
# --------------------------------------------------------------------------- #
class FieldVerification(BaseModel):
    """LLM-judge verdict on whether one extracted value is supported by evidence."""

    index: int = Field(..., description="Chỉ số mục cần kiểm tra (khớp yêu cầu).")
    supported: bool = Field(
        ...,
        description="True nếu giá trị được đoạn trích nguồn xác nhận rõ ràng.",
    )
    reason: str | None = Field(default=None, description="Lý do ngắn gọn (tuỳ chọn).")


class VerificationResult(BaseModel):
    """Batch verification verdicts for a set of extracted values."""

    checks: list[FieldVerification] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Canonical layer (reconciled value + provenance)
# --------------------------------------------------------------------------- #
class BBox(BaseModel):
    """Bounding box for a source span on a document page image.

    Coordinates are normalized to ``0..1`` (origin = top-left). The page number
    is carried separately by ``source_page`` — mirroring the DB columns
    ``field_provenance.bbox_x/y/width/height`` + ``source_page``.
    """

    x: float
    y: float
    width: float
    height: float


class FieldValue(BaseModel):
    """A reconciled value for a single canonical field, with provenance.

    ``value`` keeps the **verbatim** text as read from the document; ``normalized``
    holds the code-normalized, typed value (money → int VND, area → float m²,
    date → ISO ``YYYY-MM-DD``) or ``None`` when the field has no normalizer or is
    unparseable.

    Later pipeline stages annotate the value: ``verifier_passed`` records the
    LLM-judge verdict (#5), ``validation_flags`` lists failed rule/arithmetic
    checks (feature 4), and ``alternatives`` retains the competing values from
    other documents when the merge could not reconcile them (``mau_thuan``).
    """

    value: str | None = None
    normalized: int | float | str | None = None
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0
    )  # internal 0..1; output uses confidence_pct
    status: FieldStatus = FieldStatus.NHAP_TAY
    source_doc: str | None = None  # file name (display)
    source_file_id: str | None = (
        None  # attached_document.id (for field_provenance.source_document_id)
    )
    source_doc_type: DocType | None = None
    source_page: int | None = None
    source_snippet: str | None = None
    bbox: BBox | None = None
    verifier_passed: bool | None = None
    validation_flags: list[str] = Field(default_factory=list)
    alternatives: list["FieldValue"] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Service I/O
# --------------------------------------------------------------------------- #
class PropertyIntakeInput(BaseModel):
    """Input: uploaded file ids to extract from."""

    file_ids: list[str] = Field(
        ...,
        min_length=1,
        description="Danh sách file_id đã upload (sổ đỏ/hồng, tờ khai, biên bản, thông báo thuế).",
    )
    language: str = Field(default="vi", description="Ngôn ngữ tài liệu.")
    case_id: str | None = Field(default=None, description="Mã hồ sơ (REQ-...), nếu có.")


class DocumentInfo(BaseModel):
    """Per-document metadata surfaced in the output (→ ``attached_document``)."""

    file_id: str  # = attached_document.id
    file_name: str
    detected_doc_type: DocType  # → attached_document.detected_doc_type
    is_scan: bool  # → attached_document.is_scan
    page_count: int


class AlternativeValue(BaseModel):
    """A competing value from another document for a ``mau_thuan`` field.

    Each maps to one extra ``field_provenance`` row with ``is_selected = false``.
    """

    value: str | None = None
    normalized: int | float | str | None = None
    status: FieldStatus = FieldStatus.MAU_THUAN
    confidence_pct: int = Field(default=0, ge=0, le=100)
    source_file_id: str | None = None
    source_doc_type: DocType | None = None
    source_page: int | None = None
    source_snippet: str | None = None
    bbox: BBox | None = None


class FormField(BaseModel):
    """A single form field ready to render on the "Nhập thông tin" tab.

    Carries the DB write target (``target_table``/``target_field``) and provenance
    so the backend can persist it into the 4 Màn-1 tables + ``field_provenance``
    without extra lookups. See ai/docs/contracts/property-intake-contract.md.
    """

    key: str
    section: str  # 'A' | 'B' | 'C' | 'D'
    label: str
    target_table: str
    target_field: str
    value: str | None
    normalized: int | float | str | None = None
    status: FieldStatus
    confidence_pct: int = Field(default=0, ge=0, le=100)
    source_file_id: str | None = None
    source_page: int | None = None
    source_snippet: str | None = None
    bbox: BBox | None = None
    verifier_passed: bool | None = None
    validation_flags: list[str] = Field(default_factory=list)
    alternatives: list[AlternativeValue] = Field(default_factory=list)


class PropertyIntakeOutput(BaseModel):
    """Output: documents processed + form fields with provenance + warnings."""

    case_id: str | None = None
    documents: list[DocumentInfo] = Field(default_factory=list)
    fields: list[FormField] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
