# Dashboard (Màn 5) — phương pháp tổng hợp & kết luận

> Màn 5 **tổng hợp** kết quả Màn 1–4 để cán bộ ký duyệt. Con số + kết luận **100% xác định,
> audit/tái lập được** (vì = tiền); LLM chỉ **diễn giải văn phong**, không đổi số/quyết định.
> Engine: [capabilities/dashboard/synthesis.py](../src/shb/capabilities/dashboard/synthesis.py).

## 1. Hạn mức cho vay tối đa (số học thuần)
```
max_loan_vnd = round(proposed_value_vnd × ltv_proposed_pct / 100)
```
- `proposed_value_vnd` ← Màn 3 (`valuation_result`), `ltv_proposed_pct` ← Màn 4 (`risk_assessment_result`).
- Thiếu 1 trong 2 → `max_loan_vnd = null` + ghi lý do.

## 2. Kết luận cho vay (verdict) — 3 bậc, luật xác định
Bậc từ tốt → xấu: `de_xuat_cho_vay` → `can_nhac` → `tu_choi`.

**Bước 1 — verdict cơ sở theo `risk_label`:**
| risk_label | verdict cơ sở |
|---|---|
| `thap`, `trung_binh` | `de_xuat_cho_vay` |
| `cao` | `can_nhac` |
| `nghiem_trong` | `tu_choi` |

**Bước 2 — hạ một bậc nếu có cờ pháp lý nghiêm trọng đã xác thực:**
Tồn tại flag `group_key='legal'` **và** `verified=true` **và** `severity ≥ cao`
(`cao` hoặc `nghiem_trong`) → verdict tụt **một bậc** (đã ở `tu_choi` thì giữ nguyên).

> Chỉ cờ pháp lý **đã xác thực** mới hạ bậc — tin đồn/chưa xác thực (vd nhóm `reputation`) **không** ảnh hưởng quyết định, chỉ hiển thị cảnh báo. Đồng nhất nguyên tắc Màn 4.

**Bước 3 — `reasons[]`:** mỗi bước trên ghi lại một dòng lý do (nhãn rủi ro, có hạ bậc không, phép tính hạn mức) để truy vết.

## 3. Ví dụ chốt số (khớp `tests/capabilities/test_dashboard_synthesis.py`)
| risk_label | value (đ) | LTV | legal flag | → decision | max_loan (đ) |
|---|---|---|---|---|---|
| trung_binh | 4,000,000,000 | 65 | — | de_xuat_cho_vay | 2,600,000,000 |
| cao | 4,000,000,000 | 55 | — | can_nhac | 2,200,000,000 |
| nghiem_trong | 4,000,000,000 | 45 | — | tu_choi | 1,800,000,000 |
| trung_binh | 4,000,000,000 | 65 | verified, `cao` | **can_nhac** (hạ bậc) | 2,600,000,000 |
| trung_binh | 4,000,000,000 | 65 | verified, `trung_binh` | de_xuat_cho_vay (không hạ) | 2,600,000,000 |
| trung_binh | 4,000,000,000 | 65 | **chưa xác thực**, `cao` | de_xuat_cho_vay (không hạ) | 2,600,000,000 |

## 4. LLM ở đâu (PR2, không thuộc engine này)
Plugin dùng LLM để viết **4 đoạn "Tổng hợp theo từng bước"** + **câu kết luận** cho mượt tiếng Việt —
**bơm sẵn con số/quyết định từ engine**, LLM không được đổi; lỗi LLM → fail-safe về template. Bounded như F3.
