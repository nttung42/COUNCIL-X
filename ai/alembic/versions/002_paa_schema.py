"""PAA (Property Appraisal Agent) domain schema.

Adds every table backing the 5 mockup screens (Nhập thông tin / Kết quả tra
cứu / Định giá / Rủi ro / Dashboard) on top of the platform tables from
``001_initial_schema``. Column-for-column port of ``PAA_Schema_PostgreSQL.sql``
(validated standalone against Postgres 16), adapted to this project's ORM at
``shb/db/models_paa.py`` — keep the two in sync when editing either.

Notes specific to this migration (see ``models_paa.py`` module docstring for
the full rationale):

* Enum types are created explicitly up front (``checkfirst=True``) and then
  referenced with ``create_type=False`` in every column, because
  ``severity_level`` is used by two tables (``risk_assessment_result``,
  ``risk_flag``) — inline ``sa.Enum(...)`` per-column would try to
  ``CREATE TYPE`` twice and fail on the second table.
* This migration targets Postgres only (``alembic/env.py`` always resolves a
  Postgres ``DATABASE_URL``); the ORM models in ``models_paa.py`` use the
  dialect-generic ``sa.Enum``/``sa.JSON`` so the *same* model classes also
  work against the SQLite engine ``tests/conftest.py`` spins up via
  ``Base.metadata.create_all`` — that path does not go through this file.
* The Postgres-only trigger (``touch_case_updated_at``) and views
  (``v_case_history``, ``v_dashboard_kpi``) from the standalone DDL are
  intentionally not created here; they are reimplemented as portable query
  functions in ``shb/capabilities/dashboard/queries.py``.

Revision ID: 002
Revises: 001
Create Date: 2026-07-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --------------------------------------------------------------------------- #
# Enum type definitions — name -> ordered values (matches models_paa.py 1:1)
# --------------------------------------------------------------------------- #

ENUM_DEFS: dict[str, tuple[str, ...]] = {
    "case_status": ("dang_xu_ly", "hoan_tat", "huy"),
    "step_status": ("locked", "unlocked", "confirmed"),
    "severity_level": ("thap", "trung_binh", "cao", "nghiem_trong"),
    "verification_status": ("da_xac_thuc", "chua_xac_thuc"),
    "edit_source": ("ui_form", "chat"),
    "edit_status": ("pending", "confirmed"),
    "chat_role": ("user", "agent", "status"),
    "document_category": ("so_do_so_hong", "cmnd_cccd", "hop_dong", "anh_hien_trang", "khac"),
    "extracted_doc_type": (
        "so_do_so_hong",
        "to_khai_lptb",
        "bien_ban_ban_giao",
        "thong_bao_thue_dat",
        "khac",
    ),
    "extraction_field_status": (
        "da_xac_thuc",
        "can_xac_minh",
        "mau_thuan",
        "nhap_tay",
        "suy_luan",
    ),
    "lookup_category": (
        "market_price",
        "planning_zoning",
        "legal_status",
        "neighborhood_amenity",
        "environmental_risk",
        "liquidity_stat",
        "stigma_reputation",
    ),
    "lookup_badge": ("da_xac_thuc", "luu_y", "chua_xac_thuc"),
    "valuation_method_key": ("sales_comparison", "hedonic_ml", "cost_approach"),
    "confidence_factor_key": (
        "comp_quantity_quality",
        "method_consensus",
        "legal_planning_completeness",
        "market_volatility",
        "comp_similarity",
    ),
    "risk_group_key": (
        "legal",
        "liquidity",
        "price_volatility",
        "physical_environment",
        "reputation",
    ),
}


def _enum(name: str) -> postgresql.ENUM:
    """Reference an already-created enum type in a column (no CREATE TYPE emitted)."""
    return postgresql.ENUM(*ENUM_DEFS[name], name=name, create_type=False)


def upgrade() -> None:
    """Create the full PAA schema: enum types, tables, indexes, seed data."""
    bind = op.get_bind()
    for name, values in ENUM_DEFS.items():
        postgresql.ENUM(*values, name=name).create(bind, checkfirst=True)

    # --- Bảng gốc -------------------------------------------------------- #
    op.create_table(
        "appraisal_case",
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("status", _enum("case_status"), nullable=False, server_default="dang_xu_ly"),
        sa.Column("current_step", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("requested_by", sa.String(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("current_step BETWEEN 1 AND 5", name="ck_appraisal_case_current_step"),
        sa.PrimaryKeyConstraint("case_id"),
    )

    op.create_table(
        "case_step_progress",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("step_number", sa.SmallInteger(), nullable=False),
        sa.Column("status", _enum("step_status"), nullable=False, server_default="locked"),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("step_number BETWEEN 1 AND 5", name="ck_case_step_progress_step_number"),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "step_number", name="uq_case_step_progress_case_step"),
    )
    op.create_index("idx_case_step_progress_case_id", "case_step_progress", ["case_id"])

    # --- Màn 1 — Nhập thông tin ------------------------------------------ #
    op.create_table(
        "case_borrower",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("national_id", sa.String(), nullable=False),
        sa.Column("phone_number", sa.String(), nullable=True),
        sa.Column("relationship_to_asset", sa.String(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_case_borrower_case_id", "case_borrower", ["case_id"])

    op.create_table(
        "property_legal_info",
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("certificate_type", sa.String(), nullable=False),
        sa.Column("certificate_number", sa.String(), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("issuing_authority", sa.String(), nullable=True),
        sa.Column("land_plot_number", sa.String(), nullable=True),
        sa.Column("map_sheet_number", sa.String(), nullable=True),
        sa.Column("land_use_purpose", sa.String(), nullable=True),
        sa.Column("use_term", sa.String(), nullable=True),
        sa.Column("ownership_form", sa.String(), nullable=True),
        sa.Column("current_mortgage_status", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("case_id"),
    )

    op.create_table(
        "property_physical_info",
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("ward", sa.String(), nullable=True),
        sa.Column("district", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("property_type", sa.String(), nullable=False),
        sa.Column("land_area_sqm", sa.Numeric(8, 2), nullable=False),
        sa.Column("floor_area_sqm", sa.Numeric(8, 2), nullable=True),
        sa.Column("num_floors_desc", sa.String(), nullable=True),
        sa.Column("frontage_m", sa.Numeric(5, 2), nullable=True),
        sa.Column("depth_m", sa.Numeric(5, 2), nullable=True),
        sa.Column("construction_year", sa.SmallInteger(), nullable=True),
        sa.Column("structure_material", sa.String(), nullable=True),
        sa.Column("house_direction", sa.String(), nullable=True),
        sa.Column("road_type_desc", sa.String(), nullable=True),
        sa.Column("alley_width_m", sa.Numeric(4, 2), nullable=True),
        sa.Column("current_usage_status", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("case_id"),
    )

    op.create_table(
        "loan_info",
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("loan_amount_vnd", sa.BigInteger(), nullable=False),
        sa.Column("loan_purpose", sa.String(), nullable=True),
        sa.Column("loan_term_years", sa.SmallInteger(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("case_id"),
    )

    op.create_table(
        "attached_document",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("file_size_kb", sa.Integer(), nullable=True),
        sa.Column(
            "doc_category", _enum("document_category"), nullable=False, server_default="khac"
        ),
        sa.Column("detected_doc_type", _enum("extracted_doc_type"), nullable=True),
        sa.Column("is_scan", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ocr_engine", sa.String(), nullable=True),
        sa.Column("page_count", sa.SmallInteger(), nullable=True),
        sa.Column(
            "uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_attached_document_case_id", "attached_document", ["case_id"])

    op.create_table(
        "field_provenance",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("source_document_id", sa.String(), nullable=True),
        sa.Column("target_table", sa.String(), nullable=False),
        sa.Column("target_field", sa.String(), nullable=False),
        sa.Column("target_record_id", sa.String(), nullable=True),
        sa.Column("extracted_value", sa.Text(), nullable=True),
        sa.Column("source_snippet", sa.Text(), nullable=True),
        sa.Column("source_page", sa.SmallInteger(), nullable=True),
        sa.Column("bbox_x", sa.Numeric(6, 4), nullable=True),
        sa.Column("bbox_y", sa.Numeric(6, 4), nullable=True),
        sa.Column("bbox_width", sa.Numeric(6, 4), nullable=True),
        sa.Column("bbox_height", sa.Numeric(6, 4), nullable=True),
        sa.Column("confidence_pct", sa.SmallInteger(), nullable=True),
        sa.Column(
            "status",
            _enum("extraction_field_status"),
            nullable=False,
            server_default="can_xac_minh",
        ),
        sa.Column("is_selected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "confidence_pct IS NULL OR confidence_pct BETWEEN 0 AND 100",
            name="ck_field_provenance_confidence_pct",
        ),
        sa.CheckConstraint(
            "source_document_id IS NOT NULL OR status IN ('nhap_tay', 'suy_luan')",
            name="ck_field_provenance_source_or_manual",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_document_id"], ["attached_document.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_field_provenance_case_id", "field_provenance", ["case_id"])
    op.create_index(
        "idx_field_provenance_target", "field_provenance", ["case_id", "target_table", "target_field"]
    )
    op.create_index(
        "idx_field_provenance_source_document_id", "field_provenance", ["source_document_id"]
    )
    # Partial unique index (Postgres-only, with COALESCE so multiple NULL
    # target_record_id rows for the same field are still mutually exclusive) —
    # at most 1 "currently selected" value per (case, target table/field/record).
    op.execute(
        """
        CREATE UNIQUE INDEX ux_field_provenance_selected ON field_provenance (
          case_id, target_table, target_field,
          COALESCE(target_record_id, '00000000-0000-0000-0000-000000000000')
        ) WHERE is_selected
        """
    )

    # --- Màn 2 — Kết quả tra cứu ------------------------------------------ #
    op.create_table(
        "market_comparable",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("comp_address", sa.String(), nullable=False),
        sa.Column("distance_km", sa.Numeric(4, 2), nullable=True),
        sa.Column("area_sqm", sa.Numeric(8, 2), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=True),
        sa.Column("price_per_sqm_vnd", sa.BigInteger(), nullable=False),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_market_comparable_case_id", "market_comparable", ["case_id"])

    op.create_table(
        "lookup_finding",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("category", _enum("lookup_category"), nullable=False),
        sa.Column("tool_name", sa.String(), nullable=False),
        sa.Column(
            "status_badge", _enum("lookup_badge"), nullable=False, server_default="chua_xac_thuc"
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("raw_findings", sa.JSON(), nullable=False),
        sa.Column("inference_text", sa.Text(), nullable=True),
        sa.Column("source_label", sa.String(), nullable=True),
        sa.Column("confidence_pct", sa.SmallInteger(), nullable=True),
        sa.CheckConstraint(
            "confidence_pct IS NULL OR confidence_pct BETWEEN 0 AND 100",
            name="ck_lookup_finding_confidence_pct",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "category", name="uq_lookup_finding_case_category"),
    )
    op.create_index("idx_lookup_finding_case_id", "lookup_finding", ["case_id"])

    # --- Màn 3 — Định giá --------------------------------------------------- #
    op.create_table(
        "valuation_result",
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("proposed_value_vnd", sa.BigInteger(), nullable=False),
        sa.Column("value_range_low_vnd", sa.BigInteger(), nullable=False),
        sa.Column("value_range_high_vnd", sa.BigInteger(), nullable=False),
        sa.Column("price_per_sqm_vnd", sa.BigInteger(), nullable=True),
        sa.Column("confidence_pct", sa.SmallInteger(), nullable=False),
        sa.Column("comparable_count", sa.SmallInteger(), nullable=True),
        sa.Column("price_index_period", sa.String(), nullable=True),
        sa.Column("price_index_value", sa.Numeric(6, 2), nullable=True),
        sa.Column("price_index_base", sa.Numeric(6, 2), server_default="100"),
        sa.Column("confidence_inference_text", sa.Text(), nullable=True),
        sa.Column(
            "computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "confidence_pct BETWEEN 0 AND 100", name="ck_valuation_result_confidence_pct"
        ),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("case_id"),
    )

    op.create_table(
        "valuation_price_index_point",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("period_label", sa.String(), nullable=False),
        sa.Column("index_value", sa.Numeric(6, 2), nullable=False),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_valuation_price_index_point_case_id", "valuation_price_index_point", ["case_id"]
    )

    op.create_table(
        "valuation_method",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("method_key", _enum("valuation_method_key"), nullable=False),
        sa.Column("estimated_value_vnd", sa.BigInteger(), nullable=False),
        sa.Column("weight_pct", sa.SmallInteger(), nullable=False),
        sa.Column("contribution_value_vnd", sa.BigInteger(), nullable=True),
        sa.Column("method_confidence_pct", sa.SmallInteger(), nullable=True),
        sa.Column("inputs", sa.JSON(), nullable=False),
        sa.Column("inference_text", sa.Text(), nullable=True),
        sa.Column("source_label", sa.String(), nullable=True),
        sa.CheckConstraint("weight_pct BETWEEN 0 AND 100", name="ck_valuation_method_weight_pct"),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "method_key", name="uq_valuation_method_case_method"),
    )
    op.create_index("idx_valuation_method_case_id", "valuation_method", ["case_id"])

    op.create_table(
        "valuation_confidence_factor",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("factor_key", _enum("confidence_factor_key"), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("weight_pct", sa.SmallInteger(), nullable=False),
        sa.Column("score", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("weight_pct BETWEEN 0 AND 100", name="ck_valuation_conf_factor_weight"),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name="ck_valuation_conf_factor_score"),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "factor_key", name="uq_valuation_conf_factor_case_factor"),
    )
    op.create_index(
        "idx_valuation_confidence_factor_case_id", "valuation_confidence_factor", ["case_id"]
    )

    # --- Màn 4 — Rủi ro ------------------------------------------------------ #
    op.create_table(
        "risk_assessment_result",
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("risk_score", sa.SmallInteger(), nullable=False),
        sa.Column("risk_label", _enum("severity_level"), nullable=False),
        sa.Column("ltv_proposed_pct", sa.SmallInteger(), nullable=False),
        sa.Column("risk_inference_text", sa.Text(), nullable=True),
        sa.Column(
            "computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("risk_score BETWEEN 0 AND 100", name="ck_risk_assessment_score"),
        sa.CheckConstraint(
            "ltv_proposed_pct BETWEEN 0 AND 100", name="ck_risk_assessment_ltv_proposed_pct"
        ),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("case_id"),
    )

    op.create_table(
        "risk_ltv_policy_band",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("min_score", sa.SmallInteger(), nullable=False),
        sa.Column("max_score", sa.SmallInteger(), nullable=True),
        sa.Column("max_ltv_pct", sa.SmallInteger(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.bulk_insert(
        sa.table(
            "risk_ltv_policy_band",
            sa.column("id", sa.SmallInteger()),
            sa.column("min_score", sa.SmallInteger()),
            sa.column("max_score", sa.SmallInteger()),
            sa.column("max_ltv_pct", sa.SmallInteger()),
            sa.column("label", sa.String()),
        ),
        [
            {"id": 1, "min_score": 0, "max_score": 20, "max_ltv_pct": 75,
             "label": "0–20 điểm → tối đa 75%"},
            {"id": 2, "min_score": 21, "max_score": 40, "max_ltv_pct": 65,
             "label": "21–40 điểm → tối đa 65%"},
            {"id": 3, "min_score": 41, "max_score": 60, "max_ltv_pct": 55,
             "label": "41–60 điểm → tối đa 55%"},
            {"id": 4, "min_score": 61, "max_score": None, "max_ltv_pct": 45,
             "label": ">60 điểm → tối đa 45% hoặc cần thẩm định lại"},
        ],
    )

    op.create_table(
        "risk_group",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("group_key", _enum("risk_group_key"), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("weight_pct", sa.SmallInteger(), nullable=False),
        sa.Column("score", sa.SmallInteger(), nullable=False),
        sa.Column("raw_findings", sa.JSON(), nullable=False),
        sa.Column("inference_text", sa.Text(), nullable=True),
        sa.Column("source_label", sa.String(), nullable=True),
        sa.Column("tool_name", sa.String(), nullable=True),
        sa.CheckConstraint("weight_pct BETWEEN 0 AND 100", name="ck_risk_group_weight_pct"),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name="ck_risk_group_score"),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "group_key", name="uq_risk_group_case_group"),
    )
    op.create_index("idx_risk_group_case_id", "risk_group", ["case_id"])

    op.create_table(
        "risk_flag",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("severity", _enum("severity_level"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("confidence_pct", sa.SmallInteger(), nullable=True),
        sa.Column(
            "verified_status",
            _enum("verification_status"),
            nullable=False,
            server_default="chua_xac_thuc",
        ),
        sa.Column("linked_risk_group", sa.String(), nullable=True),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.CheckConstraint(
            "confidence_pct IS NULL OR confidence_pct BETWEEN 0 AND 100",
            name="ck_risk_flag_confidence_pct",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["linked_risk_group"], ["risk_group.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_risk_flag_case_id", "risk_flag", ["case_id"])

    # --- Màn 5 — Dashboard --------------------------------------------------- #
    op.create_table(
        "dashboard_step_summary",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("step_number", sa.SmallInteger(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "step_number BETWEEN 1 AND 4", name="ck_dashboard_step_summary_step_number"
        ),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "step_number", name="uq_dashboard_step_summary_case_step"),
    )

    op.create_table(
        "agent_trace_event",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("seconds_offset", sa.Numeric(6, 2), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_agent_trace_event_case_id", "agent_trace_event", ["case_id"])

    op.create_table(
        "exported_report",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("format", sa.String(), nullable=False, server_default="html"),
        sa.Column("generated_by", sa.String(), nullable=True),
        sa.Column(
            "generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_exported_report_case_id", "exported_report", ["case_id"])

    # --- Dùng chung mọi màn --------------------------------------------------- #
    op.create_table(
        "case_edit_log",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("step_number", sa.SmallInteger(), nullable=False),
        sa.Column("target_table", sa.String(), nullable=False),
        sa.Column("target_field", sa.String(), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("edit_source", _enum("edit_source"), nullable=False),
        sa.Column("status", _enum("edit_status"), nullable=False, server_default="pending"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("step_number BETWEEN 1 AND 5", name="ck_case_edit_log_step_number"),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_case_edit_log_case_id", "case_edit_log", ["case_id"])
    op.create_index("idx_case_edit_log_case_status", "case_edit_log", ["case_id", "status"])

    op.create_table(
        "chat_message",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("role", _enum("chat_role"), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("related_edit_log_id", sa.String(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["case_id"], ["appraisal_case.case_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["related_edit_log_id"], ["case_edit_log.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_chat_message_case_id", "chat_message", ["case_id", "created_at"])


def downgrade() -> None:
    """Drop the full PAA schema in FK-safe reverse order, then the enum types."""
    op.drop_table("chat_message")
    op.drop_table("case_edit_log")
    op.drop_table("exported_report")
    op.drop_table("agent_trace_event")
    op.drop_table("dashboard_step_summary")
    op.drop_table("risk_flag")
    op.drop_table("risk_group")
    op.drop_table("risk_ltv_policy_band")
    op.drop_table("risk_assessment_result")
    op.drop_table("valuation_confidence_factor")
    op.drop_table("valuation_method")
    op.drop_table("valuation_price_index_point")
    op.drop_table("valuation_result")
    op.drop_table("lookup_finding")
    op.drop_table("market_comparable")
    op.execute("DROP INDEX IF EXISTS ux_field_provenance_selected")
    op.drop_table("field_provenance")
    op.drop_table("attached_document")
    op.drop_table("loan_info")
    op.drop_table("property_physical_info")
    op.drop_table("property_legal_info")
    op.drop_table("case_borrower")
    op.drop_table("case_step_progress")
    op.drop_table("appraisal_case")

    bind = op.get_bind()
    for name, values in ENUM_DEFS.items():
        postgresql.ENUM(*values, name=name).drop(bind, checkfirst=True)
