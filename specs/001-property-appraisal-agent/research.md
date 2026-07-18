# Phase 0 Research: Property Appraisal Agent (PAA) MVP

Không có mục `[NEEDS CLARIFICATION]` nào còn lại trong Technical Context của plan.md — toàn bộ
tech stack đã được người dùng chốt trực tiếp (FastAPI, Google ADK, OpenAI-compatible LLM qua custom
base_url, React, PostgreSQL+pgvector qua Docker). Tài liệu này ghi lại quyết định + rationale +
alternative đã cân nhắc cho từng lựa chọn, để khỏi phải research lại giữa chừng implement.

## 1. Agent framework: Google ADK

- **Decision**: Dùng Google Agent Development Kit (ADK) cho PAA Orchestrator và 4 sub-agent, thay
  vì LangGraph/CrewAI như gợi ý ban đầu trong design doc gốc.
- **Rationale**: Người dùng đã chỉ định ADK làm techstack bắt buộc. ADK hỗ trợ sẵn multi-agent
  (SequentialAgent, ParallelAgent) khớp đúng nhu cầu: Research Agent cần `ParallelAgent` (7 tool
  song song), còn Valuation → Risk → Advisory cần chạy tuần tự (`SequentialAgent` hoặc orchestrator
  tự gọi tuần tự bằng code). ADK hỗ trợ function tool khai báo kiểu Python function, khớp thẳng với
  tool spec ở mục 8 design doc.
- **Alternatives considered**: LangGraph (đề xuất gốc trong design doc, mạnh về explicit state
  graph) và CrewAI (role-based, đơn giản hơn) — không chọn vì đã có yêu cầu kỹ thuật cụ thể dùng ADK.

## 2. LLM kết nối qua OpenAI-compatible custom base_url

- **Decision**: Dùng `openai` Python SDK (hoặc client tương thích OpenAI Chat Completions/Responses
  API), khởi tạo với `base_url` và `api_key` đọc từ biến môi trường (`LLM_BASE_URL`, `LLM_API_KEY`,
  `LLM_MODEL`). Google ADK hỗ trợ custom model wrapper (LiteLLM hoặc OpenAI-compatible adapter) —
  dùng adapter này để ADK agent gọi được model qua endpoint tuỳ chỉnh thay vì Gemini mặc định.
- **Rationale**: Yêu cầu rõ ràng "model: openai compatible, cấu hình trong env" — không hardcode
  provider. Việc tách cấu hình vào `.env`/`config.py` cho phép đổi model/endpoint (vd. self-hosted
  vLLM, Azure OpenAI, hay Anthropic-compatible gateway) mà không sửa code.
- **Alternatives considered**: Gọi thẳng Gemini API mặc định của ADK — không chọn vì yêu cầu kỹ
  thuật của người dùng chỉ định rõ OpenAI-compatible endpoint.

## 3. Database: PostgreSQL + pgvector qua Docker

- **Decision**: 1 container Postgres 16 với extension `pgvector` bật qua `docker-compose.yml`. Dùng
  2 nhóm bảng: (a) bảng quan hệ chuẩn cho CaseSession/TraceEvent/ChecklistItem (state/observability
  store), (b) 1 bảng `kb_chunks` có cột `embedding vector(N)` cho RAG.
- **Rationale**: 1 engine DB duy nhất giảm độ phức tạp vận hành cho demo hackathon (so với tách
  riêng Postgres cho state + Chroma/FAISS cho vector như design doc gốc đề xuất) — vẫn đáp ứng đúng
  yêu cầu kỹ thuật "postgres + postgres vector, chạy Docker" của người dùng.
- **Alternatives considered**: Chroma/FAISS riêng cho RAG (đề xuất gốc trong design doc mục 9) —
  không chọn vì người dùng đã chỉ định rõ pgvector.

## 4. Frontend: React, không thêm UI framework nặng

- **Decision**: React + Vite, giữ nguyên CSS token/layout đã thiết kế sẵn trong
  `PAA_Mockup_SHB.html` (biến CSS `--navy-900`, `--orange-600`...), convert HTML/CSS tĩnh thành
  component React tương ứng 1:1 (Sidebar, ChatPane, InfoPanel + 6 tab con).
- **Rationale**: Mockup đã có đầy đủ token màu đã kiểm tra độ tương phản (đạt WCAG, ghi rõ trong
  comment CSS) và layout chi tiết — việc dùng lại nguyên token giảm rủi ro lệch thiết kế và tiết
  kiệm thời gian hackathon so với thiết kế lại từ đầu bằng 1 UI kit khác (MUI/Ant Design).
- **Alternatives considered**: Ant Design/MUI — không chọn vì mockup đã có design system riêng đủ
  chi tiết để implement thẳng, thêm UI kit ngoài sẽ tốn thời gian remap token.

## 5. Real-time đồng bộ Chat ↔ Info Panel

- **Decision**: Backend trả kết quả từng bước qua polling ngắn (`GET /cases/{id}` mỗi 1–2s) hoặc
  Server-Sent Events (SSE) `GET /cases/{id}/stream` cho MVP — ưu tiên SSE vì đơn giản hơn WebSocket
  và đủ dùng cho luồng 1 chiều "server đẩy trạng thái mới".
- **Rationale**: FastAPI hỗ trợ SSE dễ dàng (`StreamingResponse`), không cần thêm hạ tầng WebSocket
  cho demo hackathon; đáp ứng đúng yêu cầu "agent tự chuyển tab theo thời gian thực" (FR-011) mà
  không phải áp dụng đủ over-engineering.
- **Alternatives considered**: WebSocket hai chiều — không cần thiết vì chat gửi lên vẫn dùng REST
  POST bình thường, chỉ có chiều server→client cần đẩy cập nhật.

## 6. Mock Planner (test độc lập theo Nguyên tắc IV)

- **Decision**: Viết 1 script Python đơn giản (`scripts/mock_planner.py`) gửi
  `PropertyAppraisalRequest` mẫu tới `POST /appraisal-requests` và in ra `AppraisalReport` nhận
  được — dùng cho contract test và cho demo "PAA hoạt động độc lập không cần Planner thật".
- **Rationale**: Theo đúng khuyến nghị của design doc gốc mục 8 và Nguyên tắc IV của constitution.
- **Alternatives considered**: Không có — đây là yêu cầu tường minh, không có phương án khác.
