# Contract — `property_lookup` (Chức năng 2: Kết quả tra cứu / Màn 2)

> **Trạng thái:** v1 — bản chốt để AI ↔ FE/BE thống nhất.
> **Định dạng:** JSON. Plugin **ĐỌC DB** (`lookup_finding` + `market_comparable`) theo `case_id` và trả JSON Màn 2 — không sinh dữ liệu, không ghi DB.
> **Đối tượng dùng:** Frontend (render tab "Kết quả tra cứu"), Backend (proxy API).

Khác Function 1 (`property_intake` trả JSON để BE ghi DB), Function 2 **đọc dữ liệu đã có** trong DB (seed demo `apps/datasource/paa_seed_data.sql`, hoặc do một pipeline tra cứu ghi sau này) qua tầng `shb.capabilities.lookup`. Service chạy **async** (`is_async=True`) để dùng **chung luồng SSE** với các function khác — nhưng vì chỉ đọc DB nên job xong gần như tức thì. Xem [SSE contract](sse-streaming.md).

---

## 1. Enum (đồng bộ tuyệt đối với `models_paa` / DB)

| Trường JSON | Enum DB (`models_paa`) | Giá trị |
|---|---|---|
| `findings[].category` | `lookup_category` | `market_price` · `planning_zoning` · `legal_status` · `neighborhood_amenity` · `environmental_risk` · `liquidity_stat` · `stigma_reputation` |
| `findings[].status_badge` | `lookup_badge` | `da_xac_thuc` · `luu_y` · `chua_xac_thuc` |

Ý nghĩa `status_badge` (badge 3 màu trên card):
- `da_xac_thuc` — đã xác thực (nguồn tin cậy).
- `luu_y` — có điểm cần lưu ý.
- `chua_xac_thuc` — chưa kiểm chứng. Đặc biệt `stigma_reputation` (dư luận/tâm linh) thường confidence thấp + badge này → **chỉ mang tính cảnh báo tham khảo, KHÔNG dùng để từ chối hồ sơ**.

---

## 2. Input

```jsonc
// POST /api/v1/services/property_lookup/run   (body.input)
{
  "case_id": "REQ-2026-0001"   // BẮT BUỘC. Hồ sơ cần đọc kết quả tra cứu
}
```

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `case_id` | `string` | ✔ | Mã hồ sơ (`REQ-...`). Subject/data lấy từ DB theo case_id. |

**Gọi & nhận (async + SSE):**
```
POST /api/v1/services/property_lookup/run
Header: X-API-Key: <key>
Body: { "input": { "case_id": "REQ-2026-0001" } }
→ 200 { "job_id": "...", "status": "pending" }

GET /api/v1/jobs/{job_id}/stream?api_key=<key>   (SSE)
→ done { "status": "completed", "result": PropertyLookupOutput }
```

---

## 3. Output — `PropertyLookupOutput`

```jsonc
{
  "case_id": "REQ-2026-0001",
  "findings": [ LookupFinding ],        // LUÔN đủ 7 phần tử (mỗi category 1 card)
  "market_comparables": [ MarketComparable ],  // bảng "Giao dịch so sánh khu vực"
  "warnings": [ "..." ]                 // cảnh báo mức hồ sơ (vd. case chưa có dữ liệu)
}
```

### 3.1 `LookupFinding` → 1 dòng bảng `lookup_finding`

```jsonc
{
  "category": "planning_zoning",        // enum lookup_category
  "tool_name": "planning_zoning_lookup",
  "title": "Quy hoạch",
  "status_badge": "da_xac_thuc",        // enum lookup_badge
  "raw_findings": [                      // list bullet "Dữ liệu tra cứu được"
    "Không nằm trong khu vực quy hoạch treo.",
    "Lộ giới dự kiến mở rộng lên 8m theo đồ án 1/2000."
  ],
  "inference_text": "Không có yếu tố quy hoạch bất lợi...",  // "💡 Nhận định của PAA"
  "source_label": "planning_zoning_lookup",
  "confidence_pct": 93                   // 0..100
}
```

> `findings` LUÔN có đủ **7 phần tử** (kể cả khi case chưa có dữ liệu cho category đó → `status_badge="chua_xac_thuc"`, `raw_findings=[]`, `confidence_pct=0`) để FE render đủ 7 card.

### 3.2 `MarketComparable` → 1 dòng bảng `market_comparable`

```jsonc
{
  "address": "Hẻm 39 Trường Sa",
  "distance_km": 1.61,
  "area_sqm": 194.6,
  "transaction_date": "2025-12-23",   // ISO 'YYYY-MM-DD' hoặc null
  "price_per_sqm_vnd": 141500000       // BIGINT (đồng/m²)
}
```

`market_comparables` được rút từ card `market_price` (adapter `comparable_sales`), đã sắp theo `market_comparable.display_order`.

---

## 4. Ánh xạ trường ↔ cột DB

**`findings[]` ↔ `lookup_finding`** (khớp theo `case_id` + `category`):

| JSON | Cột `lookup_finding` |
|---|---|
| `category` | `category` |
| `tool_name` | `tool_name` |
| `title` | `title` |
| `status_badge` | `status_badge` |
| `raw_findings` | `raw_findings` (JSON list[str]) |
| `inference_text` | `inference_text` |
| `source_label` | `source_label` |
| `confidence_pct` | `confidence_pct` |

**`market_comparables[]` ↔ `market_comparable`** (theo `case_id`, sắp `display_order`):

| JSON | Cột `market_comparable` |
|---|---|
| `address` | `comp_address` |
| `distance_km` | `distance_km` |
| `area_sqm` | `area_sqm` |
| `transaction_date` | `transaction_date` |
| `price_per_sqm_vnd` | `price_per_sqm_vnd` |

---

## 5. Ví dụ output rút gọn (case `REQ-2026-2000`)

```jsonc
{
  "case_id": "REQ-2026-2000",
  "findings": [
    { "category": "market_price", "tool_name": "market_price_lookup", "title": "Giá thị trường",
      "status_badge": "da_xac_thuc", "confidence_pct": 78,
      "raw_findings": ["7 giao dịch so sánh trong bán kính 1.1km."],
      "inference_text": "Giá giao dịch so sánh dao động 122.7–162.1 triệu/m²...",
      "source_label": "market_price_lookup" },
    { "category": "legal_status", "tool_name": "legal_status_lookup", "title": "Pháp lý",
      "status_badge": "luu_y", "confidence_pct": 55,
      "raw_findings": ["Sổ hồng chính chủ nhưng còn ghi chú thế chấp đã tất toán, chưa xoá đăng ký."],
      "inference_text": "Cần yêu cầu khách hàng bổ sung văn bản xoá đăng ký thế chấp cũ.",
      "source_label": "legal_status_lookup" }
    // ... đủ 7 category ...
  ],
  "market_comparables": [
    { "address": "Hẻm 39 Trường Sa", "distance_km": 1.61, "area_sqm": 194.6,
      "transaction_date": "2025-12-23", "price_per_sqm_vnd": 141500000 }
    // ...
  ],
  "warnings": []
}
```

---

## 6. Ranh giới & lưu ý

- Plugin **chỉ đọc** — nếu `lookup_finding`/`market_comparable` của case chưa được ghi, output vẫn có 7 finding (badge `chua_xac_thuc`) + `warnings` báo "Chưa có dữ liệu tra cứu".
- Nguồn dữ liệu: seed demo (`ai/scripts/load_seed.sh`) hoặc pipeline tra cứu ghi vào `lookup_finding`/`market_comparable` sau này — **interface đọc không đổi** (đúng ghi chú "cắm data thật" trong ARCHITECTURE.md §6.1).
- `confidence_pct` là `SMALLINT 0..100` (khác `property_intake` nội bộ dùng 0..1).
- `stigma_reputation` confidence thấp → cảnh báo tham khảo, không dùng để từ chối hồ sơ.

## 7. Trạng thái triển khai

Đã khớp contract này (PR2): [schema.py](../../src/shb/ai/plugins/property_lookup/schema.py) · [service.py](../../src/shb/ai/plugins/property_lookup/service.py). Kiểm chứng qua unit test (SQLite), ORM Postgres (seed), và HTTP API.
