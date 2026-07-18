# Contract — `property_dashboard` (Chức năng 5: Dashboard / Màn 5)

> **Trạng thái:** v1. **Định dạng:** JSON. Service **async + SSE**. **API public** (không cần X-API-Key/register).
> **Bản chất:** **tổng hợp** Màn 1–4 thành dashboard ký duyệt. KPI + kết luận cho vay + hạn mức **100% xác định** ([dashboard-methodology.md](../dashboard-methodology.md)); LLM **chỉ diễn giải văn phong** 4 đoạn tóm tắt + kết luận, **không đổi số/quyết định**, fail-safe về template.

## 1. Enum (khớp `models_paa`)
| Trường | Enum | Giá trị |
|---|---|---|
| `verdict.decision` | (F5) | `de_xuat_cho_vay` · `can_nhac` · `tu_choi` |
| `kpi.risk_label` | `severity_level` | `thap` · `trung_binh` · `cao` · `nghiem_trong` |

## 2. Input & gọi (public)
```
POST /api/v1/services/property_dashboard/run   body { "input": { "case_id": "REQ-2026-2002" } }
→ 200 { "job_id": "...", "status": "pending" }          # KHÔNG cần X-API-Key
GET  /api/v1/jobs/{job_id}/stream               (SSE)   # done { result: PropertyDashboardOutput }
```
Đọc: Màn 1 `property_legal_info`/`property_physical_info` · Màn 2 `lookup_finding` · Màn 3 `valuation_result` · Màn 4 `risk_assessment_result`/`risk_flag`/`risk_group` · `agent_trace_event` · `appraisal_case` (sidebar).

## 3. Output — `PropertyDashboardOutput`
```jsonc
{
  "case_id": "REQ-2026-2002",
  "kpi": {                               // ↔ v_dashboard_kpi (valuation + risk) — null nếu thiếu Màn 3 hoặc 4
    "proposed_value_vnd": 49940000000, "value_range_low_vnd": 46710000000,
    "value_range_high_vnd": 53380000000, "valuation_confidence_pct": 83,
    "risk_score": 18, "risk_label": "thap", "ltv_proposed_pct": 75
  },
  "verdict": {                           // kết luận XÁC ĐỊNH (engine synthesis) — null nếu thiếu Màn 4
    "decision": "de_xuat_cho_vay",
    "headline": "Đề xuất cho vay theo mức LTV chuẩn",
    "max_loan_vnd": 37455000000,         // = proposed_value × LTV% (làm tròn)
    "downgraded": false,
    "reasons": ["…truy vết từng bước…"]  // AUDIT
  },
  "step_summaries": [                     // 4 dòng "Tổng hợp theo từng bước" (↔ dashboard_step_summary)
    { "step_number": 1, "title": "Hồ sơ & tài sản", "summary_text": "…", "generated_by": "llm" }
  ],
  "overall_narrative": "Kết luận: … Hạn mức … Điểm rủi ro …",
  "trace": [ { "seconds_offset", "actor", "title", "description" } ],   // ↔ agent_trace_event
  "case_history": [ { "case_id", "address", "status", "updated_at" } ], // ↔ v_case_history (sidebar)
  "warnings": []
}
```
- Thiếu Màn 4 → `kpi=null`, `verdict=null` + warning. Thiếu Màn 3 → warning; `step_summaries`/`trace`/`case_history` vẫn trả.
- `generated_by`: `llm` (đã diễn giải) hoặc `template` (fail-safe khi LLM lỗi/không cấu hình).

## 4. Ánh xạ ↔ DB
`kpi`↔`valuation_result`+`risk_assessment_result` · `verdict` (tính, không lưu bảng riêng) · `step_summaries`↔`dashboard_step_summary` · `trace`↔`agent_trace_event` · `case_history`↔`appraisal_case`(+địa chỉ).

## 5. Minh bạch (yêu cầu nghiệp vụ)
- **KPI + verdict + max_loan 100% xác định, audit/tái lập được**; `verdict.reasons[]` truy vết từng bước. Luật verdict + công thức hạn mức: [dashboard-methodology.md](../dashboard-methodology.md), hệ số ở [synthesis.py](../../src/shb/capabilities/dashboard/synthesis.py).
- **LLM chỉ diễn giải** 4 tóm tắt + kết luận; con số/quyết định bơm sẵn từ engine, LLM không đổi được; lỗi LLM → template. Đã kiểm chứng: mọi số liệu giữ nguyên chính xác.
- Chỉ **cờ pháp lý đã xác thực ≥ cao** mới hạ bậc verdict; tin đồn/chưa xác thực không ảnh hưởng quyết định.
