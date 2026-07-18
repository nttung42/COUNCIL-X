# Phương pháp chấm rủi ro tài sản — PAA Risk Engine (Màn 4)

> **Trạng thái:** v0 (draft để duyệt). Chấm **rủi ro của TÀI SẢN đảm bảo** (KHÔNG phải rủi ro tín dụng người vay).
> **Nguyên tắc:** vì điểm rủi ro **quyết định LTV = tiền cho vay**, toàn bộ **100% xác định, audit/tái lập được — KHÔNG LLM**.
> Mọi hệ số ở `risk_config.py` (chỉnh không cần sửa code). Hệ số dưới là **đề xuất mặc định**.

## 0. Đầu vào (chỉ số)
| Nhóm | Nguồn | Chỉ số |
|---|---|---|
| Pháp lý | Màn 2 `legal_status` + Màn 1 `property_legal_info` | badge/độ tin cậy + `current_mortgage_status`, hình thức sở hữu |
| Thanh khoản | Màn 2 `liquidity_stat` | badge/độ tin cậy (đại diện ngày bán TB & tỷ lệ thành công) |
| Biến động giá | Màn 3 `valuation_price_index_point` | độ biến động chuỗi chỉ số giá |
| Vật lý-môi trường | Màn 2 `environmental_risk` + Màn 1 | badge + tuổi công trình (`construction_year`) |
| Danh tiếng-tâm linh | Màn 2 `stigma_reputation` | badge/độ tin cậy (tin đồn) |

## 1. Điểm nền theo badge (dùng chung)
Badge (trạng thái xác thực) → điểm rủi ro nền (0–100, **cao = rủi ro cao**):
```
da_xac_thuc → 20   (đã xác thực/sạch → rủi ro thấp)
luu_y       → 50   (có điểm cần lưu ý → trung bình)
chua_xac_thuc→ 60  (chưa kiểm chứng → bất định → cao hơn)
(không có finding → 50)
+ 10 nếu confidence < 60   (bất định cao → cộng rủi ro)
```

## 2. Điểm từng nhóm (0–100)
```
legal (30%)          = base(legal_finding) + (đang thế chấp? +20) + (sở hữu không "riêng"? +10)   → clamp 0–100
liquidity (25%)      = base(liquidity_finding)
price_volatility (20%) = clamp(round(vol_fraction × 100 × 6), 15, 100)     # vol = pstdev(% thay đổi chỉ số giá)
physical_env (15%)   = base(environmental_finding) + (tuổi > 30? +15)
reputation (10%)     = base(stigma_finding)
```
- "đang thế chấp": `current_mortgage_status` có "thế chấp" nhưng KHÔNG có "chưa"/"tất toán".
- Biến động giá độc lập badge — thuần từ chuỗi chỉ số giá (ổn định → rủi ro thấp).

## 3. Tổng hợp
```
risk_score = round(Σ weightᵢ × scoreᵢ / 100)            # 0..100, cao = rủi ro cao
risk_label = thap(0–20) · trung_binh(21–40) · cao(41–60) · nghiem_trong(>60)   # khớp 4 khung LTV
ltv_proposed_pct = risk_ltv_policy_band(risk_score)     # 0–20→75% · 21–40→65% · 41–60→55% · >60→45%
```
Bảng LTV lấy từ DB `risk_ltv_policy_band` (admin sửa được); engine nhận vào, mặc định trùng bảng seed.

## 4. Flags cần lưu ý
Sinh **flag** cho mỗi nhóm có `score ≥ 50` (ngưỡng cấu hình):
```
{ severity: từ score (thap≤20/trung_binh≤40/cao≤60/nghiem_trong>60),
  title: nhãn nhóm,
  description: template theo nhóm,
  confidence_pct: độ tin cậy finding gốc,
  verified: badge finding == da_xac_thuc }
```
Danh tiếng-tâm linh chưa xác thực → flag `verified=false`, **chỉ cảnh báo tham khảo**.

## 5. Bất biến audit
- Cùng đầu vào → cùng điểm & LTV (không ngẫu nhiên, không LLM).
- Mỗi nhóm kèm `signals[]` giải thích điểm được cộng từ đâu → truy vết được.

## 6. Ảnh hưởng kế hoạch
- `capabilities/risk/engine.py` (§1–4 thuần công thức) + `config.py` (hệ số + bảng LTV mặc định) + test số học chính xác.
- Plugin `property_risk` (async+SSE) đọc Màn 1+2+3 → engine → output Màn 4.
- **Không có module LLM.** (Narrative dùng template.)
