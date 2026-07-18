# Phương pháp định giá — PAA Valuation Engine (Màn 3)

> **Trạng thái:** v0 (draft để duyệt) — mock-up **công thức định giá minh bạch**.
> **Nguyên tắc:** mọi con số định giá **tái lập được, audit được**; phần **cảm tính** (hướng nhà/phong thủy) do **LLM** quyết định **có biên ±5%** và **đánh dấu tách bạch**.
> Mọi hệ số dưới đây là **đề xuất mặc định** — để trong 1 file config (`valuation_config.py`) để chỉnh theo nghiệp vụ SHB **không cần sửa code**.

---

## 0. Đầu vào (chỉ số ảnh hưởng công thức)

| Nhóm | Nguồn | Chỉ số |
|---|---|---|
| Tài sản | Màn 1 `property_physical_info` | `land_area_sqm`, `floor_area_sqm`, số tầng (từ `num_floors_desc`), `frontage_m`, `depth_m`, `alley_width_m`, `road_type_desc`, `construction_year`, `structure_material`, `house_direction` |
| Giao dịch so sánh | Màn 2 `market_comparable` | `price_per_sqm_vnd` (đã quy đổi thời gian), `distance_km`, `area_sqm`, `transaction_date` |
| Bối cảnh | Màn 2 `lookup_finding` | badge/độ tin cậy: quy hoạch, pháp lý, thanh khoản, môi trường; chuỗi `valuation_price_index_point` |

**Diện tích tính giá (`effective_area`)**: mặc định **`land_area_sqm`** (nhà phố VN định giá theo m² đất). `floor_area_sqm` dùng cho phương pháp chi phí.

> 🔴 **Phần CẢM TÍNH (LLM) — nêu rõ:** chỉ **`adj_llm`** (hướng nhà, phong thủy, vị trí góc/nở hậu…). Bị **chặn ±5%**, có lý do + `source="llm_inference"`, tách khỏi công thức. Mọi chỉ số khác là **xác định**.

---

## 1. Phương pháp ① — So sánh trực tiếp (`sales_comparison`)

### 1.1 Giá/m² tham chiếu (xác định)
Trọng số tương đồng mỗi giao dịch i (gần hơn / cùng diện tích / mới hơn → nặng hơn):
```
w_dist_i = 1 / (1 + distance_km_i / D0)              D0 = 1.0 km
w_area_i = 1 / (1 + |area_i − land_area| / A0)       A0 = 30 m²
w_time_i = 1 / (1 + months_since(txn_date_i) / T0)   T0 = 12 tháng
w_sim_i  = w_dist_i × w_area_i × w_time_i
base_ppm = Σ(price_per_sqm_i × w_sim_i) / Σ w_sim_i
```

### 1.2 Điều chỉnh đặc điểm (xác định — bảng tra)
| Hệ số | Điều kiện | Giá trị |
|---|---|---|
| `a_road` (lộ giới) | mặt tiền đường lớn | +0.05 |
| | hẻm ô tô ≥3.5m | 0.00 (chuẩn) |
| | hẻm xe máy 2–3.5m | −0.04 |
| | hẻm nhỏ <2m | −0.08 |
| `a_floors` | +0.02 / tầng trên tầng 1 | tối đa +0.08 |
| `a_age` (tuổi=năm nay−XD) | <5 | +0.03 |
| | 5–15 | 0.00 |
| | 15–30 | −0.05 |
| | >30 | −0.10 |
| `a_structure` | BTCT/kiên cố | 0.00 |
| | bán kiên cố | −0.03 |
| | nhà cấp 4 | −0.06 |
```
adj_det = clamp(a_road + a_floors + a_age + a_structure, −0.20, +0.15)
```

### 1.3 Điều chỉnh cảm tính (LLM, ±5%)
```
adj_llm = LLM(house_direction, phong_thủy, vị trí) ∈ [−0.05, +0.05]   # kèm reason, source=llm_inference
final_ppm  = base_ppm × (1 + adj_det + adj_llm)
value_ss   = final_ppm × land_area_sqm
```

---

## 2. Phương pháp ② — Hedonic (`hedonic_ml`) · xác định, không cảm tính
Mô hình tuyến tính (mock, β cấu hình được / hồi quy nhanh trên comparables):
```
value_hed = base_ppm × land_area × (1 + Σ βk·featurek)
  β_floors    · (num_floors − 1)                     β_floors  = +0.015
  β_frontage  · (frontage_m − 3)                      β_frontage= +0.008
  β_age       · max(0, tuổi − 10)                     β_age     = −0.004
  β_amenity   · (amenity_conf − 0.5)                  β_amenity = +0.10
  (chặn tổng Σβ·f trong [−0.15, +0.15])
```

---

## 3. Phương pháp ③ — Chi phí (`cost_approach`) · xác định
```
unit_land_price = base_ppm                                  # giá đất/m² tham chiếu
land_value      = land_area × unit_land_price
unit_build_cost = { BTCT: 7,000,000 ; bán kiên cố: 4,500,000 ; cấp 4: 2,500,000 } đ/m²
depreciation    = max(0.40, 1 − tuổi × 0.015)               # khấu hao 1.5%/năm, sàn 40%
building_value  = floor_area × unit_build_cost × depreciation
value_cost      = land_value + building_value
```

---

## 4. Kết hợp (ensemble) · xác định
Trọng số động theo **số lượng & chất lượng** comparable:
```
n = số comparable ;  q̄ = trung bình w_sim
w_sales = clamp(0.40 + 0.05·min(n, 6), 0.40, 0.70)
w_rest  = 1 − w_sales                → w_hed = 0.55·w_rest ;  w_cost = 0.45·w_rest
proposed_value = w_sales·value_ss + w_hed·value_hed + w_cost·value_cost
```
Khoảng giá:
```
dispersion = stdev([value_ss, value_hed, value_cost]) / mean
spread     = clamp(0.03 + 0.5·dispersion + 0.1·(1 − confidence), 0.03, 0.15)
value_low  = proposed × (1 − spread) ;  value_high = proposed × (1 + spread)
price_per_sqm = proposed / land_area
```

---

## 5. Độ tin cậy (5 yếu tố có trọng số) · xác định
| factor_key | Trọng số | score (0–100) tính từ |
|---|---|---|
| `comp_quantity_quality` | 28% | số comparable & q̄ (≥6 comp tốt → ~90; 1–2 comp → ~40) |
| `method_consensus` | 26% | 100·(1 − dispersion), clamp |
| `legal_planning_completeness` | 18% | badge pháp lý + quy hoạch (da_xac_thuc→cao) |
| `market_volatility` | 17% | độ ổn định chuỗi `price_index` (biến động thấp→cao) |
| `comp_similarity` | 11% | q̄ × 100 |
```
confidence_pct = round(Σ weightᵢ · scoreᵢ)
```

---

## 6. Tách bạch phần LLM trong output
- `methods[sales_comparison].inputs`: liệt kê **breakdown `adj_det`** (từng hệ số) + **`adj_llm`** riêng.
- Thêm khối **`subjective_adjustment`**: `{ value_pct, reason, source: "llm_inference", bound: 0.05 }`.
- `confidence_inference_text`: giải thích tổng.
- **Kiểm tra bất biến:** nếu bỏ `adj_llm` (=0) thì toàn bộ định giá **tái lập chính xác** từ công thức → audit được.

---

## 7. Ảnh hưởng tới kế hoạch F3
- `capabilities/valuation/engine.py`: implement §1–5 (thuần công thức, test số học chính xác).
- LLM chỉ gọi **1 lần** cho `adj_llm` (prompt nêu rõ chỉ định hệ số ∈[−5%,+5%] + lý do); fail → `adj_llm=0` (fail-safe, định giá vẫn chạy bằng công thức).
- Ghi kết quả vào `valuation_result/method/confidence_factor/price_index_point` (hoặc trả JSON — chốt sau).
- Doc này = nguồn sự thật; hệ số nằm ở `valuation_config.py`.

> **Cần bạn duyệt/chỉnh:** các bảng hệ số ở §1.2, §2, §3, §4, §5 (giá trị mặc định là đề xuất). Sau khi chốt, tôi code engine đúng theo doc.
