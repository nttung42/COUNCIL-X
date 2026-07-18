"""Pydantic schemas for the property_lookup plugin (Màn 2 — Kết quả tra cứu).

Output-facing models mirroring the ``lookup_finding`` / ``market_comparable``
tables. Enum *values* match ``models_paa`` (and the demo seed) 1:1 so the JSON is
directly consumable by the frontend's Màn 2 cards.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class LookupCategory(StrEnum):
    """7 nguồn tra cứu của Research Agent (khớp enum DB ``lookup_category``)."""

    MARKET_PRICE = "market_price"
    PLANNING_ZONING = "planning_zoning"
    LEGAL_STATUS = "legal_status"
    NEIGHBORHOOD_AMENITY = "neighborhood_amenity"
    ENVIRONMENTAL_RISK = "environmental_risk"
    LIQUIDITY_STAT = "liquidity_stat"
    STIGMA_REPUTATION = "stigma_reputation"


class LookupBadge(StrEnum):
    """Badge 3 màu trên mỗi lookup-detail card (khớp enum DB ``lookup_badge``)."""

    DA_XAC_THUC = "da_xac_thuc"
    LUU_Y = "luu_y"
    CHUA_XAC_THUC = "chua_xac_thuc"


class MarketComparableOut(BaseModel):
    """1 dòng "Giao dịch so sánh khu vực" (từ ``market_comparable``)."""

    address: str
    distance_km: float | None = None
    area_sqm: float | None = None
    transaction_date: str | None = None  # ISO date 'YYYY-MM-DD'
    price_per_sqm_vnd: int


class LookupFindingOut(BaseModel):
    """1 lookup-detail card (từ ``lookup_finding``)."""

    category: LookupCategory
    tool_name: str
    title: str
    status_badge: LookupBadge
    raw_findings: list[str] = Field(default_factory=list)
    inference_text: str | None = None
    source_label: str | None = None
    confidence_pct: int | None = None


class PropertyLookupInput(BaseModel):
    """Input: mã hồ sơ cần đọc kết quả tra cứu."""

    case_id: str = Field(..., description="Mã hồ sơ (REQ-...).")


class PropertyLookupOutput(BaseModel):
    """Output Màn 2: 7 finding + bảng giao dịch so sánh + cảnh báo."""

    case_id: str
    findings: list[LookupFindingOut] = Field(default_factory=list)
    market_comparables: list[MarketComparableOut] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
