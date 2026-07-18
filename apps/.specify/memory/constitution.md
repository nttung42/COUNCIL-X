<!--
Sync Impact Report
- Version change: [TEMPLATE] → 1.0.0 (initial ratification)
- Modified principles: none (first fill of template)
- Added sections: Core Principles (I–VI), Additional Constraints (Tech Stack),
  Development Workflow (Agent Parallelization), Governance
- Removed sections: none
- Templates requiring updates:
  ✅ .specify/templates/plan-template.md (Constitution Check section — generic, compatible)
  ✅ .specify/templates/spec-template.md (no changes needed)
  ✅ .specify/templates/tasks-template.md (no changes needed)
  ⚠ README.md / docs/quickstart.md — not yet created (deferred, no follow-up blocking)
- Follow-up TODOs: none — all placeholders resolved from project docs
  (PROBLEM-STATEMENT-SHB2.pdf, PAA_KienTruc_HighLevel.md, SHB_ThamDinhBDS_DesignDoc_2.md)
-->
# PAA — Property Appraisal Agent Constitution

## Core Principles

### I. Con người luôn quyết định cuối cùng (Human-in-the-loop, NON-NEGOTIABLE)
PAA là executor agent hỗ trợ thẩm định viên, KHÔNG thay thế quyết định tín dụng.
Mọi output (định giá, điểm rủi ro, checklist, nháp biên bản) là **đề xuất**, không
phải quyết định tự động. Hệ thống KHÔNG được tự động từ chối/khoá hồ sơ dựa trên bất
kỳ tool hay agent nào. Biên bản thẩm định luôn kết thúc bằng bước ký duyệt của con
người (`requires_human_verification` phải luôn hiện diện trong output).
Rationale: đây là ràng buộc pháp lý/đạo đức của nghiệp vụ ngân hàng, không phải giới
hạn kỹ thuật — nêu rõ trong đề bài và trong design doc gốc.

### II. Minh bạch & Explainable (Confidence + Source Type bắt buộc)
Mọi dữ liệu trả về từ lookup tool, mọi kết quả định giá/rủi ro PHẢI kèm: phương pháp
tính, nguồn dữ liệu, `confidence` (0–1), và `source_type` (`mock` / `verified` /
`unverified_rumor`). Không được trình bày một con số tuyệt đối mà không có khoảng
tin cậy (value_range) hay confidence_score đi kèm — tránh false precision.
Rationale: thẩm định viên cần audit trail để giải thích quyết định trước khách hàng
và kiểm toán nội bộ.

### III. Tin đồn/tâm linh không phải căn cứ từ chối (Stigma Data Isolation)
Nhóm dữ liệu `stigma_reputation_lookup` (tin đồn, yếu tố tâm linh, sự kiện chưa xác
thực) LUÔN được gắn `verified=false` và confidence thấp, tách biệt tuyệt đối khỏi dữ
kiện pháp lý đã xác thực. Risk Scoring Engine chỉ được dùng nhóm này để tạo **flag
cảnh báo yêu cầu xác minh thực địa**, tuyệt đối không dùng làm căn cứ chính để tính
điểm loại trừ hồ sơ hay từ chối tín dụng.
Rationale: tránh rủi ro pháp lý/đạo đức khi từ chối tín dụng dựa trên tin đồn chưa
kiểm chứng (nêu rõ trong design doc §4.1 và §11).

### IV. Interface Contract chuẩn hoá & Phát triển độc lập
PAA expose đúng 1 interface contract: nhận `property_appraisal_request`, trả
`AppraisalReport` (JSON). Interface này KHÔNG được thay đổi phá vỡ tương thích khi
thêm tính năng nội bộ. Mọi agent con (Research/Valuation/Risk/Advisory) và tool phải
test được độc lập bằng mock input/output, không phụ thuộc Planner Agent thật hay các
digital expert agent khác (Credit/Legal/Operations) đã được xây hay chưa — dùng mock
Planner script để demo/test toàn bộ pipeline.
Rationale: cho phép phát triển, test, demo PAA độc lập trong thời gian hackathon hạn
chế, đúng tinh thần "executor agent" của kiến trúc multi-agent tổng.

### V. Kiến trúc 1 Orchestrator + 4 Agent chuyên trách
PAA PHẢI được cấu trúc thành PAA Orchestrator + 4 agent chuyên trách (Research,
Valuation, Risk Assessment, Advisory), mỗi agent sở hữu tool riêng, xây trên Google
ADK (Agent Development Kit). Research Agent chạy 7 lookup tool song song; Valuation/
Risk/Advisory chạy tuần tự vì phụ thuộc dữ liệu bước trước. Mỗi agent hoàn tất tương
ứng đúng 1 tab trên Info Panel UI (Research→tab 2, Valuation→tab 3, Risk→tab 4,
Advisory→tab 5) — Orchestrator điều phối chuyển tab tự động, đồng thời cho phép
người dùng bấm tay chuyển tab.
Rationale: song song hoá đúng chỗ, đồng bộ tab tự nhiên, dễ test/mở rộng độc lập
(xem PAA_KienTruc_HighLevel.md §4).

### VI. Mock Data Only — Disclaimer bắt buộc
Toàn bộ dữ liệu dùng trong MVP hackathon (giao dịch so sánh, chỉ số giá, hồ sơ pháp
lý/môi trường/dư luận, RAG knowledge base) là **synthetic/mock**, được thiết kế theo
adapter pattern để thay bằng nguồn thật sau này mà không đổi interface. Giao diện và
báo cáo sinh ra PHẢI disclaimer rõ ràng đây là dữ liệu mô phỏng, tránh gây hiểu lầm là
số liệu ngân hàng thật.
Rationale: yêu cầu minh bạch demo hackathon, tránh rủi ro compliance khi trình bày dữ
liệu giả như dữ liệu thật.

## Additional Constraints — Tech Stack

- **Backend**: FastAPI (Python), expose orchestration endpoint + tool endpoints theo
  interface contract ở Nguyên tắc IV.
- **Agent framework**: Google ADK (Agent Development Kit) cho Orchestrator và 4 agent
  chuyên trách; function calling chuẩn hoá theo tool spec (mục 8 design doc).
- **LLM**: model OpenAI-compatible, kết nối qua custom `base_url` — KHÔNG hardcode
  provider/endpoint/API key trong code; toàn bộ cấu hình (`base_url`, `api_key`,
  `model_name`) đọc từ biến môi trường (`.env`), có `.env.example` mẫu.
- **Database**: PostgreSQL + pgvector (chạy qua Docker/docker-compose) — PostgreSQL
  cho Session/Case State Store + Trace/Observability Store; pgvector cho RAG
  Knowledge Base (Nguyên tắc V).
- **Frontend**: React.js, tuân thủ đúng layout/màu sắc/hành vi trong
  `PAA_Mockup_SHB.html` (chat 30% trái, info panel 70% phải, 6 tab, sidebar lịch sử
  hồ sơ, SHB brand tokens navy/orange).
- **Không thêm phụ thuộc phá vỡ minh bạch**: mọi service bên thứ 3 gọi thật (nếu có,
  ngoài phạm vi MVP) phải qua adapter pattern giữ nguyên interface mock.

## Development Workflow — Agent Parallelization

- Task phát triển PAA được chia theo ranh giới module đã tách bạch trong kiến trúc
  (Nguyên tắc V): mock data, mỗi lookup adapter, Valuation Engine, Risk Scoring
  Engine, RAG/Advisory, Orchestrator, Output Formatter/interface contract, và React
  frontend — mỗi module CÓ THỂ giao cho 1 agent/dev thực hiện song song vì đã có
  interface/schema chuẩn hoá làm hợp đồng giữa các phần.
- Mock data (JSON schema + dataset mẫu theo mục 5 design doc) PHẢI hoàn thành hoặc
  chốt schema TRƯỚC KHI các module phụ thuộc (Lookup adapters, Valuation, Risk) bắt
  đầu, để tránh rework khi chạy song song.
- Mọi PR/thay đổi liên quan đến tool schema hoặc `AppraisalReport` schema phải được
  review đối chiếu với interface contract (Nguyên tắc IV) trước khi merge.

## Governance

Constitution này supersede mọi quy ước code style/kiến trúc không chính thức khác
trong dự án. Mọi thay đổi kiến trúc lớn (đổi số lượng agent, đổi interface contract,
đổi nguyên tắc xử lý dữ liệu tin đồn) phải cập nhật constitution trước, kèm Sync
Impact Report, rồi mới cập nhật `plan.md`/`tasks.md` liên quan.

**Amendment procedure**: sửa trực tiếp file này, tăng version theo semver (MAJOR:
loại bỏ/đổi nghĩa nguyên tắc; MINOR: thêm nguyên tắc/mở rộng; PATCH: làm rõ câu chữ),
cập nhật `LAST_AMENDED_DATE`, và rà soát lại `plan-template.md`/`spec-template.md`/
`tasks-template.md` xem có cần đồng bộ không.

**Compliance review**: trước khi `/speckit-implement` chạy bất kỳ task nào, đối chiếu
task đó với Nguyên tắc I–III (human-in-the-loop, explainability, stigma isolation) —
đây là 3 nguyên tắc có rủi ro đạo đức/pháp lý cao nhất của domain ngân hàng.

**Version**: 1.0.0 | **Ratified**: 2026-07-18 | **Last Amended**: 2026-07-18
