"""generate_report_draft — sinh nháp biên bản thẩm định (AppraisalReportDraft §9).

NGUYÊN TẮC I (NON-NEGOTIABLE): mọi output là ĐỀ XUẤT, không phải quyết định.
- `signature_block` LUÔN để trống chờ ký (2 dòng checkbox: thẩm định viên + chuyên
  viên tín dụng) — KHÔNG bao giờ tự sinh chữ ký hay đánh dấu "đã duyệt".
- KHÔNG chèn kết luận "đã duyệt"/"từ chối"/"chấp thuận" vào bất kỳ section nào.

Hàm nhận input dạng dict (JSON) HOẶC object (pydantic/dataclass) — dùng accessor
linh hoạt để không phụ thuộc schema class của agent Valuation/Risk. Chữ ký hàm giữ
ổn định cho agent Orchestrator & API.
"""

from __future__ import annotations

from typing import Any, Optional

try:
    from pydantic import BaseModel

    class ReportSections(BaseModel):
        property_info: str
        valuation: str
        risk_and_ltv: str

    class AppraisalReportDraft(BaseModel):
        sections: ReportSections
        signature_block: str

    _HAS_PYDANTIC = True
except ImportError:  # pragma: no cover
    from dataclasses import dataclass

    @dataclass
    class ReportSections:  # type: ignore[no-redef]
        property_info: str
        valuation: str
        risk_and_ltv: str

    @dataclass
    class AppraisalReportDraft:  # type: ignore[no-redef]
        sections: ReportSections
        signature_block: str

    _HAS_PYDANTIC = False


# Signature block BẤT BIẾN — luôn 2 dòng checkbox trống (Nguyên tắc I).
SIGNATURE_BLOCK = (
    "☐ Chữ ký thẩm định viên    ☐ Xác nhận chuyên viên tín dụng\n"
    "(Bản nháp — chưa có hiệu lực cho tới khi có đủ chữ ký của con người.)"
)


def _get(obj: Any, *keys: str, default: Any = None) -> Any:
    """Truy cập field lồng nhau, hỗ trợ cả dict lẫn object.

    VD: ``_get(valuation, "value_range", "low")``.
    """
    cur = obj
    for key in keys:
        if cur is None:
            return default
        if isinstance(cur, dict):
            cur = cur.get(key, default)
        else:
            cur = getattr(cur, key, default)
    return cur if cur is not None else default


def _fmt_vnd(value: Any) -> str:
    """Định dạng số tiền VNĐ có phân tách nghìn; an toàn với None/không phải số."""
    try:
        return f"{int(round(float(value))):,} VNĐ"
    except (TypeError, ValueError):
        return "N/A"


def _fmt_pct(value: Any) -> str:
    """Định dạng tỉ lệ 0–1 thành %; an toàn với None."""
    try:
        return f"{float(value):.0%}"
    except (TypeError, ValueError):
        return "N/A"


def _extract_checklist_items(kb_checklist: Optional[list[dict]]) -> list[str]:
    """Trích các dòng checklist ('- [ ] ...') từ kết quả query_knowledge_base.

    Trả về list ``"nội dung mục — (nguồn: source_doc)"`` để giữ citation.
    """
    items: list[str] = []
    for entry in kb_checklist or []:
        source = entry.get("source_doc", "?") if isinstance(entry, dict) else "?"
        text = entry.get("chunk_text", "") if isinstance(entry, dict) else ""
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("- [ ]", "- [x]", "* [ ]")):
                content = stripped.split("]", 1)[1].strip()
                if content:
                    items.append(f"{content} — (nguồn: {source})")
    return items


def generate_report_draft(
    subject_property: Any,
    valuation_result: Any,
    risk_result: Any,
    kb_checklist: Optional[list[dict]] = None,
) -> AppraisalReportDraft:
    """Sinh AppraisalReportDraft từ dữ liệu tài sản + định giá + rủi ro + checklist RAG.

    Args:
        subject_property: PropertyAppraisalRequest.subject_property (dict/object) —
            cần `address`, `area_m2`, `legal_status_claimed`, tuỳ chọn `property_type`.
        valuation_result: ValuationResult (data-model §6) — dict/object.
        risk_result: AssetRiskAssessment (data-model §7) — dict/object.
        kb_checklist: kết quả `query_knowledge_base(...)` cho checklist theo
            property_type (list dict có `source_doc`, `chunk_text`).

    Returns:
        AppraisalReportDraft: 3 section markdown + `signature_block` LUÔN trống chờ ký.
    """
    # --- Section 1: thông tin tài sản ---
    address = _get(subject_property, "address", default="N/A")
    area_m2 = _get(subject_property, "area_m2", default="N/A")
    legal_claimed = _get(subject_property, "legal_status_claimed", default="N/A")
    prop_type = _get(subject_property, "property_type", default=None)

    property_info_lines = [
        "## Thông tin tài sản",
        f"- **Địa chỉ**: {address}",
        f"- **Diện tích**: {area_m2} m²",
        f"- **Pháp lý khai báo**: {legal_claimed}",
    ]
    if prop_type:
        property_info_lines.append(f"- **Loại tài sản**: {prop_type}")
    property_info = "\n".join(property_info_lines)

    # --- Section 2: định giá ---
    estimated = _get(valuation_result, "estimated_value")
    low = _get(valuation_result, "value_range", "low")
    high = _get(valuation_result, "value_range", "high")
    confidence = _get(valuation_result, "confidence_score")
    comparables_used = _get(valuation_result, "comparables_used", default=0)
    adjustment_notes = _get(valuation_result, "adjustment_notes", default=[]) or []

    valuation_lines = [
        "## Định giá",
        f"- **Giá trị đề xuất**: {_fmt_vnd(estimated)}",
        f"- **Khoảng giá trị**: {_fmt_vnd(low)} – {_fmt_vnd(high)}",
        f"- **Độ tin cậy**: {_fmt_pct(confidence)}",
        f"- **Số giao dịch so sánh sử dụng**: {comparables_used}",
    ]
    if adjustment_notes:
        valuation_lines.append("- **Ghi chú điều chỉnh**:")
        valuation_lines.extend(f"  - {note}" for note in adjustment_notes)
    valuation = "\n".join(valuation_lines)

    # --- Section 3: rủi ro & LTV ---
    risk_score = _get(risk_result, "asset_risk_score", default="N/A")
    risk_tier = _get(risk_result, "risk_tier", default="N/A")
    ltv_cap = _get(risk_result, "recommended_ltv_cap")
    flags = _get(risk_result, "flags", default=[]) or []
    recommended_conditions = (
        _get(risk_result, "recommended_conditions", default=[]) or []
    )

    risk_lines = [
        "## Rủi ro & LTV",
        f"- **Điểm rủi ro tài sản**: {risk_score}/100 ({risk_tier})",
        f"- **LTV đề xuất**: {_fmt_pct(ltv_cap)}",
    ]

    if flags:
        risk_lines.append("- **Cảnh báo (flags) cần lưu ý**:")
        for flag in flags:
            ftype = _get(flag, "type", default="?")
            severity = _get(flag, "severity", default="?")
            detail = _get(flag, "detail", default="")
            verified = _get(flag, "verified", default=None)
            suffix = " [chưa xác thực]" if verified is False else ""
            risk_lines.append(f"  - `{ftype}` ({severity}): {detail}{suffix}")

    if recommended_conditions:
        risk_lines.append("- **Điều kiện khuyến nghị**:")
        risk_lines.extend(f"  - {cond}" for cond in recommended_conditions)

    # Chèn checklist xác minh (từ RAG) khi có flag rủi ro — Nguyên tắc I: đây là
    # mục CẦN THẨM ĐỊNH VIÊN XÁC MINH, không phải kết luận duyệt/từ chối.
    if flags:
        checklist_items = _extract_checklist_items(kb_checklist)
        if checklist_items:
            risk_lines.append("")
            risk_lines.append(
                "### Mục cần thẩm định viên xác minh thực địa (tham khảo checklist nội bộ)"
            )
            risk_lines.extend(f"- ☐ {item}" for item in checklist_items)

    risk_and_ltv = "\n".join(risk_lines)

    sections = ReportSections(
        property_info=property_info,
        valuation=valuation,
        risk_and_ltv=risk_and_ltv,
    )
    return AppraisalReportDraft(sections=sections, signature_block=SIGNATURE_BLOCK)
