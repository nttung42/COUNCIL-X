# Plugin `property_valuation` — Định giá (Màn 3)

Định giá tài sản theo **công thức minh bạch** từ Màn 1 (đặc điểm) + Màn 2 (giao dịch
so sánh), trả về đúng shape tab **"Định giá" (Màn 3)**.

- **Service id:** `property_valuation` · **async** (`is_async=True`, SSE) · **không nhận file**
- **Contract:** [../../../../../docs/contracts/property-valuation-contract.md](../../../../../docs/contracts/property-valuation-contract.md)
- **Công thức (mock-up):** [../../../../../docs/valuation-methodology.md](../../../../../docs/valuation-methodology.md)
- **SSE:** [../../../../../docs/contracts/sse-streaming.md](../../../../../docs/contracts/sse-streaming.md)

## Nguyên tắc — minh bạch & audit
- Định giá **TÍNH** bằng engine ([../../../../capabilities/valuation/engine.py](../../../../capabilities/valuation/engine.py)): 3 phương pháp (so sánh trực tiếp / hedonic / chi phí) → blend có trọng số → điểm tin cậy 5 yếu tố. **Thuần công thức, tái lập được.**
- Mọi hệ số ở [config.py](../../../../capabilities/valuation/config.py) — chỉnh không cần sửa code.
- **Chỉ một** input cảm tính: `adj_llm` (hướng nhà/phong thủy), **chặn ±5%**, `source="llm_inference"`, **fail-safe** (LLM lỗi → 0%). Bỏ nó → định giá tái lập 100% từ công thức.

## Luồng (async + SSE)
```
POST /api/v1/services/property_valuation/run   body { "input": { "case_id": "REQ-2026-2000" } }
→ 200 { "job_id" }
GET  /api/v1/jobs/{job_id}/stream?api_key=<key>   → progress → done { result: PropertyValuationOutput }
```

## Bên trong
```
run(case_id) → đọc property_physical_info + market_comparable + lookup_finding + price_index (DB)
             → build Subject/Comparable/Context (categorize road/structure, months_since)
             → assess_subjective_adjustment (LLM, ±5%, fail-safe)
             → engine.compute_valuation(subject, comps, context, adj_llm)
             → PropertyValuationOutput { valuation, methods[3], confidence_factors[5],
                                          price_index_series, subjective_adjustment, warnings }
```

## Test
- Engine (số học chính xác): [../../../../../tests/capabilities/test_valuation_engine.py](../../../../../tests/capabilities/test_valuation_engine.py)
- Plugin + subjective: [../../../../../tests/plugins/test_property_valuation.py](../../../../../tests/plugins/test_property_valuation.py)

```bash
uv run pytest tests/capabilities/test_valuation_engine.py tests/plugins/test_property_valuation.py -v
```
Chạy offline trên SQLite; LLM cảm tính được mock.
