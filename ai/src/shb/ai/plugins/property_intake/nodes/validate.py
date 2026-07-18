"""Validate node (feature 4): apply rule + arithmetic cross-checks.

Runs the pure validators over the merged canonical values and attaches any issue
messages to the offending field's ``validation_flags``. Tiering then downgrades
flagged fields to *cần xác minh*. Validation never removes a value.
"""

from __future__ import annotations

import logging

from shb.ai.plugins.property_intake.schema import FieldValue
from shb.ai.plugins.property_intake.state import IntakeState
from shb.ai.plugins.property_intake.validators import run_validators

logger = logging.getLogger(__name__)


async def validate_node(state: IntakeState) -> dict:
    """Attach validation flags to canonical fields that fail a rule/cross-check."""
    canonical: dict[str, FieldValue] = state.get("canonical", {})
    warnings: list[str] = list(state.get("warnings", []))

    for issue in run_validators(canonical):
        fv = canonical.get(issue.key)
        if fv is None:
            continue
        if issue.message not in fv.validation_flags:
            fv.validation_flags.append(issue.message)
            warnings.append(f"Kiểm tra dữ liệu: {issue.message}")

    _report_progress(state.get("ctx"), 92)
    return {"canonical": canonical, "warnings": warnings}


def _report_progress(ctx, value: int) -> None:
    cb = getattr(ctx, "update_progress", None)
    if callable(cb):
        try:
            cb(value)
        except Exception:  # pragma: no cover - progress is best-effort
            logger.debug("progress callback failed", exc_info=True)
