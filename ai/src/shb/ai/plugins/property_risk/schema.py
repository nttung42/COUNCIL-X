"""Pydantic schemas for the property_risk plugin (Màn 4 — Rủi ro).

Output mirrors the Màn 4 mockup + ``risk_*`` tables. Enum values match
``models_paa`` 1:1. Every group carries ``signals`` (why the score was built) so
the risk → LTV decision is auditable.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class RiskGroupKey(StrEnum):
    """5 nhóm rủi ro (khớp enum DB ``risk_group_key``)."""

    LEGAL = "legal"
    LIQUIDITY = "liquidity"
    PRICE_VOLATILITY = "price_volatility"
    PHYSICAL_ENVIRONMENT = "physical_environment"
    REPUTATION = "reputation"


class SeverityLevel(StrEnum):
    """Mức nghiêm trọng (khớp enum DB ``severity_level``)."""

    THAP = "thap"
    TRUNG_BINH = "trung_binh"
    CAO = "cao"
    NGHIEM_TRONG = "nghiem_trong"


class RiskGroupOut(BaseModel):
    """1 nhóm rủi ro cấu thành (↔ risk_group) — bar chart."""

    group_key: RiskGroupKey
    label: str
    weight_pct: int
    score: int
    signals: list[str] = Field(default_factory=list)
    source_confidence: int | None = None
    verified: bool = False


class RiskFlagOut(BaseModel):
    """1 "flag cần lưu ý" (↔ risk_flag)."""

    severity: SeverityLevel
    title: str
    description: str
    confidence_pct: int | None = None
    verified: bool = False


class LtvBandOut(BaseModel):
    """1 khung chính sách LTV (↔ risk_ltv_policy_band)."""

    min_score: int
    max_score: int | None = None
    max_ltv_pct: int
    label: str


class RiskAssessmentSummary(BaseModel):
    """Tổng hợp rủi ro (↔ risk_assessment_result)."""

    risk_score: int
    risk_label: SeverityLevel
    ltv_proposed_pct: int
    risk_inference_text: str | None = None


class PropertyRiskInput(BaseModel):
    """Input: mã hồ sơ cần chấm rủi ro."""

    case_id: str = Field(..., description="Mã hồ sơ (REQ-...).")


class PropertyRiskOutput(BaseModel):
    """Output Màn 4: điểm rủi ro + LTV + 5 nhóm + flags + khung chính sách."""

    case_id: str
    assessment: RiskAssessmentSummary | None = None
    groups: list[RiskGroupOut] = Field(default_factory=list)
    flags: list[RiskFlagOut] = Field(default_factory=list)
    ltv_policy_bands: list[LtvBandOut] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
