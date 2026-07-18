# PAA Mock Data

**DỮ LIỆU MÔ PHỎNG (MOCK)** — toàn bộ file trong thư mục này là dữ liệu synthetic dùng cho demo
hackathon Vietnam AI Innovation Challenge 2026. Không phải số liệu ngân hàng/thị trường thật
(Nguyên tắc VI, `.specify/memory/constitution.md`).

## Khu vực mẫu

- **Phường B, Quận C** — khu vực flagship, dùng cho địa chỉ ví dụ xuyên suốt design doc:
  `Hẻm 45 Nguyễn Văn A, Phường B, Quận C` (`ADDR-88291`), lat/long `10.7756, 106.7019`.
- **Phường Tân Định, Quận 1** — khu vực mẫu thứ 2, giá cao hơn, thanh khoản nhanh hơn.

## File & mapping với lookup tool (data-model.md §5)

| File | Dùng bởi tool | Khoá join |
|---|---|---|
| `transactions.json` | `market_price_lookup` | `lat`/`long` + `radius_km`, lọc theo `property_type` |
| `price_index.json` | `market_price_lookup` (quy đổi giá theo thời gian) | `ward` + `property_segment` |
| `zoning.json` | `planning_zoning_lookup` | `address_id` |
| `legal_records.json` | `legal_status_lookup` | `address_id` |
| `amenities.json` | `neighborhood_amenity_lookup` | `address_id` |
| `address_profiles.json` | `stigma_reputation_lookup` (field `stigma_factors`) + tham khảo `positive_factors`/`negative_factors` | `address_id` |
| `environmental_risk.json` | `environmental_risk_lookup` | `address_id` |
| `liquidity_stats.json` | `liquidity_stat_lookup` | `ward` + `property_segment` |
| `kb_documents/*.md` | `query_knowledge_base` (nạp vào pgvector qua `app/rag/ingest.py`) | frontmatter `doc_type`/`property_type` |

## address_id hiện có (dùng để test — xem `backend/app/mockdata/validate_mockdata.py` khi cần thêm)

`ADDR-88291`, `ADDR-88292`, `ADDR-88293`, `ADDR-88294`, `ADDR-88295` (Phường B, Quận C) —
`ADDR-71001`, `ADDR-71002`, `ADDR-71003` (Phường Tân Định, Quận 1).

## Địa chỉ demo khuyến nghị (khớp toàn bộ ví dụ trong design doc/mockup)

```json
{
  "address": "Hẻm 45 Nguyễn Văn A, Phường B, Quận C",
  "lat": 10.7756, "long": 106.7019,
  "area_m2": 62,
  "property_type": "nha_pho",
  "legal_status_claimed": "so_hong"
}
```

Kỳ vọng kết quả (tham chiếu `quickstart.md`): định giá đề xuất ≈ 4.85 tỷ, độ tin cậy ≈ 78%, điểm
rủi ro tài sản ≈ 34/100 (MEDIUM), LTV đề xuất 65%, có flag `stigma` (tin đồn 2019, `verified=false`)
và flag `environmental` (ngập nhẹ 2022–2023).

## Ghi chú khi mở rộng dữ liệu

- Mọi `address_id`/địa chỉ mới phải xuất hiện nhất quán ở CẢ 6 file theo `address_id`
  (`transactions.json` join theo toạ độ, không theo `address_id`, nên chỉ cần đảm bảo toạ độ nằm
  trong bán kính hợp lý quanh địa chỉ mới).
- `stigma_factors`/`stigma_reputation_lookup` PHẢI luôn có `verified: false` — không được đổi thành
  `true` dù dữ liệu demo có vẻ "chắc chắn" đến đâu (Nguyên tắc III).
- Thêm `kb_documents/*.md` mới cần có frontmatter `doc_type` (`quy_trinh`/`quy_dinh`/`checklist`/
  `case_cu`) và `property_type` để `query_knowledge_base` lọc đúng theo loại tài sản.
