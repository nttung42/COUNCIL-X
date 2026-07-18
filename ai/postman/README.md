# Test property_intake trên Postman

## Chuẩn bị
1. Chạy stack: `docker compose up` (trong thư mục `ai/`). API ở `http://localhost:8888`.
2. Postman → **Import** → chọn `postman/PAA_property_intake.postman_collection.json`.
3. File mẫu để upload có sẵn: `ai/samples/01_so_hong.pdf` … `04_thong_bao_thue_dat.pdf`.

## Chạy theo thứ tự (biến tự lưu qua test script)
| # | Request | Ghi chú |
|---|---|---|
| 0 | Health | Kiểm tra server (200). |
| 1 | Register | Tự lưu `{{api_key}}`. Nếu 409 (email trùng) → đổi biến `email` rồi gửi lại. |
| 2a–2d | Upload file 1–4 | Body → **form-data** → key `file` (kiểu **File**) → chọn PDF tương ứng. Tự lưu `{{file_id_1..4}}`. |
| 3 | Run property_intake | Dùng 4 file_id, trả `{{job_id}}` (async). |
| 4 | Get job (poll) | Bấm **Send** lại nhiều lần tới khi `status = completed`; đọc `result`. |

> Nguồn sự thật là **`status`** (pending → running → completed), không phải `progress`
> (progress ghi kiểu fire-and-forget nên có thể dừng ở 82 dù đã completed).

## Kết quả mong đợi (với 4 file mẫu)
- `documents`: 4 tài liệu, `detected_doc_type` đúng từng loại.
- `fields`: 30 ô. Owner/giấy tờ/địa chỉ… `da_xac_thuc`; ngày cấp `normalized` = `2020-03-15`; diện tích `normalized` số.
- **`Diện tích đất` = `mau_thuan`**: sổ hồng 62 m² thắng, `alternatives` giữ 80 m² (từ thông báo thuế).
- `warnings`: liệt kê các trường mâu thuẫn.

## Lưu ý
- Mọi request (trừ Register/Health) cần header `X-API-Key: {{api_key}}` (đã set sẵn).
- Trích xuất gọi **LLM thật** theo `LLM_*` trong `.env`. Nếu key sai/không tới được, field sẽ thành `nhap_tay` + có `warnings`, nhưng job vẫn `completed`.
- Chạy uvicorn thủ công (port 8000)? Đổi biến collection `host` → `http://localhost:8000` và `base_url` → `http://localhost:8000/api/v1`.
