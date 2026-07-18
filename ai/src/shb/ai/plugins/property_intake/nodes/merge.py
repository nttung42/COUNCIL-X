"""Merge node: reconcile per-field candidates across documents (PR4).

For each canonical key the candidate from the most authoritative source wins
(``SOURCE_PRIORITY``: GCN > thông báo thuế > tờ khai > biên bản). When a
lower-priority source *disagrees* beyond tolerance the field is marked
``mau_thuan`` and every competing value is retained in ``alternatives`` so a human
can resolve it. When sources agree, the corroboration nudges confidence up.
"""

from __future__ import annotations

import logging

from shb.ai.plugins.property_intake.documents import (
    CORROBORATION_BONUS,
    FIELD_SPEC_BY_KEY,
    source_priority,
    values_agree,
)
from shb.ai.plugins.property_intake.schema import FieldStatus, FieldValue
from shb.ai.plugins.property_intake.state import IntakeState

logger = logging.getLogger(__name__)


def _label(key: str) -> str:
    spec = FIELD_SPEC_BY_KEY.get(key)
    return spec.label if spec else key


def _distinct(values: list[FieldValue]) -> list[FieldValue]:
    """Deduplicate values that agree with one another, preserving order."""
    kept: list[FieldValue] = []
    for fv in values:
        if not any(values_agree(fv, seen) for seen in kept):
            kept.append(fv)
    return kept


def merge_candidates(candidates: list[FieldValue]) -> FieldValue | None:
    """Reconcile one field's candidates into a single value with provenance."""
    if not candidates:
        return None

    ordered = sorted(
        candidates,
        key=lambda c: (source_priority(c), c.confidence, c.verifier_passed is True),
        reverse=True,
    )
    primary = ordered[0].model_copy(deep=True)
    rest = ordered[1:]
    conflicting = [c for c in rest if not values_agree(primary, c)]
    agreeing = [c for c in rest if values_agree(primary, c)]

    if conflicting:
        primary.status = FieldStatus.MAU_THUAN
        primary.alternatives = _distinct(conflicting)
    elif agreeing:
        bonus = CORROBORATION_BONUS * len(agreeing)
        primary.confidence = round(min(0.99, primary.confidence + bonus), 2)

    return primary


async def merge_node(state: IntakeState) -> dict:
    """Reconcile ``candidates`` into a single ``canonical`` value per field."""
    candidates: dict[str, list[FieldValue]] = state.get("candidates", {})
    warnings: list[str] = list(state.get("warnings", []))

    canonical: dict[str, FieldValue] = {}
    for key, cands in candidates.items():
        merged = merge_candidates(cands)
        if merged is None:
            continue
        canonical[key] = merged
        if merged.status == FieldStatus.MAU_THUAN:
            others = ", ".join(alt.value for alt in merged.alternatives if alt.value)
            warnings.append(
                f"Trường '{_label(key)}' mâu thuẫn giữa các tài liệu: "
                f"ưu tiên '{merged.value}' (từ {merged.source_doc}); giá trị khác: {others}."
            )

    _report_progress(state.get("ctx"), 82)
    return {"canonical": canonical, "warnings": warnings}


def _report_progress(ctx, value: int) -> None:
    cb = getattr(ctx, "update_progress", None)
    if callable(cb):
        try:
            cb(value)
        except Exception:  # pragma: no cover - progress is best-effort
            logger.debug("progress callback failed", exc_info=True)
