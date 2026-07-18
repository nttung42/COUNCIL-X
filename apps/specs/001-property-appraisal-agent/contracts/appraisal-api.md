# Interface Contract: PAA Backend API

Đây là hợp đồng giao tiếp mà bất kỳ caller nào (Planner Agent thật, mock Planner script, hay React
frontend) đều tuân theo để dùng PAA độc lập — khớp với "Interface contract" mục 8 của
`SHB_ThamDinhBDS_DesignDoc_2.md`, cụ thể hoá thành REST/JSON + SSE cho MVP web app.

## 1. Tạo yêu cầu thẩm định

`POST /api/appraisal-requests`

**Request body** (`PropertyAppraisalRequest`):
```json
{
  "request_id": "REQ-2026-0001",
  "subject_property": {
    "address": "Hẻm 45 Nguyễn Văn A, Phường B, Quận C",
    "lat": 10.7756, "long": 106.7019,
    "area_m2": 62,
    "property_type": "nha_pho",
    "legal_status_claimed": "so_hong"
  },
  "loan_context": {
    "requested_amount": 3200000000,
    "purpose": "the_chap_vay_von"
  }
}
```

**Response 202 Accepted**:
```json
{ "case_id": "uuid", "request_id": "REQ-2026-0001", "status": "processing" }
```

**Response 422**: lỗi validation (thiếu field bắt buộc, `area_m2 <= 0`...) — trả về danh sách lỗi
theo field, KHÔNG được silently accept dữ liệu sai.

## 2. Theo dõi tiến độ theo thời gian thực

`GET /api/cases/{case_id}/stream` (Server-Sent Events)

Mỗi event là 1 dòng JSON tương ứng 1 `TraceEvent` + tab cần active:
```json
event: step_update
data: {"step_name": "Đã có kết quả tra cứu", "active_tab": 2, "chat_message": "Đã có kết quả tra cứu — xem tab Kết quả tra cứu. Phát hiện 1 điểm cần lưu ý."}
```

Frontend dùng event này để: (a) append message vào ChatPane, (b) tự động chuyển `active_tab` trên
InfoPanel — đúng FR-011. Kết thúc stream khi `status` chuyển `completed`.

## 3. Lấy toàn bộ state của 1 case (dùng khi mở lại từ sidebar)

`GET /api/cases/{case_id}`

**Response 200** (`AppraisalReport` mở rộng với case state đầy đủ):
```json
{
  "request_id": "REQ-2026-0001",
  "status": "completed",
  "subject_property": { "...": "như lúc tạo" },
  "lookup_result": { "market_price": {"...": "envelope theo data-model.md §5"}, "...": "..." },
  "valuation": { "...": "xem data-model.md §6" },
  "asset_risk": { "...": "xem data-model.md §7" },
  "checklist": [ { "item_id": "...", "text": "...", "is_checked": true } ],
  "draft_report": { "...": "xem data-model.md §9" },
  "requires_human_verification": true,
  "trace_id": "TRACE-8891",
  "trace_events": [ { "step_name": "...", "t_offset_seconds": 0.0 } ]
}
```

**Response 404**: `case_id` không tồn tại.

## 4. Danh sách hồ sơ (sidebar "Lịch sử hồ sơ")

`GET /api/cases?status=processing|completed|cancelled` (optional filter)

**Response 200**:
```json
[
  {"case_id": "uuid", "address": "Hẻm 45 Nguyễn Văn A, Q.C", "status": "processing", "updated_at": "2026-07-18T10:00:00Z"}
]
```

## 5. Chat tự do / Q&A Copilot

`POST /api/cases/{case_id}/messages`

**Request**: `{ "role": "user", "content": "tài sản đang thế chấp nơi khác thì xử lý sao?" }`

**Response 200**: `{ "role": "agent", "content": "...", "citations": [{"source_doc": "quy-trinh-tham-dinh.md", "excerpt": "..."}] }`

**Contract rule**: endpoint này KHÔNG được sửa `valuation`/`asset_risk` của case — chỉ đọc, trả lời,
và append vào `chat_history_json`.

## 6. Checklist toggle

`PATCH /api/cases/{case_id}/checklist/{item_id}` — body `{ "is_checked": true }` → 200 trả lại
`ChecklistItem` đã cập nhật.

## 7. Huỷ hồ sơ

`POST /api/cases/{case_id}/cancel` → 200, `status` chuyển `cancelled`. Không cho phép huỷ case đã
`completed` (trả 409).

## Nguyên tắc chung áp dụng cho mọi endpoint

- Mọi response chứa dữ liệu tra cứu/định giá/rủi ro PHẢI giữ nguyên field `confidence` và
  `source_type`/`verified` từ data-model.md — API layer không được lược bỏ các field này dù
  frontend không hiển thị hết.
- Mọi lỗi trả về theo format chuẩn: `{ "error_code": "...", "message": "...", "field_errors": [] }`.
- Không có endpoint nào tự động set `status = completed` kèm quyết định duyệt/từ chối tín dụng —
  chỉ set `status = completed` khi pipeline (research→valuation→risk→advisory) chạy xong.

## Mock Planner (test độc lập)

`scripts/mock_planner.py` gọi tuần tự: (1) POST tạo request mẫu → (2) poll hoặc subscribe SSE →
(3) GET case đầy đủ → in ra JSON. Dùng script này làm smoke test / demo "PAA chạy độc lập không cần
Planner Agent hệ thống thật".
