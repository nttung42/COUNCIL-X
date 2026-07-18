"""Pydantic schema cho request/response API (contracts/appraisal-api.md).

Chỉ định nghĩa các schema I/O của lớp API. Các entity nội bộ (envelope lookup,
ValuationResult, AssetRiskAssessment, AppraisalReportDraft) đã do agent Wave 1
định nghĩa và được truyền/serialize dạng dict — API không định nghĩa lại để tránh
lệch schema (Nguyên tắc IV).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class PropertyType(str, Enum):
    nha_pho = "nha_pho"
    dat_nen = "dat_nen"
    chung_cu = "chung_cu"
    bds_thuong_mai = "bds_thuong_mai"


class LegalStatus(str, Enum):
    so_hong = "so_hong"
    so_do = "so_do"
    giay_tay = "giay_tay"
    khac = "khac"


class SubjectProperty(BaseModel):
    # extra="allow" để không mất field phụ (frontage_m, alley_width_m, floors,
    # cadastral_id, ward, owner_id...) mà Valuation/Research có thể dùng.
    model_config = ConfigDict(extra="allow")

    address: str = Field(..., min_length=1)
    lat: Optional[float] = None
    long: Optional[float] = None
    area_m2: float = Field(..., gt=0, description="Diện tích m², phải > 0")
    property_type: PropertyType = PropertyType.nha_pho
    legal_status_claimed: LegalStatus = LegalStatus.so_hong


class LoanContext(BaseModel):
    model_config = ConfigDict(extra="allow")

    requested_amount: int = Field(..., gt=0)
    purpose: str = "the_chap_vay_von"


class PropertyAppraisalRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
    subject_property: SubjectProperty
    loan_context: Optional[LoanContext] = None


class AppraisalRequestAccepted(BaseModel):
    case_id: str
    request_id: str
    status: str = "processing"


class CaseSummary(BaseModel):
    case_id: str
    address: str
    status: str
    updated_at: Optional[str] = None


class ChatMessageIn(BaseModel):
    role: str = "user"
    content: str = Field(..., min_length=1)


class Citation(BaseModel):
    source_doc: str
    excerpt: str


class ChatMessageOut(BaseModel):
    role: str = "agent"
    content: str
    citations: list[Citation] = Field(default_factory=list)


class ChecklistToggleIn(BaseModel):
    is_checked: bool


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    field_errors: list[dict[str, Any]] = Field(default_factory=list)
