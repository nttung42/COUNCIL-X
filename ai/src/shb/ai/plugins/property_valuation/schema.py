"""Pydantic schemas for the property_valuation plugin (Màn 3 — Định giá).

Output mirrors the Màn 3 mockup + ``valuation_*`` tables. Enum values match
``models_paa`` 1:1. The ``subjective_adjustment`` block makes the single LLM input
explicit and separable from the deterministic formula (audit).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ValuationMethodKey(StrEnum):
    """3 phương pháp định giá (khớp enum DB ``valuation_method_key``)."""

    SALES_COMPARISON = "sales_comparison"
    HEDONIC_ML = "hedonic_ml"
    COST_APPROACH = "cost_approach"


class ConfidenceFactorKey(StrEnum):
    """5 yếu tố cấu thành độ tin cậy (khớp enum DB ``confidence_factor_key``)."""

    COMP_QUANTITY_QUALITY = "comp_quantity_quality"
    METHOD_CONSENSUS = "method_consensus"
    LEGAL_PLANNING_COMPLETENESS = "legal_planning_completeness"
    MARKET_VOLATILITY = "market_volatility"
    COMP_SIMILARITY = "comp_similarity"


class ValuationSummary(BaseModel):
    """Khối tổng hợp — 4 KPI tile (↔ valuation_result)."""

    proposed_value_vnd: int
    value_range_low_vnd: int
    value_range_high_vnd: int
    price_per_sqm_vnd: int
    confidence_pct: int
    comparable_count: int
    price_index_period: str | None = None
    price_index_value: float | None = None
    price_index_base: float | None = 100
    confidence_inference_text: str | None = None


class MethodOut(BaseModel):
    """1 phương pháp định giá (↔ valuation_method) — bar chart."""

    method_key: ValuationMethodKey
    estimated_value_vnd: int
    weight_pct: int
    contribution_value_vnd: int
    method_confidence_pct: int | None = None
    inputs: list[str] = Field(default_factory=list)
    inference_text: str | None = None
    source_label: str | None = None


class FactorOut(BaseModel):
    """1 yếu tố độ tin cậy (↔ valuation_confidence_factor)."""

    factor_key: ConfidenceFactorKey
    label: str
    weight_pct: int
    score: int


class PriceIndexPointOut(BaseModel):
    """1 điểm chuỗi chỉ số giá (↔ valuation_price_index_point) — sparkline."""

    period_label: str
    index_value: float
    display_order: int


class SubjectiveAdjustmentOut(BaseModel):
    """Điều chỉnh cảm tính do LLM — tách bạch khỏi công thức."""

    value_pct: float  # vd +2.5 (%)
    reason: str
    source: str = "llm_inference"
    bound_pct: float = 5.0


class PropertyValuationInput(BaseModel):
    """Input: mã hồ sơ cần định giá."""

    case_id: str = Field(..., description="Mã hồ sơ (REQ-...).")


class PropertyValuationOutput(BaseModel):
    """Output Màn 3: định giá + 3 phương pháp + 5 yếu tố tin cậy + chỉ số giá."""

    case_id: str
    valuation: ValuationSummary | None = None
    methods: list[MethodOut] = Field(default_factory=list)
    confidence_factors: list[FactorOut] = Field(default_factory=list)
    price_index_series: list[PriceIndexPointOut] = Field(default_factory=list)
    subjective_adjustment: SubjectiveAdjustmentOut | None = None
    warnings: list[str] = Field(default_factory=list)
