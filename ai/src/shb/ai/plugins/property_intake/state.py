"""Shared graph state types for the property_intake pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict

from shb.ai.plugins.property_intake.schema import (
    DocType,
    DocumentInfo,
    FieldValue,
    PropertyIntakeInput,
    PropertyIntakeOutput,
)
from shb.services.parsers import ParsedDocument


@dataclass
class IngestedDoc:
    """A parsed + (lightly) classified uploaded document."""

    file_id: str
    file_name: str
    doc_type: DocType
    parsed: ParsedDocument


class IntakeState(TypedDict, total=False):
    """Mutable state threaded through the LangGraph pipeline."""

    input: PropertyIntakeInput
    ctx: Any  # AIServiceContext (kept as Any to avoid a hard import cycle)
    docs: list[IngestedDoc]
    candidates: dict[str, list[FieldValue]]  # per-key candidates before merge
    canonical: dict[str, FieldValue]  # reconciled single value per key (post-merge)
    documents_info: list[DocumentInfo]
    warnings: list[str]
    output: PropertyIntakeOutput
