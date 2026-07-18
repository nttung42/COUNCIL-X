# Mock Planner — chạy PAA độc lập không cần Planner Agent thật

Tài liệu này mô tả cách frontend (hoặc `scripts/mock_planner.py` phía backend) đóng vai
"Planner Agent" để gọi PAA độc lập theo `contracts/appraisal-api.md`.

## Luồng frontend đang dùng (state/caseStore.ts)

1. `POST /api/appraisal-requests` (contracts §1) — `actions.createCase(body)`
2. `GET /api/cases/{id}/stream` SSE (contracts §2) — `api.streamCase(...)`; mỗi `step_update`:
   append message vào ChatPane + set `active_tab` trên InfoPanel (FR-011).
3. Khi stream `status=completed` → `GET /api/cases/{id}` (contracts §3) nạp state đầy đủ.
4. Sidebar dùng `GET /api/cases` (contracts §4). Chat tự do `POST /api/cases/{id}/messages`
   (contracts §5). Checklist `PATCH /api/cases/{id}/checklist/{item_id}` (contracts §6).

## Chế độ fixture (VITE_USE_FIXTURE=true)

`services/apiClient.ts` short-circuit mọi hàm trên về dữ liệu trong `mocks/fixtureCase.ts`:

- `fixtureCase` — 1 `AppraisalReport` đầy đủ (Hẻm 45 Nguyễn Văn A, định giá 4.85 tỷ / 78%,
  risk 34/100 MEDIUM, LTV 65%, flag stigma 2019 `verified=false`, flag môi trường ngập 2022–2023).
- `fixtureStepUpdates` — 5 event SSE mô phỏng, phát lại tuần tự để test đồng bộ chat ↔ tab.
- `fixtureCaseList` — 5 hồ sơ cho sidebar (processing/completed/cancelled).

Đổi sang backend thật: đặt `VITE_USE_FIXTURE=false` trong `.env` — KHÔNG cần sửa component/logic UI.
