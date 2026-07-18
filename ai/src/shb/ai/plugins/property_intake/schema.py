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
    construction_year: ExtractedField | None = None
    structure_material: ExtractedField | None = None
    house_direction: ExtractedField | None = None


# --------------------------------------------------------------------------- #
# Canonical layer (reconciled value + provenance)
# --------------------------------------------------------------------------- #
class BBox(BaseModel):
    """Bounding box (percent of page) for a source span on a document image."""

    page: int
    x: float
    y: float
    w: float
    h: float


class FieldValue(BaseModel):
    """A reconciled value for a single canonical field, with provenance."""

    value: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    status: FieldStatus = FieldStatus.NHAP_TAY
    source_doc: str | None = None
    source_page: int | None = None
    source_snippet: str | None = None
    bbox: BBox | None = None


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
    """Per-document metadata surfaced in the output."""

    file_id: str
    file_name: str
    doc_type: DocType
    is_scanned: bool
    page_count: int


class FormField(BaseModel):
    """A single form field ready to render on the "Nhập thông tin" tab."""

    key: str
    section: str  # 'A' | 'B' | 'C' | 'D'
    label: str
    value: str | None
    confidence: float
    status: FieldStatus
    source_doc: str | None = None
    source_page: int | None = None
    source_snippet: str | None = None
    bbox: BBox | None = None


class PropertyIntakeOutput(BaseModel):
    """Output: documents processed + form fields with provenance + warnings."""

    case_id: str | None = None
    documents: list[DocumentInfo] = Field(default_factory=list)
    fields: list[FormField] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
