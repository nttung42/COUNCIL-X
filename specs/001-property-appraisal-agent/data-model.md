# Phase 1 Data Model: Property Appraisal Agent (PAA) MVP

Nguồn: Key Entities trong `spec.md` + schema mẫu mục 5 của `SHB_ThamDinhBDS_DesignDoc_2.md`. Mọi
entity tra cứu (không phải entity nội bộ như CaseSession/TraceEvent) PHẢI có `confidence` và
`source_type` theo Nguyên tắc II của constitution.

## 1. PropertyAppraisalRequest (input, không lưu bảng riêng — nhúng trong CaseSession)

| Field | Type | Ghi chú |
|---|---|---|
| request_id | string | vd. `REQ-2026-0001`, unique |
| subject_property.address | string | bắt buộc |
| subject_property.lat / long | float | dùng cho lookup theo bán kính |
| subject_property.area_m2 | float | > 0 |
| subject_property.property_type | enum(`nha_pho`, `dat_nen`, `chung_cu`, `bds_thuong_mai`) | MVP ưu tiên `nha_pho` |
| subject_property.legal_status_claimed | enum(`so_hong`, `so_do`, `giay_tay`, `khac`) | tự khai báo, đối chiếu với `legal_status_lookup` |
| loan_context.requested_amount | integer (VND) | > 0 |
| loan_context.purpose | string | vd. `the_chap_vay_von` |

## 2. ComparableTransaction

| Field | Type | Validation |
|---|---|---|
| transaction_id | string | unique, vd. `TXN-000123` |
| address | string | |
| lat, long | float | |
| area_m2 | float | > 0 |
| frontage_m | float | mặt tiền (m) |
| alley_width_m | float\|null | null nếu mặt tiền đường lớn |
| floors | int | ≥ 1 |
| legal_status | enum | cùng tập giá trị với `legal_status_claimed` |
| transaction_type | enum(`sold`, `listed`) | |
| price_total | integer (VND) | > 0 |
| price_per_m2 | integer (VND) | = price_total / area_m2 (làm tròn) |
| transaction_date | date (YYYY-MM-DD) | |
| distance_from_subject_km | float | ≥ 0, dùng để lọc theo `radius_km` |
| source_type | enum(`mock`,`verified`,`unverified_rumor`) | MVP luôn `mock` |
| confidence | float [0,1] | mock cố định theo độ mới của giao dịch |

## 3. PriceIndexSeries

| Field | Type | Ghi chú |
|---|---|---|
| ward | string | khớp với khu vực của subject_property |
| series[] | array | mỗi phần tử: `{period: "YYYY-Qn", index: float}` |
| series[].index | float | gốc 100.0 tại kỳ base |

**Business rule**: `giá_quy_đổi = giá_giao_dịch × (index[kỳ_hiện_tại] / index[kỳ_giao_dịch])`
(công thức mục 4.2 design doc).

## 4. AddressProfile

| Field | Type | Ghi chú |
|---|---|---|
| address_id | string | unique, vd. `ADDR-88291` |
| positive_factors[] | array of `{type, detail, confidence}` | nguồn `amenity_lookup`, `zoning_lookup` |
| negative_factors[] | array of `{type, detail, confidence}` | nguồn `environmental_risk_lookup`, `legal_status_lookup` |
| stigma_factors[] | array of `{type, detail, confidence, verified: bool}` | **PHẢI tách riêng field này**, `verified` luôn `false` trong MVP (Nguyên tắc III) |

## 5. Lookup Tool Output Envelope (áp dụng cho cả 7 adapter)

Mọi tool trong Research Agent trả về bọc ngoài dạng chuẩn để Valuation/Risk Engine xử lý đồng nhất:

```json
{
  "tool_name": "market_price_lookup",
  "status": "ok",            // ok | partial | error
  "confidence": 0.85,
  "source_type": "mock",
  "data": { "...": "payload riêng theo từng tool" },
  "warning": null              // string nếu status = partial/error
}
```

- `planning_zoning_lookup.data`: `{ zoning_status, is_planned_overlay: bool, road_widening_plan }`
- `legal_status_lookup.data`: `{ legal_status, has_dispute: bool, mortgaged_elsewhere: bool }`
- `neighborhood_amenity_lookup.data`: `{ amenities: [{type, name, distance_m}] }`
- `stigma_reputation_lookup.data`: `{ rumors: [{detail, year, verified: false}] }` (verified luôn false)
- `environmental_risk_lookup.data`: `{ flood_risk, landslide_risk, pollution_risk, notes }`
- `liquidity_stat_lookup.data`: `{ avg_days_on_market, success_rate_pct }`

## 6. ValuationResult

| Field | Type | Validation |
|---|---|---|
| estimated_value | integer (VND) | > 0, = blend của 3 phương pháp |
| value_range.low / high | integer (VND) | low < estimated_value < high |
| value_per_m2 | integer (VND) | |
| confidence_score | float [0,1] | phụ thuộc số lượng comparables dùng |
| methodology_breakdown.comparable_approach | integer (VND) | |
| methodology_breakdown.hedonic_model | integer (VND) | |
| methodology_breakdown.cost_approach | integer (VND) | |
| comparables_used | int | ≥ 0; nếu 0 → confidence_score MUST < 0.4 và kèm flag "không đủ dữ liệu so sánh" |
| time_adjustment_index_period | string | vd. `2026-Q2` |
| adjustment_notes[] | array of string | giải thích điều chỉnh (explainability) |

## 7. AssetRiskAssessment

| Field | Type | Validation |
|---|---|---|
| asset_risk_score | int [0,100] | weighted sum của 5 risk_group_scores |
| risk_tier | enum(`LOW`,`MEDIUM`,`HIGH`) | LOW ≤30, MEDIUM 31–60, HIGH >60 |
| recommended_ltv_cap | float (0,1] | vd. 0.65 |
| risk_group_scores | object | `{legal: int, liquidity: int, price_volatility: int, physical_environmental: int, reputation_stigma: int}`, mỗi giá trị [0,100] |
| flags[] | array of `{type, severity(low\|medium\|high), detail, confidence, action?, verified?}` | flag `type=stigma` MUST có `verified=false` |
| recommended_conditions[] | array of string | vd. "mua bảo hiểm tài sản" |

**Business rule (Nguyên tắc III)**: `risk_group_scores.reputation_stigma` được tính từ
`stigma_factors` nhưng CHỈ đóng góp tối đa 10% trọng số tổng — không được dùng riêng để set
`risk_tier = HIGH` hay tự động sinh flag "từ chối".

## 8. ChecklistItem

| Field | Type | Ghi chú |
|---|---|---|
| item_id | string | |
| text | string | |
| property_type_scope | array of enum | loại tài sản áp dụng mục này |
| is_checked | bool | mặc định false, trừ mục tự động xác thực được (vd. sổ hồng hợp lệ) |
| related_flag_type | string\|null | liên kết tới `AssetRiskAssessment.flags[].type` nếu có |

## 9. AppraisalReportDraft

| Field | Type | Ghi chú |
|---|---|---|
| sections.property_info | string (markdown) | |
| sections.valuation | string (markdown) | |
| sections.risk_and_ltv | string (markdown) | |
| signature_block | string | luôn chứa 2 dòng checkbox trống: thẩm định viên + chuyên viên tín dụng |

## 10. CaseSession (bảng Postgres)

| Column | Type | Ghi chú |
|---|---|---|
| id (PK) | uuid | |
| request_id | text unique | |
| status | enum(`processing`,`completed`,`cancelled`) | |
| subject_property_json | jsonb | snapshot PropertyAppraisalRequest |
| lookup_result_json | jsonb\|null | |
| valuation_result_json | jsonb\|null | |
| risk_result_json | jsonb\|null | |
| checklist_json | jsonb\|null | |
| report_draft_json | jsonb\|null | |
| chat_history_json | jsonb | array message `{role, content, created_at}` |
| requires_human_verification | bool | |
| created_at, updated_at | timestamptz | |

**State transitions**: `processing → completed` (pipeline chạy xong) hoặc `processing → cancelled`
(người dùng huỷ). Không có transition ngược từ `completed`/`cancelled` về `processing` trong MVP —
tạo request mới nếu cần chạy lại.

## 11. TraceEvent (bảng Postgres)

| Column | Type | Ghi chú |
|---|---|---|
| id (PK) | uuid | |
| case_id (FK → CaseSession.id) | uuid | |
| step_name | text | vd. "7 nguồn tra cứu chạy song song" |
| component | text | vd. `research_agent`, `valuation_agent` |
| t_offset_seconds | float | thời gian tương đối từ lúc case tạo, dùng vẽ timeline |
| input_summary | text | |
| output_summary | text | |
| created_at | timestamptz | |

## 12. KbChunk (bảng Postgres + pgvector, RAG)

| Column | Type | Ghi chú |
|---|---|---|
| id (PK) | uuid | |
| source_doc | text | vd. `quy-trinh-tham-dinh.md` |
| chunk_text | text | |
| embedding | vector(N) | N theo model embedding OpenAI-compatible đang dùng |
| metadata_json | jsonb | `{doc_type: "quy_trinh"\|"quy_dinh"\|"checklist"\|"case_cu", property_type?}` |

## Relationships (tóm tắt)

```
CaseSession 1---N TraceEvent
CaseSession 1---1 ValuationResult (nhúng jsonb)
CaseSession 1---1 AssetRiskAssessment (nhúng jsonb)
CaseSession 1---N ChecklistItem (nhúng jsonb array)
AssetRiskAssessment.flags[type=stigma] ---- AddressProfile.stigma_factors (nguồn dữ liệu)
KbChunk N---1 (không FK) tham chiếu tới property_type qua metadata_json khi Advisory Agent query
```
