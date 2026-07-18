# property_dashboard — Chức năng 5 (Dashboard / Màn 5)

**Tổng hợp** Màn 1–4 thành dashboard ký duyệt. KPI + kết luận cho vay + hạn mức **100% xác định**;
LLM **chỉ diễn giải** 4 đoạn tóm tắt + kết luận (fail-safe template). Async + SSE. **API public** (không auth).

## Luồng
```
POST /api/v1/services/property_dashboard/run   { "input": { "case_id": "REQ-2026-2002" } }  →  { job_id }
GET  /api/v1/jobs/{job_id}/stream               (SSE: progress 50→100 → done { result })
```
Đọc: Màn 1 `property_legal_info`/`property_physical_info` · Màn 2 `lookup_finding` ·
Màn 3 `valuation_result` · Màn 4 `risk_assessment_result`/`risk_flag`/`risk_group` ·
`agent_trace_event` (timeline) · `appraisal_case` (sidebar lịch sử).

## Ranh giới xác định vs LLM (chi tiết: [docs/dashboard-methodology.md](../../../../../docs/dashboard-methodology.md))
| Khối | Nguồn | AI? |
|---|---|---|
| KPI (giá trị, tin cậy, risk_score/label, LTV) | valuation + risk | ❌ đọc thuần |
| **Hạn mức** = `round(value × LTV% / 100)` | tính | ❌ số học |
| **Verdict** 3 bậc | luật theo `risk_label` + cờ pháp lý | ❌ **xác định** (= tiền) |
| trace / case_history | đọc | ❌ |
| **4 tóm tắt + kết luận (văn phong)** | facts Màn 1–4 | ⚠️ LLM diễn giải, **không đổi số**, fail-safe template |

**Verdict:** `thap`/`trung_binh`→`de_xuat_cho_vay`; `cao`→`can_nhac`; `nghiem_trong`→`tu_choi`.
Hạ **1 bậc** nếu có cờ `legal` **đã xác thực** severity ≥ `cao`. `reasons[]` truy vết từng bước.

## Cấu trúc
- [synthesis.py](../../../capabilities/dashboard/synthesis.py) — verdict + hạn mức (thuần, config-driven)
- [narrator.py](../../../capabilities/dashboard/narrator.py) — LLM diễn giải bounded + fail-safe template
- [queries.py](../../../capabilities/dashboard/queries.py) — read-tools (KPI/trace/history)
- [service.py](service.py) — đọc DB → engine + narrator → `PropertyDashboardOutput`
- [schema.py](schema.py) — Pydantic I/O · Contract: [docs/contracts/property-dashboard-contract.md](../../../../../docs/contracts/property-dashboard-contract.md)

## Test
`pytest tests/capabilities/test_dashboard_synthesis.py` (verdict/hạn mức số học) ·
`test_dashboard_narrator.py` (LLM bounded/fail-safe) · `tests/plugins/test_property_dashboard.py` (DB→engine).
Case demo đủ dữ liệu: **REQ-2026-2002** (thap→cho vay), REQ-2026-2004 (cao→cân nhắc). REQ-2026-2000 thiếu Màn 4 → verdict null + warning.
