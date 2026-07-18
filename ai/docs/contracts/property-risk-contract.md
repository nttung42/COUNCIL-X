# Contract — `property_risk` (Chức năng 4: Rủi ro / Màn 4)

> **Trạng thái:** v1. **Định dạng:** JSON. Service **async + SSE**. **API public** (không cần X-API-Key/register).
> **Bản chất:** engine **TÍNH** rủi ro **của tài sản đảm bảo** (không phải rủi ro tín dụng người vay) theo **công thức 100% xác định** ([risk-methodology.md](../risk-methodology.md)) — **không LLM**. Điểm rủi ro → **LTV đề xuất**.

## 1. Enum (khớp `models_paa`)
| Trường | Enum DB | Giá trị |
|---|---|---|
| `groups[].group_key` | `risk_group_key` | `legal` · `liquidity` · `price_volatility` · `physical_environment` · `reputation` |
| `assessment.risk_label`, `flags[].severity` | `severity_level` | `thap` · `trung_binh` · `cao` · `nghiem_trong` |

## 2. Input & gọi (public)
```
POST /api/v1/services/property_risk/run       body { "input": { "case_id": "REQ-2026-0001" } }
→ 200 { "job_id": "...", "status": "pending" }          # KHÔNG cần X-API-Key
GET  /api/v1/jobs/{job_id}/stream               (SSE)   # done { result: PropertyRiskOutput }
```
Engine đọc: Màn 1 `property_legal_info` (thế chấp/sở hữu) + `property_physical_info` (tuổi) · Màn 2 `lookup_finding` (legal/liquidity/environmental/stigma) · Màn 3 `valuation_price_index_point` · bảng `risk_ltv_policy_band`.

## 3. Output — `PropertyRiskOutput`
```jsonc
{
  "case_id": "REQ-2026-0001",
  "assessment": {                        // ↔ risk_assessment_result (meter + LTV)
    "risk_score": 37,                    // 0..100, CAO = rủi ro cao
    "risk_label": "trung_binh",          // thap(0–20)/trung_binh(21–40)/cao(41–60)/nghiem_trong(>60)
    "ltv_proposed_pct": 65,              // từ risk_ltv_policy_band
    "risk_inference_text": "…"
  },
  "groups": [                            // 5 nhóm (↔ risk_group) — bar chart
    { "group_key", "label", "weight_pct", "score",
      "signals": ["…giải thích điểm được cộng từ đâu…"],   // AUDIT
      "source_confidence", "verified" }
  ],
  "flags": [                             // "Flags cần lưu ý" (↔ risk_flag)
    { "severity", "title", "description", "confidence_pct", "verified" }
  ],
  "ltv_policy_bands": [                   // 4 khung LTV (↔ risk_ltv_policy_band)
    { "min_score", "max_score", "max_ltv_pct", "label" }
  ],
  "warnings": []
}
```
- `assessment = null` + `warnings` khi thiếu Màn 1.
- Thiếu Màn 2 → vẫn tính (điểm nhóm mặc định trung bình) + `warnings`.

## 4. Ánh xạ ↔ DB
`assessment`↔`risk_assessment_result` · `groups[]`↔`risk_group` (theo `group_key`) · `flags[]`↔`risk_flag` · `ltv_policy_bands[]`↔`risk_ltv_policy_band`.

## 5. Minh bạch (yêu cầu nghiệp vụ)
- Điểm 5 nhóm + risk_score + LTV **100% xác định, audit/tái lập được**. Mỗi nhóm kèm `signals[]` truy vết.
- Trọng số & bảng LTV ở [config.py](../../src/shb/capabilities/risk/config.py) + DB `risk_ltv_policy_band` (admin sửa được). Chi tiết [risk-methodology.md](../risk-methodology.md).
- **Không LLM** — điểm rủi ro quyết định LTV = tiền.
- Nhóm `reputation` (danh tiếng/tâm linh) chưa xác thực → flag `verified=false`, chỉ cảnh báo, không dùng để từ chối.
