"""Assemble node: build the form-ready output over the full field registry.

Every canonical field is emitted (in registry/display order); fields with no
extracted value default to :attr:`FieldStatus.NHAP_TAY` (manual entry) so the UI
knows to leave them blank rather than implying they were found.
"""

from __future__ import annotations

import logging

from shb.ai.plugins.property_intake.documents import CANONICAL_FIELDS
from shb.ai.plugins.property_intake.schema import (
    FieldStatus,
    FieldValue,
    FormField,
    PropertyIntakeOutput,
)
from shb.ai.plugins.property_intake.state import IntakeState

logger = logging.getLogger(__name__)


async def assemble_node(state: IntakeState) -> dict:
    """Compose :class:`PropertyIntakeOutput` from canonical values + doc info."""
    canonical: dict[str, FieldValue] = state.get("canonical", {})
    intake_input = state["input"]

    fields: list[FormField] = []
    for spec in CANONICAL_FIELDS:
        fv = canonical.get(spec.key)
        if fv is None:
            fv = FieldValue(status=FieldStatus.NHAP_TAY)
        fields.append(
            FormField(
                key=spec.key,
                section=spec.section,
                label=spec.label,
                value=fv.value,
                confidence=fv.confidence,
                status=fv.status,
                source_doc=fv.source_doc,
                source_page=fv.source_page,
                source_snippet=fv.source_snippet,
                bbox=fv.bbox,
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
