---
name: paa-lookup-tools-impl
description: "Cách implement 7 lookup tool của PAA Research Agent — envelope format bắt buộc, cách đọc từng file mock data, và quy tắc xử lý địa chỉ không có dữ liệu. Dùng khi viết code cho backend/app/tools/{market_price,planning_zoning,legal_status,neighborhood_amenity,stigma_reputation,environmental_risk,liquidity_stat}_lookup.py."
---

# Implement PAA Lookup Tools

## Envelope bắt buộc (mọi tool trả về đúng format này)

```python
{
    "tool_name": "market_price_lookup",
    "status": "ok",            # "ok" | "partial" | "error"
    "confidence": 0.85,          # 0..1, lấy trực tiếp/trung bình từ mock data đã có field confidence
    "source_type": "mock",       # luôn "mock" trong MVP — KHÔNG đổi thành "verified" dù dữ liệu có vẻ chắc chắn
    "data": { ... },             # payload riêng — xem bảng dưới
    "warning": None,              # string nếu status != "ok", giải thích lý do (vd. "không tìm thấy giao dịch trong bán kính yêu cầu")
}
```

`status="partial"` khi tìm được MỘT PHẦN dữ liệu (vd. có địa chỉ nhưng thiếu 1 vài field);
`status="error"` CHỈ dùng khi input không hợp lệ (vd. thiếu `lat`/`long`), không dùng cho "không có
dữ liệu" — trường hợp đó luôn là `partial` kèm `data` rỗng/mặc định, để không chặn pipeline
(constitution Nguyên tắc IV, spec.md Edge Case).

## Mapping tool ↔ file mock data ↔ shape của `data`

| Tool | File đọc | `data` payload |
|---|---|---|
| `market_price_lookup(address, lat, long, radius_km, period_from, period_to, property_type)` | `backend/app/mockdata/transactions.json` + `price_index.json` | `{comparables: [ComparableTransaction quy đổi giá theo index], price_index_period_used}` — lọc `distance_from_subject_km <= radius_km`, sort theo distance tăng dần |
| `planning_zoning_lookup(address, cadastral_id)` | `zoning.json` | `{zoning_status, is_planned_overlay, road_widening_plan}` — tìm theo `address_id` suy ra từ địa chỉ khớp gần đúng chuỗi, hoặc nhận thẳng `address_id` nếu caller truyền vào |
| `legal_status_lookup(address, owner_id)` | `legal_records.json` | `{legal_status, has_dispute, mortgaged_elsewhere, notes}` |
| `neighborhood_amenity_lookup(lat, long, radius_km)` | `amenities.json` | `{amenities: [...]}` — lọc theo địa chỉ gần lat/long nhất trong danh sách |
| `stigma_reputation_lookup(address)` | `address_profiles.json` field `stigma_factors` | `{rumors: [{detail, confidence, verified: false}]}` — **luôn ép `verified=False` dù mock data có ghi gì** |
| `environmental_risk_lookup(lat, long)` | `environmental_risk.json` | `{flood_risk, landslide_risk, pollution_risk, notes}` |
| `liquidity_stat_lookup(address hoặc ward, property_type)` | `liquidity_stats.json` | `{avg_days_on_market, success_rate_pct}` — match theo `ward` + `property_segment` |

Vì mock data hiện tại join theo `address_id` (zoning/legal/amenities/environmental) hoặc theo
toạ độ (`transactions.json`, `address_profiles.json`), cách đơn giản nhất để tra theo `address`
đầu vào: viết 1 helper `_find_address_id(address_or_latlong)` dùng so khớp gần đúng chuỗi địa chỉ
HOẶC khoảng cách toạ độ nhỏ nhất tới các entry trong `address_profiles.json` (đã có `lat`/`long`
cho từng `address_id`) — dùng chung helper này cho cả 5 tool cần `address_id`
(zoning/legal/amenity/stigma/environmental) để tránh lặp code, có thể đặt trong
`backend/app/tools/_mockdata_utils.py`.

## Công thức quy đổi giá theo thời gian (market_price_lookup)

```
giá_quy_đổi = giá_giao_dịch × (index[kỳ_hiện_tại] / index[kỳ_giao_dịch])
```

`kỳ_hiện_tại` = kỳ mới nhất có trong `price_index.json` cho đúng `ward` + `property_segment`
(vd. `2026-Q2`). `kỳ_giao_dịch` suy ra từ `transaction_date` (vd. `2025-11-10` → `2025-Q4`).

## Khi không tìm thấy dữ liệu cho địa chỉ

Trả `status="partial"`, `confidence <= 0.3`, `data` chứa mảng rỗng/giá trị mặc định trung tính
(không phải `null` toàn bộ, để tránh lỗi ở tầng gọi), và `warning` mô tả rõ — vd.
`"Không tìm thấy giao dịch so sánh nào trong bán kính 2km quanh toạ độ đã cho — cần thẩm định viên
bổ sung dữ liệu."` Đây chính là cơ chế thoả mãn SC-005 trong spec.md.
