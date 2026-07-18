"""Canonical field registry, normalizers, thresholds and lightweight routing.

The registry is the single source of truth for which form fields exist, how they
map to the "Nhập thông tin" sections (A/B/C/D) and to the PostgreSQL Màn-1 tables
(for the future persistence PR). Normalizers convert verbatim extracted text into
display-consistent values (dates, areas) — done in code, not by the LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from shb.ai.plugins.property_intake.schema import DocType

# Confidence tiers driving auto-fill vs review (feature #9).
CONF_HIGH = 0.85  # >= -> da_xac_thuc (auto-filled)
CONF_MID = 0.60  # >= -> can_xac_minh; below -> treated as low / manual


@dataclass(frozen=True)
class CanonicalFieldSpec:
    """Definition of one canonical form field."""

    key: str
    section: str  # 'A' | 'B' | 'C' | 'D'
    label: str
    target_table: str  # PostgreSQL table (persistence PR)
    target_field: str  # PostgreSQL column


# Order here is the display order on the form.
CANONICAL_FIELDS: list[CanonicalFieldSpec] = [
    # A. Bên vay / chủ sở hữu
    CanonicalFieldSpec("owner_full_name", "A", "Họ và tên", "case_borrower", "full_name"),
    CanonicalFieldSpec("owner_national_id", "A", "Số CMND/CCCD", "case_borrower", "national_id"),
    CanonicalFieldSpec("owner_phone", "A", "Số điện thoại", "case_borrower", "phone_number"),
    CanonicalFieldSpec(
        "relationship_to_asset",
        "A",
        "Mối quan hệ với tài sản",
        "case_borrower",
        "relationship_to_asset",
    ),
    # B. Pháp lý tài sản
    CanonicalFieldSpec(
        "certificate_type",
        "B",
        "Loại giấy chứng nhận",
        "property_legal_info",
        "certificate_type",
    ),
    CanonicalFieldSpec(
        "certificate_number",
        "B",
        "Số giấy chứng nhận",
        "property_legal_info",
        "certificate_number",
    ),
    CanonicalFieldSpec("issue_date", "B", "Ngày cấp", "property_legal_info", "issue_date"),
    CanonicalFieldSpec(
        "issuing_authority", "B", "Cơ quan cấp", "property_legal_info", "issuing_authority"
    ),
    CanonicalFieldSpec(
        "land_plot_number", "B", "Số thửa", "property_legal_info", "land_plot_number"
    ),
    CanonicalFieldSpec(
        "map_sheet_number", "B", "Số tờ bản đồ", "property_legal_info", "map_sheet_number"
    ),
    CanonicalFieldSpec(
        "land_use_purpose",
        "B",
        "Mục đích sử dụng đất",
        "property_legal_info",
        "land_use_purpose",
    ),
    CanonicalFieldSpec("use_term", "B", "Thời hạn sử dụng", "property_legal_info", "use_term"),
    CanonicalFieldSpec(
        "ownership_form", "B", "Hình thức sở hữu", "property_legal_info", "ownership_form"
    ),
    CanonicalFieldSpec(
        "current_mortgage_status",
        "B",
        "Tình trạng thế chấp hiện tại",
        "property_legal_info",
        "current_mortgage_status",
    ),
    # C. Vị trí & đặc điểm
    CanonicalFieldSpec("address", "C", "Địa chỉ", "property_physical_info", "address"),
    CanonicalFieldSpec("property_type", "C", "Loại BĐS", "property_physical_info", "property_type"),
    CanonicalFieldSpec(
        "land_area_sqm", "C", "Diện tích đất", "property_physical_info", "land_area_sqm"
    ),
    CanonicalFieldSpec(
        "floor_area_sqm",
        "C",
        "Diện tích sàn xây dựng",
        "property_physical_info",
        "floor_area_sqm",
    ),
    CanonicalFieldSpec(
        "num_floors_desc", "C", "Số tầng", "property_physical_info", "num_floors_desc"
    ),
    CanonicalFieldSpec(
        "construction_year", "C", "Năm xây dựng", "property_physical_info", "construction_year"
    ),
    CanonicalFieldSpec(
        "structure_material",
        "C",
        "Kết cấu / vật liệu",
        "property_physical_info",
        "structure_material",
    ),
    CanonicalFieldSpec(
        "house_direction", "C", "Hướng nhà", "property_physical_info", "house_direction"
    ),
    CanonicalFieldSpec(
        "road_type_desc",
        "C",
        "Loại đường / độ rộng hẻm",
        "property_physical_info",
        "road_type_desc",
    ),
    CanonicalFieldSpec(
        "current_usage_status",
        "C",
        "Tình trạng sử dụng hiện tại",
        "property_physical_info",
        "current_usage_status",
    ),
    # D. Khoản vay (không có trong tài liệu tài sản -> nhập tay)
    CanonicalFieldSpec("loan_amount_vnd", "D", "Số tiền vay", "loan_info", "loan_amount_vnd"),
    CanonicalFieldSpec("loan_purpose", "D", "Mục đích vay", "loan_info", "loan_purpose"),
    CanonicalFieldSpec("loan_term_years", "D", "Thời hạn vay", "loan_info", "loan_term_years"),
]

CANONICAL_KEYS = [f.key for f in CANONICAL_FIELDS]
FIELD_SPEC_BY_KEY = {f.key: f for f in CANONICAL_FIELDS}


# --------------------------------------------------------------------------- #
# Normalizers (code, not LLM) — verbatim text -> display-consistent value
# --------------------------------------------------------------------------- #
def normalize_area(value: str) -> str:
    """Normalize an area to ``<number> m²`` while keeping the original number."""
    match = re.search(r"[\d.,]+", value)
    if not match:
        return value.strip()
    return f"{match.group(0).strip()} m²"


def normalize_date(value: str) -> str:
    """Normalize a date to ``dd/mm/yyyy`` when clearly parseable, else trim."""
    m = re.search(r"(\d{1,2})\D+(\d{1,2})\D+(\d{4})", value)
    if m:
        d, mo, y = m.groups()
        return f"{int(d):02d}/{int(mo):02d}/{y}"
    return value.strip()


# canonical key -> normalizer
NORMALIZERS = {
    "land_area_sqm": normalize_area,
    "floor_area_sqm": normalize_area,
    "issue_date": normalize_date,
}


def normalize_value(key: str, value: str) -> str:
    """Apply the registered normalizer for ``key`` (trim by default)."""
    fn = NORMALIZERS.get(key)
    return fn(value) if fn else value.strip()


# --------------------------------------------------------------------------- #
# Lightweight keyword classifier (PR2 stub; PR3 replaces with an LLM classifier)
# --------------------------------------------------------------------------- #
_DOC_KEYWORDS: list[tuple[DocType, tuple[str, ...]]] = [
    (
        DocType.SO_DO_SO_HONG,
        ("giấy chứng nhận quyền sử dụng đất", "sổ hồng", "sổ đỏ", "quyền sở hữu nhà"),
    ),
    (DocType.TO_KHAI_LPTB, ("tờ khai lệ phí trước bạ", "lệ phí trước bạ")),
    (DocType.BIEN_BAN_BAN_GIAO, ("biên bản bàn giao",)),
    (DocType.THONG_BAO_THUE_DAT, ("thông báo nộp thuế", "thuế sử dụng đất", "thuế đất")),
]


def classify_by_keywords(text: str) -> DocType:
    """Best-effort document classification by keyword (case-insensitive).

    Returns :attr:`DocType.KHAC` when no keyword matches.
    """
    lowered = text.lower()
    for doc_type, keywords in _DOC_KEYWORDS:
        if any(kw in lowered for kw in keywords):
            return doc_type
    return DocType.KHAC
