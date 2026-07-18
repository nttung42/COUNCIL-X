# Tasks: Property Appraisal Agent (PAA) — MVP Workspace

**Input**: Design documents from `/specs/001-property-appraisal-agent/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/appraisal-api.md, quickstart.md

**Tests**: Bao gồm 1 lớp contract/integration test mỏng cho các endpoint cốt lõi (đủ để chặn lỗi
schema phá vỡ Nguyên tắc IV) — không làm full TDD cho từng hàm nội bộ, do giới hạn thời gian
hackathon.

**Organization**: Task nhóm theo user story (US1/US2/US3, khớp `spec.md`) để có thể giao cho nhiều
agent/dev làm song song qua `/harness`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Có thể chạy song song (khác file, không phụ thuộc task chưa xong)
- **[Story]**: US1 / US2 / US3 theo `spec.md`
- Mọi task đều có đường dẫn file cụ thể theo `plan.md` Project Structure

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Tạo khung thư mục `backend/` và `frontend/` theo `plan.md` Project Structure
- [ ] T002 Khởi tạo backend Python: `backend/requirements.txt` (fastapi, uvicorn, google-adk,
      openai, sqlalchemy, asyncpg, pgvector, pydantic-settings, python-dotenv, pytest, httpx)
- [ ] T003 [P] Khởi tạo frontend Vite + React + TypeScript trong `frontend/`
- [ ] T004 [P] Viết `docker-compose.yml` gồm service `db` (Postgres 16 + extension `pgvector`) và
      service `backend`
- [ ] T005 [P] Viết `backend/.env.example` (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`,
      `DATABASE_URL`, `EMBEDDING_MODEL`)
- [ ] T006 [P] Cấu hình lint/format: `ruff`+`black` cho backend, `eslint`+`prettier` cho frontend

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: Không user story nào được bắt đầu trước khi phase này xong — đặc biệt là mock
data, vì mọi tool/agent ở Phase 3 đều đọc từ đây (Development Workflow trong constitution).

### Mock data (ưu tiên cao nhất — chốt schema trước để các phase sau không phải rework)

- [ ] T007 [P] Tạo `backend/app/mockdata/transactions.json` — dataset `ComparableTransaction`
      (data-model.md §2): ≥30 bản ghi trải trên 2 khu vực mẫu (vd. "Phường B, Quận C" và 1 khu vực
      thứ 2), có đủ biến thiên `frontage_m`/`alley_width_m`/`floors`/`legal_status` để Valuation
      Engine có dữ liệu điều chỉnh thực tế
- [ ] T008 [P] Tạo `backend/app/mockdata/price_index.json` — `PriceIndexSeries` (data-model.md §3)
      cho cùng 2 khu vực, theo quý từ 2024-Q1 đến 2026-Q2, khớp ví dụ 100.0→118.3 trong design doc
- [ ] T009 [P] Tạo `backend/app/mockdata/address_profiles.json` — `AddressProfile` (data-model.md
      §4) cho ≥8 địa chỉ, MỖI địa chỉ đủ 3 nhóm `positive_factors`/`negative_factors`/
      `stigma_factors` tách biệt rõ ràng, `stigma_factors[].verified` luôn `false`
- [ ] T010 [P] Tạo `backend/app/mockdata/zoning.json` — dữ liệu quy hoạch/lộ giới theo địa chỉ/mã
      thửa cho cùng tập địa chỉ ở T009
- [ ] T011 [P] Tạo `backend/app/mockdata/legal_records.json` — tình trạng pháp lý/tranh chấp/thế
      chấp theo địa chỉ, khớp `legal_status_claimed` để test đối chiếu khai báo vs thực tế
- [ ] T012 [P] Tạo `backend/app/mockdata/amenities.json` — POI (trường học, chợ, bệnh viện, giao
      thông) theo bán kính quanh từng địa chỉ mẫu
- [ ] T013 [P] Tạo `backend/app/mockdata/environmental_risk.json` — ngập úng/sạt lở/ô nhiễm theo
      khu vực, bao gồm case "từng ngập nhẹ 2022–2023" khớp ví dụ design doc
- [ ] T014 [P] Tạo `backend/app/mockdata/liquidity_stats.json` — thời gian bán TB + tỷ lệ thành
      công theo khu vực/phân khúc
- [ ] T015 [P] Viết `backend/app/mockdata/kb_documents/` — ≥6 tài liệu RAG: quy trình thẩm định nội
      bộ, checklist theo loại BĐS (nhà phố/đất nền/chung cư), trích quy định pháp luật liên quan
      LTV, và ≥2 case đã thẩm định trước làm best-practice
- [ ] T016 Viết script kiểm tra chéo `backend/app/mockdata/validate_mockdata.py` — đảm bảo mọi
      `address_id` xuất hiện nhất quán giữa transactions/zoning/legal/amenities/environmental/
      liquidity/address_profiles (tránh case "có profile nhưng thiếu giao dịch" gây lỗi demo)

### Hạ tầng backend

- [ ] T017 Thiết lập schema/migration Postgres cho `CaseSession`, `TraceEvent`, `KbChunk`
      (data-model.md §10–12) trong `backend/app/db/migrations/`
- [ ] T018 Implement `backend/app/config.py` đọc `.env` (LLM base_url/api_key/model,
      embedding model, database url) — không hardcode giá trị mặc định nhạy cảm
- [ ] T019 Implement `backend/app/db/session.py` (SQLAlchemy engine/session async)
- [ ] T020 [P] Implement SQLAlchemy models `backend/app/models/case_session.py`,
      `backend/app/models/trace_event.py`, `backend/app/models/kb_chunk.py` theo data-model.md
- [ ] T021 Implement `backend/app/rag/embedder.py` (gọi embedding model qua OpenAI-compatible
      client dùng config T018) và `backend/app/rag/ingest.py` (chunk + nạp `kb_documents/` vào
      bảng `KbChunk`) — phụ thuộc T015, T018, T020
- [ ] T022 Implement khung FastAPI `backend/app/main.py` + format lỗi chuẩn
      `{error_code, message, field_errors}` dùng chung cho mọi router
- [ ] T023 Viết khung `scripts/mock_planner.py` (chưa gọi API thật, chỉ dựng CLI arg parser +
      cấu trúc gọi tuần tự theo contracts/appraisal-api.md)
- [ ] T024 [P] Dựng khung React: `frontend/src/theme/tokens.css` (copy nguyên token màu từ
      `PAA_Mockup_SHB.html`), `frontend/src/App.tsx` (layout Sidebar + ChatPane 30% + InfoPanel 70%)

**Checkpoint**: Mock data đầy đủ + hạ tầng backend/frontend sẵn sàng — user story có thể bắt đầu
song song.

---

## Phase 3: User Story 1 — Thẩm định viên nộp hồ sơ và nhận kết quả tự động (Priority: P1) 🎯 MVP

**Goal**: Toàn bộ pipeline Research → Valuation → Risk → Advisory chạy tự động từ 1
`PropertyAppraisalRequest`, đồng bộ ra chat + 5 tab info panel.

**Independent Test**: Chạy `scripts/mock_planner.py` với địa chỉ mẫu, xác nhận nhận đủ
`AppraisalReport` (valuation + asset_risk + checklist + draft_report) đúng theo quickstart.md
Kịch bản 1, không cần Copilot Q&A hay sidebar đa hồ sơ.

### Tests for User Story 1

- [ ] T025 [P] [US1] Contract test `POST /api/appraisal-requests` (schema request/response theo
      `contracts/appraisal-api.md` §1) trong `backend/tests/contract/test_appraisal_requests.py`
- [ ] T026 [P] [US1] Contract test `GET /api/cases/{id}` (schema theo §3) trong
      `backend/tests/contract/test_cases_get.py`
- [ ] T027 [P] [US1] Integration test pipeline đầy đủ qua mock Planner trong
      `backend/tests/integration/test_pipeline_e2e.py` (dùng địa chỉ mẫu, assert có
      `confidence`/`source_type` trên mọi field tra cứu — chặn regression Nguyên tắc II)

### Lookup tools (Research Agent) — 7 file độc lập, chạy song song

- [ ] T028 [P] [US1] Implement `market_price_lookup` trong `backend/app/tools/market_price_lookup.py`
      (đọc T007+T008, áp dụng công thức quy đổi giá theo chỉ số ở data-model.md §3)
- [ ] T029 [P] [US1] Implement `planning_zoning_lookup` trong
      `backend/app/tools/planning_zoning_lookup.py` (đọc T010)
- [ ] T030 [P] [US1] Implement `legal_status_lookup` trong `backend/app/tools/legal_status_lookup.py`
      (đọc T011, đối chiếu với `legal_status_claimed`)
- [ ] T031 [P] [US1] Implement `neighborhood_amenity_lookup` trong
      `backend/app/tools/neighborhood_amenity_lookup.py` (đọc T012)
- [ ] T032 [P] [US1] Implement `stigma_reputation_lookup` trong
      `backend/app/tools/stigma_reputation_lookup.py` (đọc T009 `stigma_factors`,
      **luôn set `verified=false`** — Nguyên tắc III)
- [ ] T033 [P] [US1] Implement `environmental_risk_lookup` trong
      `backend/app/tools/environmental_risk_lookup.py` (đọc T013)
- [ ] T034 [P] [US1] Implement `liquidity_stat_lookup` trong
      `backend/app/tools/liquidity_stat_lookup.py` (đọc T014)

### Agents & Orchestrator

- [ ] T035 [US1] Implement Research Agent (ADK `ParallelAgent`) trong
      `backend/app/agents/research_agent.py` gọi 7 tool T028–T034 song song, gộp kết quả theo
      envelope chuẩn data-model.md §5 (phụ thuộc T028–T034)
- [ ] T036 [P] [US1] Implement `calculate_valuation` trong
      `backend/app/tools/calculate_valuation.py` (3 phương pháp + blend + confidence, data-model.md §6)
- [ ] T037 [US1] Implement Valuation Agent trong `backend/app/agents/valuation_agent.py` (phụ
      thuộc T035, T036)
- [ ] T038 [P] [US1] Implement `calculate_asset_risk_score` trong
      `backend/app/tools/calculate_asset_risk_score.py` (5 nhóm rủi ro có trọng số, cô lập
      `reputation_stigma` tối đa 10% theo Nguyên tắc III, data-model.md §7)
- [ ] T039 [US1] Implement Risk Assessment Agent trong `backend/app/agents/risk_agent.py` (phụ
      thuộc T037, T038)
- [ ] T040 [P] [US1] Implement `query_knowledge_base` trong
      `backend/app/tools/query_knowledge_base.py` (similarity search trên bảng `KbChunk`, phụ
      thuộc T021)
- [ ] T041 [P] [US1] Implement `generate_report_draft` trong
      `backend/app/tools/generate_report_draft.py` (sinh `AppraisalReportDraft` theo data-model.md §9)
- [ ] T042 [US1] Implement Advisory Agent trong `backend/app/agents/advisory_agent.py` (checklist
      động + nháp báo cáo, phụ thuộc T039, T040, T041)
- [ ] T043 [US1] Implement PAA Orchestrator trong `backend/app/orchestrator/paa_orchestrator.py` —
      điều phối Research→Valuation→Risk→Advisory tuần tự, ghi `TraceEvent` mỗi bước, cập nhật
      `CaseSession` (phụ thuộc T035, T037, T039, T042, T017, T020)

### API Endpoints

- [ ] T044 [US1] Implement `POST /api/appraisal-requests` trong `backend/app/api/appraisal.py`
      (tạo `CaseSession`, kích hoạt Orchestrator bất đồng bộ — phụ thuộc T043)
- [ ] T045 [US1] Implement `GET /api/cases/{id}` và `GET /api/cases` trong
      `backend/app/api/cases.py` (phụ thuộc T020)
- [ ] T046 [US1] Implement `GET /api/cases/{id}/stream` (SSE) trong `backend/app/api/appraisal.py`
      đẩy `TraceEvent` mới + `active_tab` theo contracts/appraisal-api.md §2 (phụ thuộc T044)
- [ ] T047 [US1] Implement `PATCH /api/cases/{id}/checklist/{item_id}` trong
      `backend/app/api/cases.py`
- [ ] T048 [US1] Implement `POST /api/cases/{id}/cancel` trong `backend/app/api/cases.py`

### Frontend — 6 tab

- [ ] T049 [P] [US1] Implement `frontend/src/components/InfoPanel/Tab1Input.tsx` (form nhập +
      nút "Bắt đầu thẩm định")
- [ ] T050 [P] [US1] Implement `frontend/src/components/InfoPanel/Tab2Lookup.tsx` (bảng giao dịch
      so sánh + lookup mini-card, hiển thị badge xác thực/chưa xác thực theo `source_type`)
- [ ] T051 [P] [US1] Implement `frontend/src/components/InfoPanel/Tab3Valuation.tsx` (stat tile +
      barchart 3 phương pháp + sparkline chỉ số giá)
- [ ] T052 [P] [US1] Implement `frontend/src/components/InfoPanel/Tab4Risk.tsx` (meter điểm rủi
      ro/LTV + barchart 5 nhóm rủi ro + danh sách flag)
- [ ] T053 [P] [US1] Implement `frontend/src/components/InfoPanel/Tab5Checklist.tsx` (checklist
      tick/untick gọi T047 + preview nháp biên bản)
- [ ] T054 [P] [US1] Implement `frontend/src/components/InfoPanel/Tab6Dashboard.tsx` (timeline
      trace từ `TraceEvent`)
- [ ] T055 [US1] Implement `frontend/src/components/InfoPanel/SubtabBar.tsx` + logic tự chuyển
      tab khi nhận SSE event (phụ thuộc T046, T049–T054)
- [ ] T056 [US1] Implement `frontend/src/components/ChatPane/ChatPane.tsx` (hiển thị message
      trạng thái tuần tự theo SSE, phụ thuộc T046)
- [ ] T057 [US1] Implement `frontend/src/services/apiClient.ts` và
      `frontend/src/state/caseStore.ts` (state đồng bộ chat + info panel cho case đang mở)
- [ ] T058 [US1] Hoàn thiện `scripts/mock_planner.py` gọi đủ luồng POST → SSE/poll → GET (phụ
      thuộc T044–T048), dùng làm smoke test độc lập theo Nguyên tắc IV

**Checkpoint**: User Story 1 chạy được độc lập đầu-cuối (quickstart.md Kịch bản 1–3) — đây là MVP
có thể demo.

---

## Phase 4: User Story 2 — Hỏi đáp & chỉnh sửa qua Copilot (Priority: P2)

**Goal**: Thẩm định viên hỏi tự do trong chat và nhận câu trả lời có trích dẫn RAG, không ảnh
hưởng kết quả đã có của case.

**Independent Test**: Với 1 case đã `completed` (từ US1), gửi 1 câu hỏi tự do, xác nhận nhận câu
trả lời kèm trích dẫn và `valuation`/`asset_risk` của case không đổi.

- [ ] T059 [P] [US2] Contract test `POST /api/cases/{id}/messages` trong
      `backend/tests/contract/test_messages.py` (khớp contracts/appraisal-api.md §5)
- [ ] T060 [US2] Implement `POST /api/cases/{id}/messages` trong `backend/app/api/chat.py`, dùng
      Advisory Agent (T042) + `query_knowledge_base` (T040) để trả lời kèm citation, chỉ append
      `chat_history_json`, không sửa `valuation_result_json`/`risk_result_json`
- [ ] T061 [US2] Nối ô nhập chat tự do trong `frontend/src/components/ChatPane/ChatPane.tsx` gọi
      T060 (phụ thuộc T056, T060)
- [ ] T062 [US2] Hiển thị citation nguồn RAG trong bong bóng chat agent
      (`frontend/src/components/ChatPane/ChatPane.tsx`)

**Checkpoint**: User Story 1 + 2 cùng hoạt động độc lập.

---

## Phase 5: User Story 3 — Quản lý nhiều hồ sơ qua sidebar & dashboard (Priority: P3)

**Goal**: Chuyển đổi giữa nhiều hồ sơ ở sidebar không lẫn state; dashboard hiển thị đúng trace của
case đang mở.

**Independent Test**: Tạo 2 case độc lập (US1), chuyển qua lại ở sidebar, xác nhận mỗi case hiển
thị đúng dữ liệu/trace riêng của nó (quickstart.md Kịch bản 4).

- [ ] T063 [P] [US3] Implement `frontend/src/components/Sidebar/Sidebar.tsx` (danh sách hồ sơ gọi
      `GET /api/cases`, dot màu theo `status`, nút "Yêu cầu thẩm định mới")
- [ ] T064 [US3] Implement logic chuyển case trong `frontend/src/state/caseStore.ts` — load lại
      toàn bộ chat + info panel qua `GET /api/cases/{id}` khi chọn hồ sơ khác (phụ thuộc T057, T063)
- [ ] T065 [US3] Xác nhận `GET /api/cases/{id}` (T045) trả đủ `trace_events` sắp theo
      `t_offset_seconds` để `Tab6Dashboard.tsx` (T054) vẽ đúng timeline cho case được chọn
- [ ] T066 [US3] Reset về `Tab1Input` khi bấm "Yêu cầu thẩm định mới" trong
      `frontend/src/App.tsx`/`caseStore.ts`

**Checkpoint**: Cả 3 user story hoạt động độc lập và cùng lúc.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T067 [P] Thêm banner disclaimer "dữ liệu mô phỏng, không phải số liệu ngân hàng thật" cố
      định trong `frontend/src/App.tsx` (Nguyên tắc VI)
- [ ] T068 [P] Thêm error boundary + toast lỗi API dùng chung format `error_code`/`message`
      trong `frontend/src/App.tsx`
- [ ] T069 Chạy đủ 4 kịch bản trong `quickstart.md` và ghi lại kết quả
- [ ] T070 [P] Viết `README.md` gốc: hướng dẫn setup Docker, chạy backend/frontend, chạy
      `scripts/mock_planner.py`
- [ ] T071 Rà soát bảo mật/tuân thủ: xác nhận không hardcode API key/base_url ở bất kỳ file nào
      ngoài `.env`/`.env.example`, và mọi response API vẫn giữ nguyên `confidence`/`source_type`
      (đối chiếu lại Constitution Check trong `plan.md`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: không phụ thuộc — bắt đầu ngay
- **Foundational (Phase 2)**: phụ thuộc Setup — **CHẶN** toàn bộ user story, đặc biệt mock data
  (T007–T016) phải xong trước khi bất kỳ tool nào ở Phase 3 được viết
- **User Stories (Phase 3+)**: đều phụ thuộc Foundational xong; US1 là MVP bắt buộc trước, US2/US3
  có thể chạy song song với nhau sau khi US1 có API endpoint ổn định (US2 cần T042/T040, US3 cần
  T045/T054 — cả hai đều thuộc US1 nhưng không cần US1 "hoàn thiện UI" mới bắt đầu được)
- **Polish (Phase 6)**: sau khi các user story cần thiết đã xong

### Parallel Opportunities

- Toàn bộ T007–T015 (mock data) là các file JSON/markdown độc lập — giao cho nhiều agent/dev làm
  đồng thời, chỉ cần thống nhất `address_id`/tên địa chỉ trước (xem T016 làm bước validate cuối)
- Toàn bộ 7 lookup tool T028–T034 độc lập file, độc lập logic — song song hoàn toàn
- 6 tab frontend T049–T054 độc lập file — song song hoàn toàn
- Sau khi Foundational xong: 1 nhóm có thể làm backend (Research→Advisory, T028–T048), 1 nhóm làm
  frontend (T049–T058) song song, join tại T055/T056/T058

---

## Parallel Example: Foundational mock data

```bash
Task: "Tạo backend/app/mockdata/transactions.json — dataset ComparableTransaction ≥30 bản ghi"
Task: "Tạo backend/app/mockdata/price_index.json — PriceIndexSeries 2024-Q1..2026-Q2"
Task: "Tạo backend/app/mockdata/address_profiles.json — AddressProfile ≥8 địa chỉ"
Task: "Tạo backend/app/mockdata/zoning.json"
Task: "Tạo backend/app/mockdata/legal_records.json"
Task: "Tạo backend/app/mockdata/amenities.json"
Task: "Tạo backend/app/mockdata/environmental_risk.json"
Task: "Tạo backend/app/mockdata/liquidity_stats.json"
Task: "Viết backend/app/mockdata/kb_documents/*.md — ≥6 tài liệu RAG"
```

## Parallel Example: User Story 1 — 7 lookup tools

```bash
Task: "Implement market_price_lookup trong backend/app/tools/market_price_lookup.py"
Task: "Implement planning_zoning_lookup trong backend/app/tools/planning_zoning_lookup.py"
Task: "Implement legal_status_lookup trong backend/app/tools/legal_status_lookup.py"
Task: "Implement neighborhood_amenity_lookup trong backend/app/tools/neighborhood_amenity_lookup.py"
Task: "Implement stigma_reputation_lookup trong backend/app/tools/stigma_reputation_lookup.py"
Task: "Implement environmental_risk_lookup trong backend/app/tools/environmental_risk_lookup.py"
Task: "Implement liquidity_stat_lookup trong backend/app/tools/liquidity_stat_lookup.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Hoàn thành Phase 1: Setup
2. Hoàn thành Phase 2: Foundational (mock data là trọng tâm — KHÔNG rút gọn phần này)
3. Hoàn thành Phase 3: User Story 1
4. **DỪNG và kiểm chứng**: chạy đủ quickstart.md Kịch bản 1–3
5. Demo nếu đã sẵn sàng

### Incremental Delivery

1. Setup + Foundational → nền tảng sẵn sàng
2. + User Story 1 → kiểm thử độc lập → Demo (MVP!)
3. + User Story 2 → kiểm thử độc lập → Demo
4. + User Story 3 → kiểm thử độc lập → Demo

### Parallel Agent/Team Strategy

Sau khi Foundational xong, chia theo ranh giới module (khớp Development Workflow trong
constitution) để nhiều agent/dev chạy song song qua `/harness`:

1. Agent "Mock Data" — T007–T016 (nên chạy TRƯỚC/sớm nhất, chặn mọi agent khác)
2. Agent "Lookup Tools" — T028–T034 (Research Agent tools)
3. Agent "Valuation & Risk" — T036–T039
4. Agent "Advisory & RAG" — T021, T040–T042
5. Agent "Orchestrator & API" — T043–T048 (cần chờ agent 2–4 xong phần tool trước khi wiring)
6. Agent "Frontend" — T049–T058 (chạy song song với agent 2–5, chỉ cần contracts/appraisal-api.md
   làm hợp đồng, join ở cuối khi API thật sẵn sàng)

---

## Notes

- [P] = khác file, không phụ thuộc task chưa xong
- [Story] map task với user story để truy vết
- Mock data (T007–T016) là nền tảng của toàn bộ demo — theo yêu cầu người dùng, đây là phần cần
  làm chi tiết nhất và không được rút gọn dù áp lực thời gian hackathon
- Dừng ở bất kỳ checkpoint nào để kiểm chứng độc lập từng user story trước khi làm tiếp
