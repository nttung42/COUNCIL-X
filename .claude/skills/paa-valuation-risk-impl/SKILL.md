---
name: paa-valuation-risk-impl
description: "Công thức chi tiết cho calculate_valuation (3 phương pháp blend) và calculate_asset_risk_score (5 nhóm rủi ro có trọng số) của PAA. Dùng khi viết code cho backend/app/tools/calculate_valuation.py và calculate_asset_risk_score.py."
---

# Implement PAA Valuation & Risk Engines

## calculate_valuation — 3 phương pháp + blend

1. **So sánh trực tiếp** (trọng số chính, ~50%): với mỗi `ComparableTransaction` đã quy đổi giá
   theo thời gian (nhận từ `market_price_lookup`, đã có `price_per_m2` quy đổi), điều chỉnh thêm:
   - diện tích khác biệt: hệ số nhỏ theo economies-of-scale (căn nhỏ hơn thường giá/m² cao hơn)
   - `alley_width_m` hẹp hơn subject: trừ ~1-2%/mét hẹp hơn; mặt tiền đường lớn (`alley_width_m
     is None`): cộng ~5-8%
   - `legal_status` khác `so_hong`: trừ 10-15%
   - Giá trị = trung bình có trọng số (trọng số = 1/distance_from_subject_km, giao dịch gần hơn
     ảnh hưởng nhiều hơn) của `price_per_m2` đã điều chỉnh × `area_m2` của subject.
2. **Hedonic (ML-assisted, đơn giản hoá cho MVP)**: hồi quy tuyến tính đơn giản hoặc trọng số thủ
   công trên feature {khoảng cách trung tâm, diện tích, mặt tiền, tuổi nhà (ước lượng từ floors),
   mật độ tiện ích (đếm từ `neighborhood_amenity_lookup`)} — cho MVP, có thể dùng công thức
   heuristic: `giá_hedonic = giá_so_sánh_trực_tiếp × (1 + tổng hệ số điều chỉnh nhỏ theo tiện ích)`,
   miễn là code có docstring giải thích rõ đây là xấp xỉ heuristic thay ML thật (ghi rõ trong
   report cuối — không cần train model thật cho hackathon).
3. **Chi phí xây dựng**: `giá_đất_ước_lượng (theo so sánh, trừ phần công trình) + đơn_giá_xây_dựng
   × diện_tích_sàn × hệ_số_khấu_hao_theo_tuổi`. Đơn giá xây dựng mock: 8-12 triệu/m² tuỳ property_type
   (nhà phố cao hơn đất nền/chung cư phần xây thô).

**Blend**: trọng số mặc định {comparable: 0.5, hedonic: 0.3, cost: 0.2}; nếu `comparables_used < 3`
→ tăng trọng số `cost` lên và giảm `comparable` (vì so sánh trực tiếp kém tin cậy khi ít dữ liệu).

**confidence_score**: tăng theo số `comparables_used` (vd. `min(0.95, 0.3 + 0.08 * comparables_used)`)
và giảm nếu độ lệch giữa 3 phương pháp lớn (>15% so với giá trị blend).

**value_range**: `[estimated_value * (1 - spread), estimated_value * (1 + spread)]` với `spread`
tỷ lệ nghịch với `confidence_score` (vd. `spread = 0.15 * (1 - confidence_score) + 0.05`).

Ví dụ đối chiếu (địa chỉ "Hẻm 45 Nguyễn Văn A", dùng dữ liệu mock hiện có): kỳ vọng
`estimated_value` xấp xỉ 4.7–5.0 tỷ, `confidence_score` xấp xỉ 0.75–0.8, khớp với ví dụ trong
design doc gốc (4.85 tỷ / 78%) — không cần trùng khớp tuyệt đối, chỉ cần cùng bậc độ lớn hợp lý.

## calculate_asset_risk_score — 5 nhóm rủi ro có trọng số

```
asset_risk_score = 0.30*legal + 0.25*liquidity + 0.20*price_volatility
                  + 0.15*physical_environmental + 0.10*reputation_stigma
```

Mỗi nhóm điểm 0-100 (100 = rủi ro cao nhất):

- **legal** (30%): 0 nếu `has_dispute=False` và `mortgaged_elsewhere=False` và
  `legal_status="so_hong"`; +40 nếu `mortgaged_elsewhere=True`; +50 nếu `has_dispute=True`; +20 nếu
  `is_planned_overlay=True`. Cap tại 100.
- **liquidity** (25%): dựa `avg_days_on_market` (vd. `min(100, avg_days_on_market)` scaled) và
  nghịch với `success_rate_pct` (vd. `100 - success_rate_pct` rồi trung bình 2 yếu tố).
- **price_volatility** (20%): độ lệch chuẩn của `price_per_m2` giữa các comparables đã dùng, chuẩn
  hoá về thang 0-100 (biến thiên lớn → điểm cao).
- **physical_environmental** (15%): dựa `flood_risk`/`landslide_risk`/`pollution_risk` — mỗi mức
  `none`→0, `low`/`low_recorded`→30, `medium`→60, `high`→90; lấy max của 3 yếu tố.
- **reputation_stigma** (10%): dựa số lượng và `confidence` trong `stigma_factors`/`rumors` —
  KHÔNG CÓ tin đồn → 0; có tin đồn → điểm tỷ lệ thuận với `confidence` gốc của tin đồn (vd.
  `min(70, confidence_tin_đồn * 100 * 0.8)`) — dù điểm nhóm này cao, trọng số 10% đảm bảo không thể
  tự nó đẩy `asset_risk_score` tổng vượt ngưỡng HIGH một mình (đây chính là cơ chế "cô lập" theo
  Nguyên tắc III — hãy viết 1 unit test nhỏ/ví dụ trong docstring chứng minh: dù
  `reputation_stigma=100`, nếu 4 nhóm còn lại đều =0 thì `asset_risk_score` tối đa chỉ = 10).

**risk_tier**: LOW ≤30, MEDIUM 31-60, HIGH >60. **recommended_ltv_cap**: LOW→0.70, MEDIUM→0.65,
HIGH→0.50.

**flags[]**: sinh 1 flag cho mỗi yếu tố đáng chú ý (has_dispute, mortgaged_elsewhere, flood_risk
khác none, mọi rumor trong stigma_factors). Flag từ `stigma_factors` PHẢI có `verified=false`
truyền nguyên từ input, KHÔNG được set lại thành `true`.

**recommended_conditions[]**: sinh gợi ý theo flag (vd. có flood_risk → "mua bảo hiểm tài sản"; có
rumor → "yêu cầu khảo sát thực địa xác minh").
