"""Rule + arithmetic cross-check validators (feature 4).

Pure functions over the merged canonical field map. Each validator inspects the
fields it cares about and returns :class:`ValidationIssue` entries; the validate
node attaches their messages to the offending field's ``validation_flags`` so
tiering downgrades it to *cần xác minh*.

The checks are intentionally *soft* (they flag, never delete): banking review
keeps the value visible but marks it for a human. New cross-checks (e.g.
mặt tiền × chiều sâu ≈ diện tích, once those fields are extracted) plug in by
appending to :data:`VALIDATORS`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from shb.ai.plugins.property_intake.schema import FieldValue

# A plausible span for building years and certificate dates.
YEAR_MIN = 1900
YEAR_MAX = 2035
# Floor area may exceed land area on multi-storey builds; flag only large misses.
FLOOR_LAND_TOL = 0.20
# Plots are rarely perfect rectangles; flag mặt tiền×sâu vs diện tích only when far off.
FRONTAGE_DEPTH_TOL = 0.20


@dataclass(frozen=True)
class ValidationIssue:
    """One failed validation, tied to the canonical field it concerns."""

    key: str
    message: str


def _digits(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")


def _first_int(value: str | None) -> int | None:
    m = re.search(r"\d+", value or "")
    return int(m.group(0)) if m else None


def _num(fv: FieldValue | None) -> float | None:
    """Return a field's numeric normalized value when available."""
    if fv is None:
        return None
    return fv.normalized if isinstance(fv.normalized, (int, float)) else None


def check_national_id(canonical: dict[str, FieldValue]) -> list[ValidationIssue]:
    """Flag a national ID that is not 9 (CMND) or 12 (CCCD) digits."""
    fv = canonical.get("owner_national_id")
    if fv is None or not fv.value:
        return []
    digits = _digits(fv.value)
    if len(digits) not in (9, 12):
        return [
            ValidationIssue(
                "owner_national_id",
                f"Số CMND/CCCD có {len(digits)} chữ số (kỳ vọng 9 hoặc 12).",
            )
        ]
    return []


def check_construction_year(canonical: dict[str, FieldValue]) -> list[ValidationIssue]:
    """Flag a construction year outside the plausible range."""
    fv = canonical.get("construction_year")
    if fv is None or not fv.value:
        return []
    year = _first_int(fv.value)
    if year is None or not (YEAR_MIN <= year <= YEAR_MAX):
        return [
            ValidationIssue(
                "construction_year",
                f"Năm xây dựng '{fv.value}' ngoài khoảng hợp lệ [{YEAR_MIN}, {YEAR_MAX}].",
            )
        ]
    return []


def check_issue_date(canonical: dict[str, FieldValue]) -> list[ValidationIssue]:
    """Certificate issue-date year must be plausible."""
    fv = canonical.get("issue_date")
    if fv is None or not isinstance(fv.normalized, str):
        return []
    year = _first_int(fv.normalized[:4])
    if year is None or not (YEAR_MIN <= year <= YEAR_MAX):
        return [ValidationIssue("issue_date", f"Ngày cấp '{fv.value}' có năm không hợp lệ.")]
    return []


def check_areas(canonical: dict[str, FieldValue]) -> list[ValidationIssue]:
    """Areas must be positive; floor area ≈ land area × số tầng when both known."""
    issues: list[ValidationIssue] = []
    land = _num(canonical.get("land_area_sqm"))
    floor = _num(canonical.get("floor_area_sqm"))

    for key, val in (("land_area_sqm", land), ("floor_area_sqm", floor)):
        if val is not None and val <= 0:
            issues.append(ValidationIssue(key, "Diện tích phải là số dương."))

    floors_fv = canonical.get("num_floors_desc")
    floors = _first_int(floors_fv.value) if floors_fv else None
    if land and floor and land > 0 and floors and floors >= 1:
        expected = land * floors
        if abs(floor - expected) / expected > FLOOR_LAND_TOL:
            issues.append(
                ValidationIssue(
                    "floor_area_sqm",
                    f"Diện tích sàn {floor:g} m² lệch nhiều so với "
                    f"đất {land:g} m² × {floors} tầng (≈{expected:g} m²).",
                )
            )
    return issues


def check_frontage_depth(canonical: dict[str, FieldValue]) -> list[ValidationIssue]:
    """Cross-check mặt tiền × chiều sâu ≈ diện tích đất (thửa gần chữ nhật)."""
    land = _num(canonical.get("land_area_sqm"))
    frontage = _num(canonical.get("frontage_m"))
    depth = _num(canonical.get("depth_m"))
    if not (land and frontage and depth) or land <= 0 or frontage <= 0 or depth <= 0:
        return []
    expected = frontage * depth
    if abs(land - expected) / land > FRONTAGE_DEPTH_TOL:
        return [
            ValidationIssue(
                "land_area_sqm",
                f"Diện tích đất {land:g} m² lệch nhiều so với mặt tiền {frontage:g} m × "
                f"sâu {depth:g} m (≈{expected:g} m²).",
            )
        ]
    return []


VALIDATORS = [
    check_national_id,
    check_construction_year,
    check_issue_date,
    check_areas,
    check_frontage_depth,
]


def run_validators(canonical: dict[str, FieldValue]) -> list[ValidationIssue]:
    """Run every validator and return the flat list of issues found."""
    issues: list[ValidationIssue] = []
    for validator in VALIDATORS:
        issues.extend(validator(canonical))
    return issues
