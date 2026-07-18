# Contract — `property_intake` (Chức năng 1: Nhập thông tin / Màn 1)

> **Trạng thái:** v1 — bản chốt để AI ↔ Backend thống nhất triển khai.
> **Định dạng:** JSON. Plugin AI **chỉ trả JSON**; Backend nhận và ghi DB (PR5).
> **Đối tượng dùng:** Backend (ghi `field_provenance` + 4 bảng Màn 1 + mở khoá `case_step_progress`) và Frontend (render tab "Nhập thông tin").

Contract này căn 1:1 với schema PostgreSQL Màn 1 do FE cung cấp: enum, kiểu dữ liệu, và mô hình provenance (nhiều candidate / field, `is_selected`, `mau_thuan`).

---

## 1. Enum (đồng bộ tuyệt đối với DB)

| Trường JSON | Enum DB | Giá trị |
|---|---|---|
| `documents[].detected_doc_type` | `extracted_doc_type` | `so_do_so_hong` · `to_khai_lptb` · `bien_ban_ban_giao` · `thong_bao_thue_dat` · `khac` |
| `fields[].status`, `alternatives[].status` | `extraction_field_status` | `da_xac_thuc` · `can_xac_minh` · `mau_thuan` · `nhap_tay` · `suy_luan` |

Ý nghĩa `status`:
- `da_xac_thuc` — grounded + verifier pass + confidence ≥ 85 → auto-fill.
- `can_xac_minh` — có giá trị nhưng cần soát (confidence thấp / verifier trượt / dính validation flag).
- `mau_thuan` — nhiều tài liệu cho giá trị khác nhau; `value` là giá trị ưu tiên, các giá trị khác nằm trong `alternatives`.
- `nhap_tay` — không có trong tài liệu → để trống cho người nhập.
- `suy_luan` — agent suy luận (không có span nguồn trực tiếp).

---

## 2. Input

```jsonc
// POST /api/v1/services/property_intake/run  (body.input)
{
  "file_ids": ["a3f1c2e4-...", "b7d9e0f1-..."], // BẮT BUỘC, ≥1. Là id của attached_document
  "case_id": "REQ-2026-0001",                    // tuỳ chọn (mã hồ sơ)
  "language": "vi"                               // tuỳ chọn, mặc định "vi"
}
```

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `file_ids` | `string[]` | ✔ (min 1) | `attached_document.id` của các file đã upload. Backend nạp bytes qua storage. |
| `case_id` | `string \| null` | ✗ | Trả nguyên lại trong output. |
| `language` | `string` | ✗ | Mặc định `"vi"`. |

---

## 3. Output

```jsonc
{
  "case_id": "REQ-2026-0001",     // hoặc null
  "documents": [ DocumentInfo ],  // 1 phần tử / file đọc được
  "fields":    [ FormField ],     // TOÀN BỘ field của form (thiếu → status "nhap_tay")
  "warnings":  [ "..." ]          // cảnh báo mức hồ sơ (mâu thuẫn, file lỗi, scan chưa OCR...)
}
```

### 3.1 `DocumentInfo` → bảng `attached_document`

```jsonc
{
  "file_id": "a3f1c2e4-...",       // = attached_document.id
  "file_name": "so-hong.pdf",
  "detected_doc_type": "so_do_so_hong", // enum extracted_doc_type -> cột detected_doc_type
  "is_scan": false,                // -> cột is_scan
  "page_count": 3                  // -> cột page_count
}
```

### 3.2 `FormField` → 1 field của form + nguồn để ghi DB

```jsonc
{
  "key": "land_area_sqm",              // khoá canonical (ổn định)
  "section": "C",                      // 'A'|'B'|'C'|'D' (nhóm hiển thị)
  "label": "Diện tích đất",

  "target_table": "property_physical_info", // bảng đích để UPSERT
  "target_field": "land_area_sqm",          // cột đích

  "value": "62",            // NGUYÊN VĂN từ tài liệu -> field_provenance.extracted_value
  "normalized": 62.0,       // giá trị TYPED để ghi cột đích (xem §4). null nếu không chuẩn hoá được
  "status": "da_xac_thuc",  // enum extraction_field_status
  "confidence_pct": 80,     // 0..100 (SMALLINT) -> field_provenance.confidence_pct

  // Provenance của GIÁ TRỊ ĐANG CHỌN (is_selected = true)
  "source_file_id": "a3f1c2e4-...",  // -> field_provenance.source_document_id. null nếu nhap_tay/suy_luan
  "source_page": 1,                  // -> field_provenance.source_page. null nếu chưa xác định
  "source_snippet": "Diện tích: 62 m2", // -> field_provenance.source_snippet
  "bbox": null,                      // hoặc {x,y,width,height} 0..1; page = source_page

  "verifier_passed": true,           // #5: true/false/null(chưa chấm). Thông tin, không có cột riêng
  "validation_flags": [],            // feature 4: lý do cần xác minh (mảng string)

  // Chỉ khác rỗng khi status = "mau_thuan": các giá trị cạnh tranh từ tài liệu khác
  "alternatives": [ AlternativeValue ]
}
```

### 3.3 `AlternativeValue` (mỗi phần tử → 1 dòng `field_provenance` với `is_selected=false`)

```jsonc
{
  "value": "80",
  "normalized": 80.0,
  "status": "mau_thuan",
  "confidence_pct": 90,
  "source_file_id": "b7d9e0f1-...",
  "source_doc_type": "thong_bao_thue_dat",
  "source_page": 1,
  "source_snippet": "Diện tích đất: 80 m²",
  "bbox": null
}
```

### 3.4 `Bbox` (toạ độ chuẩn hoá 0..1)

```jsonc
{ "x": 0.12, "y": 0.34, "width": 0.20, "height": 0.03 }
```

---

## 4. Kiểu `normalized` theo từng cột đích

| target_field (cột) | Kiểu DB | `normalized` |
|---|---|---|
| `loan_amount_vnd` | `BIGINT` | `int` (VND, vd `1500000000`) |
| `land_area_sqm`, `floor_area_sqm`, `frontage_m`, `depth_m`, `alley_width_m` | `NUMERIC` | `float` (vd `62.0`) |
| `construction_year`, `loan_term_years` | `SMALLINT` | `int` |
| `issue_date` | `DATE` | `string` ISO `"YYYY-MM-DD"` |
| còn lại (text) | `TEXT` | `null` (dùng `value`) |

Backend ghi cột đích bằng `normalized` khi có; nếu `null` (không chuẩn hoá được) thì fallback `value`.

---

## 5. Cách Backend biến output thành DB (PR5, tóm tắt)

1. **`attached_document`**: cập nhật `detected_doc_type`, `is_scan`, `page_count` từ `documents[]`.
2. **`field_provenance`**: mỗi `FormField` có `value` → ghi 1 dòng `is_selected=true`; mỗi `alternatives[]` → 1 dòng `is_selected=false`. Field `nhap_tay`/`suy_luan` không có `source_file_id` (đúng CHECK constraint của bảng).
3. **4 bảng Màn 1**: UPSERT giá trị `is_selected` theo `target_table` → gom các field cùng bảng thành 1 row (`property_legal_info`/`property_physical_info`/`loan_info` là 1:1 theo `case_id`; `case_borrower` cho phép nhiều dòng).
4. **`case_step_progress`**: sau khi ghi xong → set bước 1 = `unlocked`.

> Backend là **chủ** của `target_record_id`, `is_selected` cuối cùng (khi người dùng chọn lại giá trị ở ô `mau_thuan`), và `case_edit_log`. Plugin chỉ đề xuất giá trị + provenance.

---

## 6. Ví dụ output rút gọn

```jsonc
{
  "case_id": "REQ-2026-0001",
  "documents": [
    { "file_id": "a3f1c2e4-...", "file_name": "so-hong.pdf",
      "detected_doc_type": "so_do_so_hong", "is_scan": false, "page_count": 2 },
    { "file_id": "b7d9e0f1-...", "file_name": "thong-bao-thue.pdf",
      "detected_doc_type": "thong_bao_thue_dat", "is_scan": false, "page_count": 1 }
  ],
  "fields": [
    { "key": "owner_full_name", "section": "A", "label": "Họ và tên",
      "target_table": "case_borrower", "target_field": "full_name",
      "value": "Nguyễn Văn A", "normalized": null, "status": "da_xac_thuc",
      "confidence_pct": 95, "source_file_id": "a3f1c2e4-...", "source_page": 1,
      "source_snippet": "Người sử dụng đất: Ông Nguyễn Văn A", "bbox": null,
      "verifier_passed": true, "validation_flags": [], "alternatives": [] },

    { "key": "land_area_sqm", "section": "C", "label": "Diện tích đất",
      "target_table": "property_physical_info", "target_field": "land_area_sqm",
      "value": "62", "normalized": 62.0, "status": "mau_thuan",
      "confidence_pct": 80, "source_file_id": "a3f1c2e4-...", "source_page": 1,
      "source_snippet": "Diện tích: 62 m2", "bbox": null,
      "verifier_passed": true, "validation_flags": [],
      "alternatives": [
        { "value": "80", "normalized": 80.0, "status": "mau_thuan", "confidence_pct": 90,
          "source_file_id": "b7d9e0f1-...", "source_doc_type": "thong_bao_thue_dat",
          "source_page": 1, "source_snippet": "Diện tích đất: 80 m²", "bbox": null }
      ] },

    { "key": "loan_amount_vnd", "section": "D", "label": "Số tiền vay",
      "target_table": "loan_info", "target_field": "loan_amount_vnd",
      "value": null, "normalized": null, "status": "nhap_tay",
      "confidence_pct": 0, "source_file_id": null, "source_page": null,
      "source_snippet": null, "bbox": null,
      "verifier_passed": null, "validation_flags": [], "alternatives": [] }
  ],
  "warnings": [
    "Trường 'Diện tích đất' mâu thuẫn giữa các tài liệu: ưu tiên '62' (từ so-hong.pdf); giá trị khác: 80."
  ]
}
```

---

## 7. Trạng thái triển khai (đã khớp — PR4.1)

Code plugin đã khớp contract này (PR4.1):
- ✅ `FormField`: có `target_table`, `target_field`, `source_file_id`; dùng `confidence_pct` (0..100); `alternatives` dùng shape `AlternativeValue`.
- ✅ `DocumentInfo`: `is_scan`, `detected_doc_type`.
- ✅ `FieldValue`: mang `source_file_id`; suy ra `source_page` từ trang chứa snippet; normalize `construction_year`/`loan_term_years` (int).
- ✅ Registry: có `frontage_m`, `depth_m`, `alley_width_m` (property_physical_info) → validator `frontage×depth≈diện tích` đã bật.
- ✅ `Bbox`: `x,y,width,height` (0..1); page ở `source_page`.

Danh sách `fields[]` luôn chứa **toàn bộ** field của form (kể cả `nhap_tay`) để FE render đủ biểu mẫu.
```
