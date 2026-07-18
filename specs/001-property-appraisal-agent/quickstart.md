# Quickstart: Validate PAA MVP End-to-End

Mục tiêu: chứng minh pipeline (Research → Valuation → Risk → Advisory) chạy đúng, độc lập với
Planner Agent thật, và giao diện đồng bộ đúng theo `contracts/appraisal-api.md`.

## Prerequisites

- Docker + Docker Compose đã cài.
- File `.env` ở `backend/` được tạo từ `.env.example`, điền `LLM_BASE_URL`, `LLM_API_KEY`,
  `LLM_MODEL` trỏ tới endpoint OpenAI-compatible thật (hoặc mock LLM server nếu chưa có key).
- Mock dataset đã có sẵn dưới `backend/app/mockdata/` (ít nhất địa chỉ mẫu
  "Hẻm 45 Nguyễn Văn A, Phường B, Quận C" dùng xuyên suốt design doc).

## Setup

```bash
docker compose up -d db          # khởi động Postgres + pgvector
cd backend
pip install -r requirements.txt
python -m app.rag.ingest          # nạp kb_documents/ vào pgvector
uvicorn app.main:app --reload     # backend tại http://localhost:8000
```

```bash
cd frontend
npm install
npm run dev                       # frontend tại http://localhost:5173
```

## Kịch bản xác thực 1 — Pipeline độc lập qua mock Planner (không cần UI)

```bash
python scripts/mock_planner.py --address "Hẻm 45 Nguyễn Văn A, Phường B, Quận C" \
  --area-m2 62 --property-type nha_pho --legal-status so_hong \
  --requested-amount 3200000000
```

**Kỳ vọng**: script in ra `AppraisalReport` JSON đầy đủ trong <15s, có:
- `valuation.estimated_value` ≈ 4.85 tỷ (khớp ví dụ trong design doc §4.2)
- `asset_risk.asset_risk_score` ≈ 34, `risk_tier = "MEDIUM"`
- `checklist` có ít nhất 1 mục liên quan đến xác minh tin đồn dân cư
- `requires_human_verification = true`

Xác nhận thủ công (tham chiếu `spec.md` SC-002, SC-003): mọi số liệu trong output có kèm
`confidence`/`source_type`; mục `stigma_factors`/flag `type=stigma` có `verified=false`.

## Kịch bản xác thực 2 — Qua UI, đồng bộ chat ↔ tab

1. Mở `http://localhost:5173`, bấm "Yêu cầu thẩm định mới".
2. Điền form tab "Nhập thông tin" giống dữ liệu ở Kịch bản 1, bấm "Bắt đầu thẩm định →".
3. Quan sát khung chat: các message trạng thái xuất hiện tuần tự ("Đang tra cứu...", "Đã có kết quả
   tra cứu...", "Định giá đề xuất...", "Điểm rủi ro...").
4. Quan sát info panel: tab tự động chuyển 1→2→3→4 theo đúng tiến độ SSE, không cần bấm tay.
5. Mở tab "Checklist", tick 1 mục chưa hoàn thành → xác nhận trạng thái lưu lại (reload trang vẫn
   giữ nguyên, do đọc từ `GET /api/cases/{id}`).
6. Mở tab "Dashboard" → xác nhận timeline hiển thị đủ các bước với mốc thời gian tương đối.

## Kịch bản xác thực 3 — Edge case: địa chỉ không có trong mock data

```bash
python scripts/mock_planner.py --address "Số 999 Đường Không Tồn Tại, Quận X" \
  --area-m2 50 --property-type nha_pho --legal-status so_do --requested-amount 1000000000
```

**Kỳ vọng** (theo spec.md Edge Cases + SC-005): không lỗi cứng/HTTP 500; response trả về với
`valuation.comparables_used = 0`, `confidence_score < 0.4`, và có flag "không đủ dữ liệu so sánh,
cần thẩm định viên bổ sung".

## Kịch bản xác thực 4 — Đa hồ sơ song song

Chạy Kịch bản 1 hai lần với `request_id` khác nhau gần như đồng thời (2 terminal). Xác nhận cả 2
case xử lý độc lập, không case nào bị ghi đè state của case kia (đối chiếu `GET /api/cases`).

## Done When

- Cả 4 kịch bản trên chạy đạt kỳ vọng.
- `pytest backend/tests/contract` pass — schema request/response khớp `contracts/appraisal-api.md`.
- Giao diện khớp trực quan với `PAA_Mockup_SHB.html` (màu sắc, layout 30/70, 6 tab).
