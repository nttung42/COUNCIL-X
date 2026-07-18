"""Verify node (feature #5): LLM-judge grounding of extracted candidates.

Each extracted value is judged against its own source snippet by an independent
LLM pass ("does this evidence actually support this value?"). Values the judge
rejects have their ``verifier_passed`` flag set to ``False`` and their confidence
capped, which downstream tiering turns into a *cần xác minh* cell.

The verifier is **fail-open**: if the model call errors, values keep
``verifier_passed = None`` and are not penalised, so a verifier outage never
silently blanks the whole form. (Self-consistency — re-extracting and comparing —
is an alternative mechanism; LLM-judge is used here.)
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from shb.ai.llm import get_chat_model
from shb.ai.plugins.property_intake.documents import (
    FIELD_SPEC_BY_KEY,
    VERIFIER_FAIL_CONF_CAP,
)
from shb.ai.plugins.property_intake.prompts import VERIFY_SYSTEM
from shb.ai.plugins.property_intake.schema import FieldStatus, FieldValue, VerificationResult
from shb.ai.plugins.property_intake.state import IntakeState

logger = logging.getLogger(__name__)


def _build_verifier():
    """Return an LLM runnable that yields a validated :class:`VerificationResult`."""
    return get_chat_model().with_structured_output(VerificationResult)


def _label(key: str) -> str:
    spec = FIELD_SPEC_BY_KEY.get(key)
    return spec.label if spec else key


def _is_verifiable(fv: FieldValue) -> bool:
    """Only grounded, non-inferred values with a snippet are worth judging."""
    return bool(fv.value) and bool(fv.source_snippet) and fv.status != FieldStatus.SUY_LUAN


def _build_request(items: list[tuple[int, str, FieldValue]]) -> str:
    lines = []
    for index, key, fv in items:
        lines.append(
            f"[{index}] Trường: {_label(key)}\n"
            f"    Giá trị: {fv.value}\n"
            f"    Đoạn trích nguồn: {fv.source_snippet}"
        )
    return "\n".join(lines)


async def verify_node(state: IntakeState) -> dict:
    """Judge every candidate value against its evidence; annotate ``verifier_passed``."""
    candidates: dict[str, list[FieldValue]] = state.get("candidates", {})
    warnings: list[str] = list(state.get("warnings", []))

    # Flatten to an indexed worklist of verifiable candidates.
    items: list[tuple[int, str, FieldValue]] = []
    for key, values in candidates.items():
        for fv in values:
            if _is_verifiable(fv):
                items.append((len(items), key, fv))

    if items:
        await _run_verifier(items, warnings)

    _report_progress(state.get("ctx"), 70)
    return {"candidates": candidates, "warnings": warnings}


async def _run_verifier(
    items: list[tuple[int, str, FieldValue]],
    warnings: list[str],
    *,
    verifier=None,
) -> None:
    """Call the LLM judge and apply verdicts to the candidate values in place."""
    try:
        runnable = verifier or _build_verifier()
        result: VerificationResult = await runnable.ainvoke(
            [
                SystemMessage(content=VERIFY_SYSTEM),
                HumanMessage(content="Các mục cần kiểm tra:\n\n" + _build_request(items)),
            ]
        )
    except Exception as exc:  # noqa: BLE001 - fail-open: never penalise on outage
        logger.warning("Verifier failed, leaving values unjudged: %s", exc)
        warnings.append("Không chạy được bước kiểm chứng (verifier); giữ nguyên độ tin cậy.")
        return

    verdicts = {c.index: c.supported for c in result.checks}
    for index, _key, fv in items:
        supported = verdicts.get(index)
        if supported is None:
            continue
        fv.verifier_passed = supported
        if not supported:
            fv.confidence = round(min(fv.confidence, VERIFIER_FAIL_CONF_CAP), 2)


def _report_progress(ctx, value: int) -> None:
    cb = getattr(ctx, "update_progress", None)
    if callable(cb):
        try:
            cb(value)
        except Exception:  # pragma: no cover - progress is best-effort
            logger.debug("progress callback failed", exc_info=True)
