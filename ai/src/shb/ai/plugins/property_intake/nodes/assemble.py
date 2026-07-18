"""Assemble node: build the form-ready output over the full field registry.

Every canonical field is emitted (in registry/display order); fields with no
extracted value default to :attr:`FieldStatus.NHAP_TAY` (manual entry) so the UI
knows to leave them blank rather than implying they were found.
"""

from __future__ import annotations

import logging

from shb.ai.plugins.property_intake.documents import CANONICAL_FIELDS, tier_status
from shb.ai.plugins.property_intake.schema import (
    AlternativeValue,
    FieldStatus,
    FieldValue,
    FormField,
    PropertyIntakeOutput,
)
from shb.ai.plugins.property_intake.state import IntakeState

logger = logging.getLogger(__name__)


def _pct(confidence: float) -> int:
    """Convert internal 0..1 confidence to the 0..100 SMALLINT used by the DB/UI."""
    return round(confidence * 100)


def _to_alternative(fv: FieldValue) -> AlternativeValue:
    """Project a competing candidate into the output ``AlternativeValue`` shape."""
    return AlternativeValue(
        value=fv.value,
        normalized=fv.normalized,
        status=FieldStatus.MAU_THUAN,
        confidence_pct=_pct(fv.confidence),
        source_file_id=fv.source_file_id,
        source_doc_type=fv.source_doc_type,
        source_page=fv.source_page,
        source_snippet=fv.source_snippet,
        bbox=fv.bbox,
    )


async def assemble_node(state: IntakeState) -> dict:
    """Compose :class:`PropertyIntakeOutput`, applying final confidence tiering (#9)."""
    canonical: dict[str, FieldValue] = state.get("canonical", {})
    intake_input = state["input"]

    fields: list[FormField] = []
    for spec in CANONICAL_FIELDS:
        fv = canonical.get(spec.key)
        if fv is None:
            fv = FieldValue(status=FieldStatus.NHAP_TAY)
        # #9: the final cell status is decided here from confidence + verifier +
        # validation + conflict signals accumulated by the earlier nodes.
        status = tier_status(fv)
        fields.append(
            FormField(
                key=spec.key,
                section=spec.section,
                label=spec.label,
                target_table=spec.target_table,
                target_field=spec.target_field,
                value=fv.value,
                normalized=fv.normalized,
                status=status,
                confidence_pct=_pct(fv.confidence),
                source_file_id=fv.source_file_id,
                source_page=fv.source_page,
                source_snippet=fv.source_snippet,
                bbox=fv.bbox,
                verifier_passed=fv.verifier_passed,
                validation_flags=fv.validation_flags,
                alternatives=[_to_alternative(a) for a in fv.alternatives],
            )
        )

    output = PropertyIntakeOutput(
        case_id=intake_input.case_id,
        documents=state.get("documents_info", []),
        fields=fields,
        warnings=state.get("warnings", []),
    )

    _report_progress(state.get("ctx"), 100)
    return {"output": output}


def _report_progress(ctx, value: int) -> None:
    cb = getattr(ctx, "update_progress", None)
    if callable(cb):
        try:
            cb(value)
        except Exception:  # pragma: no cover - progress is best-effort
            logger.debug("progress callback failed", exc_info=True)
