# Implementation Plan: Property Appraisal Agent (PAA) — MVP Workspace

**Branch**: `001-property-appraisal-agent` | **Date**: 2026-07-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-property-appraisal-agent/spec.md`

## Summary

Xây MVP module Property Appraisal Agent (PAA) cho SHB: 1 PAA Orchestrator điều phối 4 sub-agent
chuyên trách (Research, Valuation, Risk Assessment, Advisory) trên Google ADK, expose qua FastAPI
theo interface contract `property_appraisal_request` → `AppraisalReport`, dùng LLM OpenAI-compatible
qua custom base_url, lưu state/trace vào PostgreSQL và RAG knowledge base vào pgvector (Docker), và
hiển thị qua React frontend đúng theo mockup (chat 30% + info panel 70%, 6 tab). Toàn bộ dữ liệu
tra cứu là mock/synthetic, thiết kế theo adapter pattern.

## Technical Context

**Language/Version**: Python 3.11+ (backend, agent framework), TypeScript/JavaScript + React 18
(frontend)

**Primary Dependencies**: FastAPI, Google ADK (Agent Development Kit), Pydantic, SQLAlchemy +
`pgvector` client (asyncpg/psycopg), OpenAI-compatible SDK client (`openai` python SDK pointed at
custom `base_url`), React + Vite, plain CSS theo design token có sẵn trong mockup (không cần thêm
UI framework nặng)

**Storage**: PostgreSQL 16 + pgvector extension (chạy qua Docker/docker-compose) — 1 schema cho
Case/Session State + Trace/Observability, 1 schema/table cho RAG embeddings (pgvector)

**Testing**: pytest (backend unit + contract tests cho tool schema và `AppraisalReport`), Vitest/
React Testing Library (frontend component test tối thiểu cho 6 tab)

**Target Platform**: Web (chạy local qua Docker Compose cho demo hackathon — Postgres container +
FastAPI backend + React dev server)

**Project Type**: Web application (frontend + backend tách biệt, giao tiếp qua REST/JSON)

**Performance Goals**: Toàn bộ pipeline 1 case (7 lookup song song → định giá → rủi ro → advisory)
hoàn tất dưới 15 giây với mock data (SC-001); 7 lookup tool chạy song song, không tuần tự

**Constraints**: Không hardcode API key/base_url/model name (đọc từ `.env`); mọi kết quả hiển thị
phải kèm confidence/source_type (Nguyên tắc II); dữ liệu tin đồn/tâm linh tách biệt tuyệt đối khỏi
dữ liệu đã xác thực (Nguyên tắc III); giao diện phải khớp đúng token màu/layout của
`PAA_Mockup_SHB.html`

**Scale/Scope**: Demo hackathon — 1–2 khu vực mẫu, ~5-10 địa chỉ mock có sẵn dữ liệu đầy đủ, nhiều
case song song trong 1 phiên demo (không cần multi-tenant/multi-user auth)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá |
|---|---|
| I. Human-in-the-loop | PASS — `AppraisalReport` luôn có `requires_human_verification`; không có endpoint nào "tự động duyệt/từ chối" hồ sơ trong scope. |
| II. Explainable (confidence + source_type) | PASS — data-model.md bắt buộc `confidence` + `source_type` trên mọi entity tra cứu; frontend contract yêu cầu hiển thị kèm mọi số liệu. |
| III. Stigma Data Isolation | PASS — `AddressProfile.stigma_factors` là field tách biệt hoàn toàn khỏi `positive_factors`/`negative_factors`; Risk Scoring Engine chỉ cộng dồn có trọng số 10%, không loại trừ hồ sơ. |
| IV. Interface Contract chuẩn hoá | PASS — `contracts/appraisal-api.md` định nghĩa đúng 1 request/response schema, versioned, dùng mock Planner script để test độc lập. |
| V. 1 Orchestrator + 4 agent | PASS — Project Structure bên dưới phản ánh đúng 5 module backend (orchestrator + 4 agent) trên Google ADK. |
| VI. Mock Data Only + Disclaimer | PASS — toàn bộ dataset nằm dưới `backend/app/mockdata/`, frontend hiển thị banner disclaimer cố định. |

Không có vi phạm cần justify trong Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-property-appraisal-agent/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/            # Phase 1 output
│   └── appraisal-api.md
└── tasks.md              # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                     # FastAPI app entrypoint
│   ├── config.py                   # đọc .env: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, DB_URL...
│   ├── api/
│   │   ├── appraisal.py            # POST /appraisal-requests, GET /appraisal-requests/{id}
│   │   ├── chat.py                 # POST /cases/{id}/messages (chat tự do + Q&A copilot)
│   │   └── cases.py                # GET /cases (sidebar lịch sử hồ sơ), GET /cases/{id}
│   ├── orchestrator/
│   │   └── paa_orchestrator.py     # PAA Orchestrator (Google ADK), plan-act-observe loop
│   ├── agents/
│   │   ├── research_agent.py       # gọi 7 lookup tool song song
│   │   ├── valuation_agent.py      # calculate_valuation
│   │   ├── risk_agent.py           # calculate_asset_risk_score
│   │   └── advisory_agent.py       # query_knowledge_base, generate_report_draft
│   ├── tools/
│   │   ├── market_price_lookup.py
│   │   ├── planning_zoning_lookup.py
│   │   ├── legal_status_lookup.py
│   │   ├── neighborhood_amenity_lookup.py
│   │   ├── stigma_reputation_lookup.py
│   │   ├── environmental_risk_lookup.py
│   │   ├── liquidity_stat_lookup.py
│   │   ├── calculate_valuation.py
│   │   ├── calculate_asset_risk_score.py
│   │   ├── query_knowledge_base.py
│   │   └── generate_report_draft.py
│   ├── mockdata/
│   │   ├── transactions.json          # ComparableTransaction dataset
│   │   ├── price_index.json           # PriceIndexSeries theo phường/quận
│   │   ├── address_profiles.json      # AddressProfile (tốt/xấu/tâm linh)
│   │   ├── zoning.json
│   │   ├── legal_records.json
│   │   ├── amenities.json
│   │   ├── environmental_risk.json
│   │   ├── liquidity_stats.json
│   │   └── kb_documents/              # RAG source docs (quy trình, quy định, checklist mẫu)
│   ├── models/                         # SQLAlchemy models: CaseSession, TraceEvent, ChecklistItem...
│   ├── rag/
│   │   ├── embedder.py                 # gọi embedding model qua OpenAI-compatible client
│   │   └── ingest.py                   # nạp kb_documents/ vào pgvector
│   └── db/
│       ├── session.py
│       └── migrations/                 # SQL/Alembic
├── tests/
│   ├── contract/                       # test schema request/response theo contracts/appraisal-api.md
│   ├── integration/                    # test toàn pipeline với mock Planner
│   └── unit/                           # test từng tool/agent riêng lẻ
├── docker-compose.yml                  # postgres+pgvector, backend, (frontend dev optional)
├── Dockerfile
├── .env.example
└── requirements.txt

frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── theme/tokens.css                # copy nguyên token màu từ PAA_Mockup_SHB.html
│   ├── components/
│   │   ├── Sidebar/                    # lịch sử hồ sơ + nav
│   │   ├── ChatPane/                   # khung chat 30%
│   │   └── InfoPanel/
│   │       ├── SubtabBar.tsx
│   │       ├── Tab1Input.tsx
│   │       ├── Tab2Lookup.tsx
│   │       ├── Tab3Valuation.tsx
│   │       ├── Tab4Risk.tsx
│   │       ├── Tab5Checklist.tsx
│   │       └── Tab6Dashboard.tsx
│   ├── services/
│   │   └── apiClient.ts                # gọi backend theo contracts/appraisal-api.md
│   ├── state/
│   │   └── caseStore.ts                # state đồng bộ chat + info panel theo case đang mở
│   └── mocks/
│       └── mockPlannerScript.md        # hướng dẫn/script demo gọi PAA độc lập
└── tests/
    └── components/
```

**Structure Decision**: Option 2 (Web application) — tách `backend/` (FastAPI + Google ADK agents +
Postgres/pgvector) và `frontend/` (React) vì mockup đã định hình rõ 1 SPA giao tiếp REST với 1
backend orchestration service độc lập; đúng khớp interface contract (Nguyên tắc IV) cho phép 2 đội
làm song song.

## Complexity Tracking

*Không có vi phạm Constitution Check cần justify — bảng này để trống theo đúng hướng dẫn template.*
