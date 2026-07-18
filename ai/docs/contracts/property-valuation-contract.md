# Contract — `property_valuation` (Chức năng 3: Định giá / Màn 3)

> **Trạng thái:** v1. **Định dạng:** JSON. Service **async + SSE** (POST run → job_id → `/jobs/{id}/stream`).
> **Bản chất:** engine **TÍNH** định giá từ Màn 1 + Màn 2 theo **công thức minh bạch** ([valuation-methodology.md](../valuation-methodology.md)); LLM chỉ lo **1 hệ số cảm tính chặn ±5%**, tách bạch.

## 1. Enum (khớp `models_paa`)
| Trường | Enum DB | Giá trị |
|---|---|---|
| `methods[].method_key` | `valuation_method_key` | `sales_comparison` · `hedonic_ml` · `cost_approach` |
| `confidence_factors[].factor_key` | `confidence_factor_key` | `comp_quantity_quality` · `method_consensus` · `legal_planning_completeness` · `market_volatility` · `comp_similarity` |

## 2. Input
```jsonc
// POST /api/v1/services/property_valuation/run   (body.input)
{ "case_id": "REQ-2026-0001" }   // BẮT BUỘC
→ 200 { "job_id": "...", "status": "pending" }
// rồi: GET /api/v1/jobs/{job_id}/stream?api_key=<key>  → done { result: PropertyValuationOutput }
```
Engine đọc subject (Màn 1 `property_physical_info`) + comparables (Màn 2 `market_comparable`) + badge pháp lý/quy hoạch/tiện ích (`lookup_finding`) + chuỗi `valuation_price_index_point`.

## 3. Output — `PropertyValuationOutput`
```jsonc
{
  "case_id": "REQ-2026-0001",
  "valuation": {                         // 4 KPI tile (↔ valuation_result)
    "proposed_value_vnd", "value_range_low_vnd", "value_range_high_vnd",
    "price_per_sqm_vnd", "confidence_pct", "comparable_count",
    "price_index_period", "price_index_value", "price_index_base",
    "confidence_inference_text"
  },
  "methods": [                           // 3 phương pháp (↔ valuation_method) — bar chart
    { "method_key", "estimated_value_vnd", "weight_pct", "contribution_value_vnd",
      "method_confidence_pct", "inputs":[…breakdown adj_det + adj_llm…],
      "inference_text", "source_label" }
  ],
  "confidence_factors": [                // 5 yếu tố (↔ valuation_confidence_factor)
    { "factor_key", "label", "weight_pct", "score" }
  ],
  "price_index_series": [                // sparkline (↔ valuation_price_index_point)
    { "period_label", "index_value", "display_order" }
  ],
  "subjective_adjustment": {             // 🔴 phần LLM — TÁCH BẠCH
    "value_pct": 0.5, "reason": "…", "source": "llm_inference", "bound_pct": 5.0
  },
  "warnings": []
}
```
- `valuation = null` + `warnings` khi thiếu Màn 1 hoặc không có comparable.
- **Bất biến audit:** bỏ `subjective_adjustment` (=0) → toàn bộ định giá **tái lập từ công thức**.

## 4. Ánh xạ ↔ DB
`valuation`↔`valuation_result` · `methods[]`↔`valuation_method` (theo `method_key`) · `confidence_factors[]`↔`valuation_confidence_factor` (theo `factor_key`) · `price_index_series[]`↔`valuation_price_index_point` (theo `display_order`).

## 5. Minh bạch (yêu cầu nghiệp vụ)
- Mọi con số **xác định**, hệ số ở [config.py](../../src/shb/capabilities/valuation/config.py) (đổi không cần sửa code) — chi tiết [valuation-methodology.md](../valuation-methodology.md).
- **Chỉ `subjective_adjustment`** (hướng nhà/phong thủy) là LLM, **chặn ±5%**, có `reason` + `source="llm_inference"`, **fail-safe** (LLM lỗi → 0%).
