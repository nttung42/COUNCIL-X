"""SQLAlchemy ORM models for the PAA (Property Appraisal Agent) domain.

Mirrors ``PAA_Schema_PostgreSQL.sql`` (the standalone DDL design validated against
a real Postgres instance) but adapted to this project's ORM conventions so the
models work identically under Postgres (production, via Alembic — see
``alembic/versions/002_paa_schema.py``) and SQLite (tests, via
``Base.metadata.create_all`` in ``tests/conftest.py``):

* String PKs default to ``str(uuid.uuid4())`` (matches ``User``/``Job``/``File``),
  not a native Postgres ``UUID`` column type.
* Enums are plain ``sa.Enum(PyEnum, name=...)`` (portable — becomes a native
  Postgres ``ENUM`` type, a ``VARCHAR + CHECK`` on SQLite).
* ``TEXT[]`` bullet-list columns (``raw_findings``, ``inputs``) become generic
  ``JSON`` (list[str]) — Postgres ``ARRAY`` has no SQLite equivalent.
* Postgres-only constructs from the original DDL (the ``touch_case_updated_at``
  trigger, the ``v_case_history`` / ``v_dashboard_kpi`` views) are intentionally
  NOT reproduced here as DB objects; they are reimplemented as plain parametrized
  queries in ``shb/capabilities/dashboard/queries.py`` so they also work on
  SQLite and are directly callable as agent tools.

This module is imported as a side effect of importing the ``shb.db`` package
(see ``shb/db/__init__.py``), so ``Base.metadata`` always includes these tables
whenever anything does ``from shb.db.models import Base`` — no extra wiring
needed in ``alembic/env.py`` or ``tests/conftest.py``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from enum import Enum

from sqlalchemy import (
    JSON,
)
from sqlalchemy import BigInteger as BigInt
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from shb.db.models import Base

# --------------------------------------------------------------------------- #
# Enum types (values are Vietnamese domain codes — persisted as the DB value,
# matched 1:1 against PAA_Schema_PostgreSQL.sql's ``CREATE TYPE`` statements)
# --------------------------------------------------------------------------- #


class CaseStatus(str, Enum):
    """Trạng thái hồ sơ — badge màu ở "Lịch sử hồ sơ" (sidebar)."""

    DANG_XU_LY = "dang_xu_ly"
    HOAN_TAT = "hoan_tat"
    HUY = "huy"


class StepStatus(str, Enum):
    """Trạng thái từng subtab (1..5): khoá / mở khoá / đã xác nhận."""

    LOCKED = "locked"
    UNLOCKED = "unlocked"
    CONFIRMED = "confirmed"


class SeverityLevel(str, Enum):
    """4 mức nghiêm trọng dùng chung cho risk_flag / risk_assessment_result."""

    THAP = "thap"
    TRUNG_BINH = "trung_binh"
    CAO = "cao"
    NGHIEM_TRONG = "nghiem_trong"


class VerificationStatus(str, Enum):
    """Trạng thái xác thực của 1 flag/finding."""

    DA_XAC_THUC = "da_xac_thuc"
    CHUA_XAC_THUC = "chua_xac_thuc"


class EditSource(str, Enum):
    """Nguồn của 1 chỉnh sửa: sửa trực tiếp trên form hay qua chat."""

    UI_FORM = "ui_form"
    CHAT = "chat"


class EditStatus(str, Enum):
    """Trạng thái 1 chỉnh sửa: pending (xanh dương) -> confirmed (xanh lá)."""

    PENDING = "pending"
    CONFIRMED = "confirmed"


class ChatRole(str, Enum):
    """Vai trò người gửi tin nhắn trong khung chat."""

    USER = "user"
    AGENT = "agent"
    STATUS = "status"


class DocumentCategory(str, Enum):
    """Nhóm tài liệu đính kèm do người dùng gắn nhãn khi upload (Màn 1)."""

    SO_DO_SO_HONG = "so_do_so_hong"
    CMND_CCCD = "cmnd_cccd"
    HOP_DONG = "hop_dong"
    ANH_HIEN_TRANG = "anh_hien_trang"
    KHAC = "khac"


class ExtractedDocType(str, Enum):
    """Loại giấy tờ do document classifier tự động nhận diện trên file upload."""

    SO_DO_SO_HONG = "so_do_so_hong"
    TO_KHAI_LPTB = "to_khai_lptb"
    BIEN_BAN_BAN_GIAO = "bien_ban_ban_giao"
    THONG_BAO_THUE_DAT = "thong_bao_thue_dat"
    KHAC = "khac"


class ExtractionFieldStatus(str, Enum):
    """Trạng thái của 1 giá trị trích xuất vào 1 field cụ thể (field_provenance)."""

    DA_XAC_THUC = "da_xac_thuc"
    CAN_XAC_MINH = "can_xac_minh"
    MAU_THUAN = "mau_thuan"
    NHAP_TAY = "nhap_tay"
    SUY_LUAN = "suy_luan"


class LookupCategory(str, Enum):
    """7 nguồn tra cứu của Research Agent."""

    MARKET_PRICE = "market_price"
    PLANNING_ZONING = "planning_zoning"
    LEGAL_STATUS = "legal_status"
    NEIGHBORHOOD_AMENITY = "neighborhood_amenity"
    ENVIRONMENTAL_RISK = "environmental_risk"
    LIQUIDITY_STAT = "liquidity_stat"
    STIGMA_REPUTATION = "stigma_reputation"


class LookupBadge(str, Enum):
    """Badge trạng thái hiển thị trên mỗi lookup-detail card."""

    DA_XAC_THUC = "da_xac_thuc"
    LUU_Y = "luu_y"
    CHUA_XAC_THUC = "chua_xac_thuc"


class ValuationMethodKey(str, Enum):
    """3 phương pháp định giá (Valuation Agent)."""

    SALES_COMPARISON = "sales_comparison"
    HEDONIC_ML = "hedonic_ml"
    COST_APPROACH = "cost_approach"


class ConfidenceFactorKey(str, Enum):
    """5 yếu tố cấu thành độ tin cậy định giá (màn 3)."""

    COMP_QUANTITY_QUALITY = "comp_quantity_quality"
    METHOD_CONSENSUS = "method_consensus"
    LEGAL_PLANNING_COMPLETENESS = "legal_planning_completeness"
    MARKET_VOLATILITY = "market_volatility"
    COMP_SIMILARITY = "comp_similarity"


class RiskGroupKey(str, Enum):
    """5 nhóm rủi ro cấu thành điểm rủi ro tài sản (màn 4)."""

    LEGAL = "legal"
    LIQUIDITY = "liquidity"
    PRICE_VOLATILITY = "price_volatility"
    PHYSICAL_ENVIRONMENT = "physical_environment"
    REPUTATION = "reputation"


def _pg_enum(enum_cls: type[Enum], *, name: str) -> SQLEnum:
    """SQLEnum bound by ``.value`` (not member name) — matches the lowercase DB values
    ``alembic/versions/002_paa_schema.py`` used to ``CREATE TYPE``.
    """
    return SQLEnum(enum_cls, name=name, values_callable=lambda obj: [e.value for e in obj])


def _uuid() -> str:
    """Default factory for UUID-as-string primary keys (matches User/Job/File)."""
    return str(uuid.uuid4())


def _now() -> datetime:
    """Default factory for timezone-aware ``created_at``/``updated_at`` columns."""
    return datetime.now(UTC)


# --------------------------------------------------------------------------- #
# Bảng gốc: 1 hồ sơ thẩm định
# --------------------------------------------------------------------------- #


class AppraisalCase(Base):
    """Hồ sơ thẩm định gốc — 1 dòng = 1 mục "Lịch sử hồ sơ" ở sidebar."""

    __tablename__ = "appraisal_case"
    __table_args__ = (
        CheckConstraint("current_step BETWEEN 1 AND 5", name="ck_appraisal_case_current_step"),
    )

    case_id: Mapped[str] = mapped_column(String, primary_key=True)  # vd. 'REQ-2026-0001'
    status: Mapped[CaseStatus] = mapped_column(
        _pg_enum(CaseStatus, name="case_status"), nullable=False, default=CaseStatus.DANG_XU_LY
    )
    current_step: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    requested_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )


class CaseStepProgress(Base):
    """Trạng thái khoá/mở/xác nhận của từng subtab (1..5)."""

    __tablename__ = "case_step_progress"
    __table_args__ = (
        UniqueConstraint("case_id", "step_number", name="uq_case_step_progress_case_step"),
        CheckConstraint("step_number BETWEEN 1 AND 5", name="ck_case_step_progress_step_number"),
        Index("idx_case_step_progress_case_id", "case_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    step_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[StepStatus] = mapped_column(
        _pg_enum(StepStatus, name="step_status"), nullable=False, default=StepStatus.LOCKED
    )
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# --------------------------------------------------------------------------- #
# Màn 1 — Nhập thông tin
# --------------------------------------------------------------------------- #


class CaseBorrower(Base):
    """A. Thông tin bên vay / chủ sở hữu. User-submitted — NOT seeded synthetically."""

    __tablename__ = "case_borrower"
    __table_args__ = (Index("idx_case_borrower_case_id", "case_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    national_id: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String, nullable=True)
    relationship_to_asset: Mapped[str | None] = mapped_column(String, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )


class PropertyLegalInfo(Base):
    """B. Thông tin pháp lý tài sản (1:1 với appraisal_case)."""

    __tablename__ = "property_legal_info"

    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), primary_key=True
    )
    certificate_type: Mapped[str] = mapped_column(String, nullable=False)
    certificate_number: Mapped[str] = mapped_column(String, nullable=False)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    issuing_authority: Mapped[str | None] = mapped_column(String, nullable=True)
    land_plot_number: Mapped[str | None] = mapped_column(String, nullable=True)
    map_sheet_number: Mapped[str | None] = mapped_column(String, nullable=True)
    land_use_purpose: Mapped[str | None] = mapped_column(String, nullable=True)
    use_term: Mapped[str | None] = mapped_column(String, nullable=True)
    ownership_form: Mapped[str | None] = mapped_column(String, nullable=True)
    current_mortgage_status: Mapped[str | None] = mapped_column(String, nullable=True)


class PropertyPhysicalInfo(Base):
    """C. Vị trí & đặc điểm tài sản (1:1 với appraisal_case)."""

    __tablename__ = "property_physical_info"

    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), primary_key=True
    )
    address: Mapped[str] = mapped_column(String, nullable=False)
    ward: Mapped[str | None] = mapped_column(String, nullable=True)
    district: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    property_type: Mapped[str] = mapped_column(String, nullable=False)
    land_area_sqm: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    floor_area_sqm: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    num_floors_desc: Mapped[str | None] = mapped_column(String, nullable=True)
    frontage_m: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    depth_m: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    construction_year: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    structure_material: Mapped[str | None] = mapped_column(String, nullable=True)
    house_direction: Mapped[str | None] = mapped_column(String, nullable=True)
    road_type_desc: Mapped[str | None] = mapped_column(String, nullable=True)
    alley_width_m: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    current_usage_status: Mapped[str | None] = mapped_column(String, nullable=True)


class LoanInfo(Base):
    """D. Thông tin khoản vay (1:1 với appraisal_case)."""

    __tablename__ = "loan_info"

    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), primary_key=True
    )
    loan_amount_vnd: Mapped[int] = mapped_column(BigInt, nullable=False)
    loan_purpose: Mapped[str | None] = mapped_column(String, nullable=True)
    loan_term_years: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)


class AttachedDocument(Base):
    """Nguồn tài liệu đính kèm (upload) — chỉ hiển thị ở Màn 1. NOT seeded synthetically."""

    __tablename__ = "attached_document"
    __table_args__ = (Index("idx_attached_document_case_id", "case_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    file_size_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doc_category: Mapped[DocumentCategory] = mapped_column(
        _pg_enum(DocumentCategory, name="document_category"),
        nullable=False,
        default=DocumentCategory.KHAC,
    )
    detected_doc_type: Mapped[ExtractedDocType | None] = mapped_column(
        _pg_enum(ExtractedDocType, name="extracted_doc_type"), nullable=True
    )
    is_scan: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ocr_engine: Mapped[str | None] = mapped_column(String, nullable=True)
    page_count: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )


class FieldProvenance(Base):
    """Chống hallucination Màn 1: nguồn gốc từng giá trị auto-fill. NOT seeded synthetically.

    ``target_record_id`` is stored as a plain string (not an FK) because it can
    point at a row in any of several target tables depending on ``target_table``.
    """

    __tablename__ = "field_provenance"
    __table_args__ = (
        CheckConstraint(
            "source_document_id IS NOT NULL OR status IN ('nhap_tay', 'suy_luan')",
            name="ck_field_provenance_source_or_manual",
        ),
        CheckConstraint(
            "confidence_pct IS NULL OR confidence_pct BETWEEN 0 AND 100",
            name="ck_field_provenance_confidence_pct",
        ),
        Index("idx_field_provenance_case_id", "case_id"),
        Index("idx_field_provenance_target", "case_id", "target_table", "target_field"),
        Index("idx_field_provenance_source_document_id", "source_document_id"),
        # Partial unique index: at most 1 "currently selected" value per
        # (case, target table/field/record). Postgres enforces this natively;
        # on SQLite (tests) the ``sqlite_where`` partial clause is honored too
        # (SQLite supports partial indexes since 3.8.0). See
        # ``alembic/versions/002_paa_schema.py`` for the stricter Postgres
        # version that also COALESCEs NULL ``target_record_id``.
        Index(
            "ux_field_provenance_selected",
            "case_id",
            "target_table",
            "target_field",
            "target_record_id",
            unique=True,
            postgresql_where=text("is_selected"),
            sqlite_where=text("is_selected"),
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    source_document_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("attached_document.id", ondelete="SET NULL"), nullable=True
    )
    target_table: Mapped[str] = mapped_column(String, nullable=False)
    target_field: Mapped[str] = mapped_column(String, nullable=False)
    target_record_id: Mapped[str | None] = mapped_column(String, nullable=True)
    extracted_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_page: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    bbox_x: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    bbox_y: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    bbox_width: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    bbox_height: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    confidence_pct: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    status: Mapped[ExtractionFieldStatus] = mapped_column(
        _pg_enum(ExtractionFieldStatus, name="extraction_field_status"),
        nullable=False,
        default=ExtractionFieldStatus.CAN_XAC_MINH,
    )
    is_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )


# --------------------------------------------------------------------------- #
# Màn 2 — Kết quả tra cứu (Research Agent, 7 tool)
# --------------------------------------------------------------------------- #


class MarketComparable(Base):
    """Bảng "Giao dịch so sánh khu vực" (nguồn: market_price_lookup / comparable_sales)."""

    __tablename__ = "market_comparable"
    __table_args__ = (Index("idx_market_comparable_case_id", "case_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    comp_address: Mapped[str] = mapped_column(String, nullable=False)
    distance_km: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    area_sqm: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    transaction_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    price_per_sqm_vnd: Mapped[int] = mapped_column(BigInt, nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class LookupFinding(Base):
    """7 nguồn tra cứu của Research Agent — 1 category = 1 lookup-detail card."""

    __tablename__ = "lookup_finding"
    __table_args__ = (
        UniqueConstraint("case_id", "category", name="uq_lookup_finding_case_category"),
        CheckConstraint(
            "confidence_pct IS NULL OR confidence_pct BETWEEN 0 AND 100",
            name="ck_lookup_finding_confidence_pct",
        ),
        Index("idx_lookup_finding_case_id", "case_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[LookupCategory] = mapped_column(
        _pg_enum(LookupCategory, name="lookup_category"), nullable=False
    )
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    status_badge: Mapped[LookupBadge] = mapped_column(
        _pg_enum(LookupBadge, name="lookup_badge"),
        nullable=False,
        default=LookupBadge.CHUA_XAC_THUC,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    raw_findings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    inference_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_label: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence_pct: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)


# --------------------------------------------------------------------------- #
# Màn 3 — Định giá (Valuation Agent)
# --------------------------------------------------------------------------- #


class ValuationResult(Base):
    """Kết quả định giá tổng hợp (1:1 với appraisal_case)."""

    __tablename__ = "valuation_result"
    __table_args__ = (
        CheckConstraint(
            "confidence_pct BETWEEN 0 AND 100", name="ck_valuation_result_confidence_pct"
        ),
    )

    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), primary_key=True
    )
    proposed_value_vnd: Mapped[int] = mapped_column(BigInt, nullable=False)
    value_range_low_vnd: Mapped[int] = mapped_column(BigInt, nullable=False)
    value_range_high_vnd: Mapped[int] = mapped_column(BigInt, nullable=False)
    price_per_sqm_vnd: Mapped[int | None] = mapped_column(BigInt, nullable=True)
    confidence_pct: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comparable_count: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    price_index_period: Mapped[str | None] = mapped_column(String, nullable=True)
    price_index_value: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    price_index_base: Mapped[float | None] = mapped_column(Numeric(6, 2), default=100)
    confidence_inference_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )


class ValuationPriceIndexPoint(Base):
    """Chuỗi chỉ số giá theo thời gian (sparkline ở màn 3)."""

    __tablename__ = "valuation_price_index_point"
    __table_args__ = (Index("idx_valuation_price_index_point_case_id", "case_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    period_label: Mapped[str] = mapped_column(String, nullable=False)
    index_value: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class ValuationMethod(Base):
    """3 phương pháp định giá + bảng "Quy đổi giá trị đề xuất — trọng số kết hợp"."""

    __tablename__ = "valuation_method"
    __table_args__ = (
        UniqueConstraint("case_id", "method_key", name="uq_valuation_method_case_method"),
        CheckConstraint("weight_pct BETWEEN 0 AND 100", name="ck_valuation_method_weight_pct"),
        Index("idx_valuation_method_case_id", "case_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    method_key: Mapped[ValuationMethodKey] = mapped_column(
        _pg_enum(ValuationMethodKey, name="valuation_method_key"), nullable=False
    )
    estimated_value_vnd: Mapped[int] = mapped_column(BigInt, nullable=False)
    weight_pct: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    contribution_value_vnd: Mapped[int | None] = mapped_column(BigInt, nullable=True)
    method_confidence_pct: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    inputs: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    inference_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_label: Mapped[str | None] = mapped_column(String, nullable=True)


class ValuationConfidenceFactor(Base):
    """5 yếu tố cấu thành độ tin cậy định giá (khối "Cấu thành độ tin cậy tổng")."""

    __tablename__ = "valuation_confidence_factor"
    __table_args__ = (
        UniqueConstraint("case_id", "factor_key", name="uq_valuation_conf_factor_case_factor"),
        CheckConstraint("weight_pct BETWEEN 0 AND 100", name="ck_valuation_conf_factor_weight"),
        CheckConstraint("score BETWEEN 0 AND 100", name="ck_valuation_conf_factor_score"),
        Index("idx_valuation_confidence_factor_case_id", "case_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    factor_key: Mapped[ConfidenceFactorKey] = mapped_column(
        _pg_enum(ConfidenceFactorKey, name="confidence_factor_key"), nullable=False
    )
    label: Mapped[str] = mapped_column(String, nullable=False)
    weight_pct: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False)


# --------------------------------------------------------------------------- #
# Màn 4 — Rủi ro (Risk Assessment Agent)
# --------------------------------------------------------------------------- #


class RiskAssessmentResult(Base):
    """Kết quả chấm điểm rủi ro tổng hợp (1:1 với appraisal_case)."""

    __tablename__ = "risk_assessment_result"
    __table_args__ = (
        CheckConstraint("risk_score BETWEEN 0 AND 100", name="ck_risk_assessment_score"),
        CheckConstraint(
            "ltv_proposed_pct BETWEEN 0 AND 100", name="ck_risk_assessment_ltv_proposed_pct"
        ),
    )

    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), primary_key=True
    )
    risk_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    risk_label: Mapped[SeverityLevel] = mapped_column(
        _pg_enum(SeverityLevel, name="severity_level"), nullable=False
    )
    ltv_proposed_pct: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    risk_inference_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )


class RiskLtvPolicyBand(Base):
    """Cấu hình khung LTV theo điểm rủi ro — dữ liệu tĩnh, dùng chung toàn hệ thống.

    Seeded with the 4 bands from the mockup by the Alembic migration
    (0–20→75%, 21–40→65%, 41–60→55%, >60→45%). Editable via this table without
    a code change.
    """

    __tablename__ = "risk_ltv_policy_band"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    min_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    max_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    max_ltv_pct: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)


class RiskGroup(Base):
    """5 nhóm rủi ro cấu thành (Pháp lý / Thanh khoản / Biến động giá / Vật lý-môi trường / Danh tiếng)."""

    __tablename__ = "risk_group"
    __table_args__ = (
        UniqueConstraint("case_id", "group_key", name="uq_risk_group_case_group"),
        CheckConstraint("weight_pct BETWEEN 0 AND 100", name="ck_risk_group_weight_pct"),
        CheckConstraint("score BETWEEN 0 AND 100", name="ck_risk_group_score"),
        Index("idx_risk_group_case_id", "case_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    group_key: Mapped[RiskGroupKey] = mapped_column(
        _pg_enum(RiskGroupKey, name="risk_group_key"), nullable=False
    )
    label: Mapped[str] = mapped_column(String, nullable=False)
    weight_pct: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    raw_findings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    inference_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_label: Mapped[str | None] = mapped_column(String, nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String, nullable=True)


class RiskFlag(Base):
    """ "Flags cần lưu ý" — danh sách cảnh báo rút gọn hiển thị cuối màn 4."""

    __tablename__ = "risk_flag"
    __table_args__ = (
        CheckConstraint(
            "confidence_pct IS NULL OR confidence_pct BETWEEN 0 AND 100",
            name="ck_risk_flag_confidence_pct",
        ),
        Index("idx_risk_flag_case_id", "case_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    severity: Mapped[SeverityLevel] = mapped_column(
        _pg_enum(SeverityLevel, name="severity_level"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_pct: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    verified_status: Mapped[VerificationStatus] = mapped_column(
        _pg_enum(VerificationStatus, name="verification_status"),
        nullable=False,
        default=VerificationStatus.CHUA_XAC_THUC,
    )
    linked_risk_group: Mapped[str | None] = mapped_column(
        String, ForeignKey("risk_group.id", ondelete="SET NULL"), nullable=True
    )
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


# --------------------------------------------------------------------------- #
# Màn 5 — Dashboard
# --------------------------------------------------------------------------- #


class DashboardStepSummary(Base):
    """ "Tổng hợp theo từng bước" — 4 dòng tóm tắt, mỗi dòng nhảy về đúng subtab."""

    __tablename__ = "dashboard_step_summary"
    __table_args__ = (
        UniqueConstraint("case_id", "step_number", name="uq_dashboard_step_summary_case_step"),
        CheckConstraint(
            "step_number BETWEEN 1 AND 4", name="ck_dashboard_step_summary_step_number"
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    step_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)


class AgentTraceEvent(Base):
    """ "Trace thực thi PAA" — timeline agent trace hiển thị ở tab Dashboard."""

    __tablename__ = "agent_trace_event"
    __table_args__ = (Index("idx_agent_trace_event_case_id", "case_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    seconds_offset: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    actor: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class ExportedReport(Base):
    """Lịch sử các lần "Xuất báo cáo thẩm định"."""

    __tablename__ = "exported_report"
    __table_args__ = (Index("idx_exported_report_case_id", "case_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    format: Mapped[str] = mapped_column(String, nullable=False, default="html")
    generated_by: Mapped[str | None] = mapped_column(String, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )


# --------------------------------------------------------------------------- #
# Dùng chung mọi màn — luồng "sửa qua form/chat -> chờ xác nhận" + lịch sử chat
# --------------------------------------------------------------------------- #


class CaseEditLog(Base):
    """Audit trail cho highlight xanh dương (pending) -> xanh lá (confirmed)."""

    __tablename__ = "case_edit_log"
    __table_args__ = (
        CheckConstraint("step_number BETWEEN 1 AND 5", name="ck_case_edit_log_step_number"),
        Index("idx_case_edit_log_case_id", "case_id"),
        Index("idx_case_edit_log_case_status", "case_id", "status"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    step_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    target_table: Mapped[str] = mapped_column(String, nullable=False)
    target_field: Mapped[str] = mapped_column(String, nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    edit_source: Mapped[EditSource] = mapped_column(
        _pg_enum(EditSource, name="edit_source"), nullable=False
    )
    status: Mapped[EditStatus] = mapped_column(
        _pg_enum(EditStatus, name="edit_status"), nullable=False, default=EditStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ChatMessage(Base):
    """Toàn bộ tin nhắn trong khung chat — phục vụ replay hội thoại + audit."""

    __tablename__ = "chat_message"
    __table_args__ = (Index("idx_chat_message_case_id", "case_id", "created_at"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("appraisal_case.case_id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[ChatRole] = mapped_column(_pg_enum(ChatRole, name="chat_role"), nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    related_edit_log_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("case_edit_log.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
