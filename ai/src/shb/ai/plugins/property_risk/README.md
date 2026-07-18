# property_risk — Chức năng 4 (Rủi ro / Màn 4)

Engine **tính rủi ro của tài sản đảm bảo** → **LTV đề xuất**. **100% xác định, không LLM**
(điểm rủi ro quyết định LTV = tiền → phải audit/tái lập được). Async + SSE. **API public** (không auth).

## Luồng
```
POST /api/v1/services/property_risk/run   { "input": { "case_id": "REQ-2026-0001" } }  →  { job_id }
GET  /api/v1/jobs/{job_id}/stream          (SSE: progress 50→100 → done { result })
```
Đọc DB: Màn 1 `property_legal_info`/`property_physical_info` · Màn 2 `lookup_finding` ·
Màn 3 `valuation_price_index_point` · bảng `risk_ltv_policy_band` (khung LTV do admin cấu hình).

## Công thức (chi tiết: [docs/risk-methodology.md](../../../../../docs/risk-methodology.md))
5 nhóm có trọng số → `risk_score = round(Σ trọng số×điểm / 100)`, cao = rủi ro cao:

| Nhóm | Trọng số | Điểm từ |
|---|---|---|
| legal (Pháp lý) | 30 | badge Màn 2 + (+20 đang thế chấp) + (+10 sở hữu không riêng) |
| liquidity (Thanh khoản) | 25 | badge Màn 2 |
| price_volatility (Biến động giá) | 20 | độ lệch chuẩn chuỗi chỉ số Màn 3 ×6, sàn 15 |
| physical_environment (Vật lý/MT) | 15 | badge môi trường + (+15 công trình >30 năm) |
| reputation (Danh tiếng/tâm linh) | 10 | badge Màn 2 (**chưa xác thực → chỉ cảnh báo**) |

badge→nền: `da_xac_thuc`=20 · `luu_y`=50 · `chua_xac_thuc`=60; +10 nếu confidence<60.
**risk_label / LTV** (khớp 4 khung): 0–20 `thap` 75% · 21–40 `trung_binh` 65% · 41–60 `cao` 55% · >60 `nghiem_trong` 45%.
Nhóm ≥50 → sinh **flag cần lưu ý**. Mỗi nhóm kèm `signals[]` truy vết điểm.

## Cấu trúc
- [config.py](../../../capabilities/risk/config.py) — hệ số/trọng số/khung LTV (chỉnh không đụng logic)
- [engine.py](../../../capabilities/risk/engine.py) — hàm thuần `compute_risk()`
- [service.py](service.py) — đọc DB → `RiskInputs` → `compute_risk` → `PropertyRiskOutput`
- [schema.py](schema.py) — Pydantic I/O · Contract: [docs/contracts/property-risk-contract.md](../../../../../docs/contracts/property-risk-contract.md)

## Test
`pytest tests/capabilities/test_risk_engine.py` (số học chính xác) · `tests/plugins/test_property_risk.py` (DB→engine).
