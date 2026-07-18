# Plugin `property_lookup` — Kết quả tra cứu (Màn 2)

Đọc kết quả **7 nguồn tra cứu** + bảng **giao dịch so sánh** của một hồ sơ và trả về
đúng shape tab **"Kết quả tra cứu" (Màn 2)** của PAA.

- **Service id:** `property_lookup` · **sync** (`is_async=False`) · **không nhận file**
- **Contract JSON:** [../../../../../docs/contracts/property-lookup-contract.md](../../../../../docs/contracts/property-lookup-contract.md)
- **Nguồn dữ liệu:** bảng `lookup_finding` + `market_comparable` (models_paa) — dữ liệu demo nạp bằng [../../../../../scripts/load_seed.sh](../../../../../scripts/load_seed.sh), hoặc do một pipeline tra cứu ghi sau này.

## Khác `property_intake` (Function 1)

| | property_intake (F1) | property_lookup (F2) |
|---|---|---|
| Vai trò | Trích xuất file → JSON để BE ghi DB | **Đọc** DB theo `case_id` → JSON |
| Async | `is_async=True` (Celery job, poll) | **`is_async=False`** (trả ngay) |
| ctx cần | `storage_service` | `db_session_factory` |

## Luồng gọi (đồng bộ)

```
POST /api/v1/services/property_lookup/run
Header: X-API-Key: <key>
Body:   { "input": { "case_id": "REQ-2026-2000" } }
→ 200   { "result": PropertyLookupOutput }        # trả ngay, KHÔNG có job_id
```

Không cần poll `/jobs` — vì chỉ đọc DB nên chạy trong request.

## Bên trong

```
run(case_id) → ctx.db_session_factory() → get_lookup_registry().run_all(case_id, session)
             → 7 AdapterResult (+ comparable_sales kèm bảng comparables)
             → assemble PropertyLookupOutput { findings[7], market_comparables[], warnings }
```

- Adapter đọc DB nằm ở [../../../../capabilities/lookup/](../../../../capabilities/lookup/) (`base.py` + `paa/` + `registry.py`). `run_all` đọc **tuần tự** trên 1 session (AsyncSession không phục vụ query đồng thời).
- `findings` LUÔN đủ **7 category** (thiếu data → `status_badge="chua_xac_thuc"`, rỗng).
- `market_comparables` rút từ adapter `comparable_sales`, sắp theo `display_order`.

## 7 category & badge

`market_price` · `planning_zoning` · `legal_status` · `neighborhood_amenity` ·
`environmental_risk` · `liquidity_stat` · `stigma_reputation`
(khớp enum `lookup_category` của models_paa).

Badge: `da_xac_thuc` / `luu_y` / `chua_xac_thuc` (enum `lookup_badge`).
**Lưu ý:** `stigma_reputation` (dư luận/tâm linh) confidence thấp → chỉ cảnh báo tham
khảo, **không dùng để từ chối hồ sơ**.

## Ranh giới

Plugin **chỉ đọc**, không ghi DB, không sinh dữ liệu. Việc ghi `lookup_finding`/
`market_comparable` (seed demo hoặc research pipeline) nằm ngoài plugin — interface
đọc không đổi khi cắm nguồn thật (ARCHITECTURE.md §6.1).

## Test

- Service/integration: [../../../../../tests/plugins/test_property_lookup.py](../../../../../tests/plugins/test_property_lookup.py) — đọc theo `case_id` qua `service.run` và qua registry (SQLite `test_db`, seed nhỏ trong test).
- Adapter đọc DB: [../../../../../tests/capabilities/test_paa_tools.py](../../../../../tests/capabilities/test_paa_tools.py).

```bash
uv run pytest tests/plugins/test_property_lookup.py tests/capabilities/test_paa_tools.py -v
```

Mọi test chạy **offline** trên SQLite in-memory (không cần Postgres/LLM).
