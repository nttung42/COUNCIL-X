# Plugin `property_intake` — Trích xuất hồ sơ BĐS (Màn 1)

Trích xuất thông tin từ tài liệu bất động sản (sổ đỏ/hồng, tờ khai LPTB, biên bản
bàn giao, thông báo thuế đất) và tự điền biểu mẫu **"Nhập thông tin" (Màn 1)** của
PAA, kèm **nguồn gốc + độ tin cậy + trạng thái** cho từng ô.

- **Service id:** `property_intake` · **async** (Celery job) · **accepts_file** (pdf, docx)
- **Contract JSON (input/output):** [../../../../../docs/contracts/property-intake-contract.md](../../../../../docs/contracts/property-intake-contract.md)
- **Schema DB đích:** `../../../../../PAA_Schema_PostgreSQL.sql` (bảng Màn 1 + `field_provenance`)

## Luồng gọi (qua platform)

```
POST /api/v1/files                      → upload từng file, nhận file_id
POST /api/v1/services/property_intake/run
     { "input": { "file_ids": ["<file_id>", ...], "case_id": "REQ-2026-0001" } }
     → 202 { "job_id": "..." }           (service is_async)
GET  /api/v1/jobs/{job_id}              → poll tới status=completed, đọc result (PropertyIntakeOutput)
```

Tiến độ job (`job.progress`) được cập nhật theo node: ingest 30 → extract 55 →
verify 70 → merge 82 → validate 92 → assemble 100.

## Pipeline (LangGraph)

```
ingest → extract → verify → merge → validate → assemble
```

| Node | File | Vai trò |
|---|---|---|
| ingest | [nodes/ingest.py](nodes/ingest.py) | Đọc file qua `ctx.storage_service`, parse hybrid PDF text/scan, **phân loại** loại giấy tờ (LLM + fallback keyword). |
| extract | [nodes/extract.py](nodes/extract.py) | Dispatch 4 extractor riêng schema/prompt; **grounding bắt buộc** (không khớp snippet → bỏ); verbatim `value` + `normalized` typed; gom **candidates đa tài liệu**. |
| verify | [nodes/verify.py](nodes/verify.py) | LLM-judge từng giá trị so với đoạn trích nguồn (#5); trượt → hạ confidence. **Fail-open**. |
| merge | [nodes/merge.py](nodes/merge.py) | Hợp nhất candidates theo **ưu tiên nguồn** (GCN > TB thuế > tờ khai > biên bản); lệch ngưỡng → `mau_thuan`, giữ `alternatives`. |
| validate | [nodes/validate.py](nodes/validate.py) | Luật + kiểm tra chéo số học (CCCD, năm XD, diện tích, **mặt tiền×sâu≈DT**) → gắn `validation_flags`. |
| assemble | [nodes/assemble.py](nodes/assemble.py) | Phân tầng confidence (#9) → trạng thái ô; build output đúng contract (target_table/field, confidence_pct, provenance). |

## 4 loại tài liệu & registry

- Extractor + prompt: [schema.py](schema.py) (`SoHongExtraction`, `ToKhaiLPTBExtraction`, `BienBanBanGiaoExtraction`, `ThongBaoThueDatExtraction`), [prompts/__init__.py](prompts/__init__.py).
- **Registry field chuẩn** (khoá canonical → `target_table.target_field`, nhóm A/B/C/D, normalizer): [documents.py](documents.py) — nguồn sự thật duy nhất cho danh sách field của form.

## Trạng thái ô (`FieldStatus`) — khớp enum DB `extraction_field_status`

`da_xac_thuc` (auto-fill) · `can_xac_minh` (cần soát) · `mau_thuan` (nhiều nguồn lệch) ·
`nhap_tay` (không có trong tài liệu) · `suy_luan` (agent suy luận).

## Ranh giới AI ↔ Backend

Plugin **chỉ trả JSON**. Backend ghi DB (PR5): mỗi `FormField`/`alternatives` → dòng
`field_provenance` (`is_selected`), UPSERT 4 bảng Màn 1 theo `target_table/target_field`,
rồi mở khoá `case_step_progress` bước 1. Xem contract để biết mapping chi tiết.

## Test

- Unit theo node + normalizer + validator + merge/verify/tiering: [../../../../../tests/plugins/test_property_intake.py](../../../../../tests/plugins/test_property_intake.py)
- Integration end-to-end qua `service.run` với 4 tài liệu mẫu: [../../../../../tests/plugins/test_property_intake_integration.py](../../../../../tests/plugins/test_property_intake_integration.py) (fixtures: `tests/plugins/_pi_fixtures.py`)

```bash
uv run pytest tests/plugins/test_property_intake.py tests/plugins/test_property_intake_integration.py -v
```

Mọi test chạy **offline** (LLM được mock theo output schema) nên không cần API key.
