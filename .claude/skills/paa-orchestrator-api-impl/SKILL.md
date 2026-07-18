---
name: paa-orchestrator-api-impl
description: "Cách wiring Google ADK ParallelAgent/SequentialAgent với custom OpenAI-compatible model, và checklist implement từng FastAPI endpoint của PAA theo contracts/appraisal-api.md. Dùng khi viết code cho backend/app/agents/*.py, backend/app/orchestrator/paa_orchestrator.py, backend/app/api/*.py."
---

# Implement PAA Orchestrator (Google ADK) & FastAPI Layer

## Wiring custom OpenAI-compatible model vào Google ADK

ADK mặc định trỏ Gemini; để dùng LLM OpenAI-compatible qua `base_url` tuỳ chỉnh, dùng model wrapper
LiteLLM (ADK hỗ trợ `LiteLlm` model adapter) hoặc client OpenAI-compatible trực tiếp nếu ADK version
đang dùng hỗ trợ:

```python
from google.adk.models.lite_llm import LiteLlm
from app.config import settings

model = LiteLlm(
    model=f"openai/{settings.llm_model}",
    api_base=settings.llm_base_url,
    api_key=settings.llm_api_key,
)
```

Nếu phiên bản ADK cài đặt không có `LiteLlm` hoặc tương đương, viết 1 adapter mỏng tự gọi
`openai.OpenAI(base_url=..., api_key=...).chat.completions.create(...)` bên trong 1 custom ADK
`BaseLlm` subclass — ghi rõ trong report cuối version ADK đã dùng và cách đã wiring, để dev khác dễ
tái hiện.

## Research Agent — chạy 7 tool song song

```python
from google.adk.agents import ParallelAgent, LlmAgent

research_agent = ParallelAgent(
    name="research_agent",
    sub_agents=[
        LlmAgent(name="market_price", model=model, tools=[market_price_lookup]),
        LlmAgent(name="zoning", model=model, tools=[planning_zoning_lookup]),
        # ... 5 tool còn lại
    ],
)
```

Nếu cách tổ chức ADK thực tế không khớp pattern trên (tuỳ version), fallback đơn giản và chắc chắn
hơn cho MVP: KHÔNG bắt buộc phải bọc mỗi tool trong 1 `LlmAgent` riêng — có thể gọi thẳng
`await asyncio.gather(market_price_lookup(...), planning_zoning_lookup(...), ...)` trong 1 hàm
Python thường và coi đó là "Research Agent" ở mức orchestration (miễn là 7 lookup chạy song song
thật sự, đúng SC-001) — ưu tiên chắc chắn chạy được hơn là đúng 100% idiom ADK.

## Valuation/Risk/Advisory Agent — tuần tự

Theo Nguyên tắc V (constitution): 3 agent này PHỤ THUỘC dữ liệu bước trước, dùng
`SequentialAgent` (hoặc gọi tuần tự bằng code thường trong orchestrator, tương tự fallback ở trên
nếu ADK API không khớp).

## paa_orchestrator.py — luồng chính

```python
async def run_appraisal_pipeline(case_id: str, request: PropertyAppraisalRequest):
    await log_trace(case_id, "Hệ thống tiếp nhận yêu cầu", t_offset=0.0)
    lookup_result = await research_agent.run(request.subject_property)
    await save_case_field(case_id, "lookup_result_json", lookup_result)
    await log_trace(case_id, "7 nguồn tra cứu chạy song song hoàn tất", ...)

    valuation_result = await valuation_agent.run(request.subject_property, lookup_result)
    await save_case_field(case_id, "valuation_result_json", valuation_result)
    await log_trace(case_id, "Bộ máy định giá hoàn tất", ...)

    risk_result = await risk_agent.run(valuation_result, lookup_result)
    await save_case_field(case_id, "risk_result_json", risk_result)
    await log_trace(case_id, "Bộ máy chấm điểm rủi ro hoàn tất", ...)

    advisory_result = await advisory_agent.run(request.subject_property, valuation_result, risk_result)
    await save_case_field(case_id, "checklist_json", advisory_result.checklist)
    await save_case_field(case_id, "report_draft_json", advisory_result.draft_report)
    await log_trace(case_id, "Copilot sinh nháp biên bản", ...)

    await set_case_status(case_id, "completed")
```

Mỗi `log_trace` gọi ghi 1 dòng `TraceEvent` VÀ đẩy 1 SSE event (nếu có subscriber đang mở
`/api/cases/{id}/stream`) — dùng `asyncio.Queue` hoặc broadcast đơn giản per-case-id trong bộ nhớ
process (đủ dùng cho demo hackathon single-process, không cần Redis pub/sub).

## Checklist endpoint theo contracts/appraisal-api.md

| Endpoint | Việc cần làm | Điểm cần chú ý |
|---|---|---|
| `POST /api/appraisal-requests` | tạo `CaseSession` (status=processing), spawn
  `run_appraisal_pipeline` bất đồng bộ (background task), trả 202 ngay | KHÔNG block request chờ
  pipeline chạy xong |
| `GET /api/cases/{id}/stream` | SSE, đẩy `TraceEvent` mới + `active_tab` suy ra từ `step_name` | đóng
  stream khi `status=completed` |
| `GET /api/cases/{id}` | trả đầy đủ state + `trace_events` sort theo `t_offset_seconds` | 404 nếu
  không tồn tại |
| `GET /api/cases` | list kèm filter `status` optional | dùng cho sidebar |
| `PATCH /api/cases/{id}/checklist/{item_id}` | update 1 item trong `checklist_json` | 404 nếu
  item_id không tồn tại trong checklist của case |
| `POST /api/cases/{id}/cancel` | set status=cancelled | 409 nếu đã `completed` |
| `POST /api/cases/{id}/messages` | gọi `query_knowledge_base` + LLM, append `chat_history_json` | KHÔNG
  sửa `valuation_result_json`/`risk_result_json` |

Mọi lỗi trả `{error_code, message, field_errors}` — viết 1 exception handler chung
(`app.add_exception_handler`) thay vì lặp lại ở từng endpoint.
