"""Canonical field registry, normalizers, thresholds and lightweight routing.

The registry is the single source of truth for which form fields exist, how they
map to the "Nhập thông tin" sections (A/B/C/D) and to the PostgreSQL Màn-1 tables
(for the future persistence PR). Normalizers convert verbatim extracted text into
display-consistent values (dates, areas) — done in code, not by the LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from shb.ai.plugins.property_intake.schema import DocType, FieldStatus, FieldValue

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
    CanonicalFieldSpec("frontage_m", "C", "Mặt tiền (m)", "property_physical_info", "frontage_m"),
    CanonicalFieldSpec("depth_m", "C", "Chiều sâu (m)", "property_physical_info", "depth_m"),
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
        "alley_width_m", "C", "Độ rộng hẻm (m)", "property_physical_info", "alley_width_m"
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
# Normalizers (code, not LLM) — verbatim text -> typed canonical value
# --------------------------------------------------------------------------- #
# The LLM returns values *verbatim*; these functions convert them to the typed
# form the persistence layer will store (money → bigint VND, area → numeric m²,
# date → ISO date). They return ``None`` when the text cannot be parsed so the
# caller keeps the verbatim value without inventing a number.

_MULTIPLIERS: list[tuple[str, int]] = [
    ("tỷ", 1_000_000_000),
    ("tỉ", 1_000_000_000),
    ("triệu", 1_000_000),
    ("nghìn", 1_000),
    ("ngàn", 1_000),
]


def normalize_numeric(value: str) -> float | None:
    """Parse the first number in ``value`` to ``float`` (VN or EN notation).

    Handles ``62`` -> 62.0, ``62,5`` -> 62.5, ``1.234`` -> 1234.0,
    ``1.234,5`` -> 1234.5. Returns ``None`` when no number is present.
    """
    match = re.search(r"\d[\d.,]*", value)
    if not match:
        return None
    num = match.group(0).rstrip(".,")
    has_dot, has_comma = "." in num, "," in num
    if has_dot and has_comma:
        # VN grouped: '.' thousands, ',' decimal.
        num = num.replace(".", "").replace(",", ".")
    elif has_comma:
        num = num.replace(",", ".")
    elif has_dot and re.fullmatch(r"\d{1,3}(\.\d{3})+", num):
        # '.' used purely as a thousands separator.
        num = num.replace(".", "")
    try:
        return float(num)
    except ValueError:  # pragma: no cover - defensive
        return None


def normalize_money(value: str) -> int | None:
    """Parse a Vietnamese money expression to an integer amount in VND.

    Handles ``1.500.000.000 đồng`` -> 1500000000 and ``1,5 tỷ`` -> 1500000000.
    Returns ``None`` when no number is present.
    """
    low = value.lower()
    multiplier = 1
    for word, factor in _MULTIPLIERS:
        if word in low:
            multiplier = factor
            break
    num = normalize_numeric(value)
    if num is None:
        return None
    return int(round(num * multiplier))


def normalize_date(value: str) -> str | None:
    """Normalize a date to ISO ``YYYY-MM-DD``; return ``None`` if unparseable."""
    m = re.search(r"(\d{1,2})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{4})", value)
    if not m:
        m = re.search(
            r"ngày\s*(\d{1,2}).*?tháng\s*(\d{1,2}).*?năm\s*(\d{4})",
            value,
            re.IGNORECASE | re.DOTALL,
        )
    if not m:
        return None
    day, month, year = (int(g) for g in m.groups())
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def normalize_int(value: str) -> int | None:
    """Parse the first integer in ``value`` (e.g. year, term) to ``int``."""
    num = normalize_numeric(value)
    return int(num) if num is not None else None


# canonical key -> normalizer producing a typed value (matches DB column types)
MONEY_KEYS = {"loan_amount_vnd"}  # -> BIGINT
NUMERIC_KEYS = {  # -> NUMERIC
    "land_area_sqm",
    "floor_area_sqm",
    "frontage_m",
    "depth_m",
    "alley_width_m",
}
INT_KEYS = {"construction_year", "loan_term_years"}  # -> SMALLINT
DATE_KEYS = {"issue_date"}  # -> DATE (ISO string)


def normalize_field(key: str, value: str) -> int | float | str | None:
    """Return the typed normalized value for ``key``, or ``None`` if not applicable."""
    if key in MONEY_KEYS:
        return normalize_money(value)
    if key in NUMERIC_KEYS:
        return normalize_numeric(value)
    if key in INT_KEYS:
        return normalize_int(value)
    if key in DATE_KEYS:
        return normalize_date(value)
    return None


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


# --------------------------------------------------------------------------- #
# Cross-document merge — source priority + conflict detection (PR4)
# --------------------------------------------------------------------------- #
# When two documents disagree on a field, the value from the more authoritative
# source wins. Order: Sổ đỏ/hồng (GCN) > Thông báo thuế đất > Tờ khai LPTB >
# Biên bản bàn giao. Unknown / unclassified documents have the lowest priority.
SOURCE_PRIORITY: dict[DocType, int] = {
    DocType.SO_DO_SO_HONG: 4,
    DocType.THONG_BAO_THUE_DAT: 3,
    DocType.TO_KHAI_LPTB: 2,
    DocType.BIEN_BAN_BAN_GIAO: 1,
    DocType.KHAC: 0,
}

# Two numeric values agree when their relative difference is within this band.
NUMERIC_CONFLICT_TOL = 0.05
# Each corroborating source nudges confidence up by this much (capped at 0.99).
CORROBORATION_BONUS = 0.05
# A value the verifier rejects has its confidence capped to this ceiling (#5).
VERIFIER_FAIL_CONF_CAP = 0.40


def source_priority(fv: FieldValue) -> int:
    """Return the merge priority of a value based on its source document type."""
    if fv.source_doc_type is None:
        return 0
    return SOURCE_PRIORITY.get(fv.source_doc_type, 0)


def _norm_text(value: str | None) -> str:
    """Casefold + collapse whitespace for lenient text comparison."""
    return " ".join((value or "").casefold().split())


def values_agree(a: FieldValue, b: FieldValue) -> bool:
    """Return True when two candidate values are equivalent.

    Numeric values agree within :data:`NUMERIC_CONFLICT_TOL`; typed non-numeric
    normalized values (e.g. ISO dates) must be equal; otherwise the verbatim text
    is compared leniently (casefold + whitespace).
    """
    na, nb = a.normalized, b.normalized
    if isinstance(na, (int, float)) and isinstance(nb, (int, float)):
        scale = max(abs(na), abs(nb))
        if scale == 0:
            return True
        return abs(na - nb) / scale <= NUMERIC_CONFLICT_TOL
    if na is not None and nb is not None:
        return str(na) == str(nb)
    return _norm_text(a.value) == _norm_text(b.value)


# --------------------------------------------------------------------------- #
# Confidence tiering (#9) — decide the final cell status
# --------------------------------------------------------------------------- #
def tier_status(fv: FieldValue) -> FieldStatus:
    """Decide a field's final :class:`FieldStatus` from all available signals.

    Terminal statuses (``mau_thuan`` from merge, ``suy_luan`` for inferred values)
    are preserved. A missing value stays ``nhap_tay``. Otherwise a failed verifier
    or any validation flag forces ``can_xac_minh``; only a grounded, verified,
    high-confidence value is auto-filled as ``da_xac_thuc``.
    """
    if fv.status in (FieldStatus.MAU_THUAN, FieldStatus.SUY_LUAN):
        return fv.status
    if not fv.value:
        return FieldStatus.NHAP_TAY
    if fv.verifier_passed is False:
        return FieldStatus.CAN_XAC_MINH
    if fv.validation_flags:
        return FieldStatus.CAN_XAC_MINH
    if fv.confidence >= CONF_HIGH:
        return FieldStatus.DA_XAC_THUC
    return FieldStatus.CAN_XAC_MINH
