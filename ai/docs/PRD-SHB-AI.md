# PRD — SHB AI

> **Phiên bản:** 0.1 (Draft)
> **Mục đích tài liệu:** Đây là Product Requirements Document được viết để dùng làm input cho **Claude Code** triển khai dự án. Tài liệu mô tả *cái gì* cần xây và *vì sao*, đồng thời nêu đủ ràng buộc kỹ thuật để Claude Code tự quyết định chi tiết *làm như thế nào*.

---

## 1. Tổng quan

**SHB AI** là một **platform tập hợp nhiều AI tool** dùng chung một hạ tầng. Thay vì mỗi tính năng AI là một ứng dụng riêng lẻ, SHB AI cung cấp một "buffet" các công cụ — người dùng chọn tool, đưa input, nhận kết quả — trong khi nền tảng lo phần xác thực, gọi LLM, lưu trữ, và xử lý tác vụ chạy nền.

Một số tool ví dụ (sẽ mở rộng dần):
- Tóm tắt cuộc họp (meeting summarization)
- Tóm tắt tài liệu (document summarization)
- Chuyển giọng nói thành văn bản (speech-to-text)

**Giá trị cốt lõi:** *thêm một tool mới phải dễ* — chỉ cần khai báo một module tuân theo interface chuẩn, không cần sửa hạ tầng. Đây là yêu cầu kiến trúc quan trọng nhất của dự án.

---

## 2. Mục tiêu & Phi mục tiêu

### 2.1 Mục tiêu (Goals)
- G1: Xây dựng backend platform cho phép **đăng ký và chạy nhiều AI tool** qua API thống nhất.
- G2: Định nghĩa một **Tool Plugin Interface** chuẩn để mở rộng tool mới mà không đụng vào core.
- G3: Hỗ trợ **tác vụ chạy nền (async jobs)** vì nhiều tool xử lý lâu (transcribe audio, tóm tắt tài liệu dài).
- G4: Dùng **LangGraph** để mô hình hóa workflow nhiều bước của từng tool, **LangChain** để trừu tượhóa việc gọi LLM/embedding.
- G5: Lưu trữ người dùng, job, và kết quả vào **PostgreSQL**.
- G6: Có sẵn 3 tool MVP hoạt động end-to-end.

### 2.2 Phi mục tiêu (Non-goals) — giai đoạn này
- Không xây dựng frontend/UI (chỉ làm API; UI là pha sau).
- Không làm hệ thống billing/thanh toán.
- Không tự host/fine-tune model riêng (dùng API của nhà cung cấp LLM + Whisper).
- Không làm multi-tenant phức tạp (org/team) — chỉ user đơn giản ở MVP.

---

## 3. Người dùng & Use case

| Vai trò | Mô tả | Use case chính |
|---|---|---|
| End user | Người dùng cuối qua API (về sau qua UI) | Chọn tool → gửi input → nhận kết quả |
| Developer (nội bộ) | Người thêm tool mới | Viết một package tool tuân theo interface, đăng ký vào registry |

**Luồng người dùng tiêu biểu:**
1. User gọi `GET /tools` để xem danh sách tool khả dụng + schema input.
2. User gọi `POST /tools/{tool_id}/run` với input (text hoặc file).
3. Nếu tool chạy nhanh → trả kết quả ngay (sync). Nếu chạy lâu → trả về `job_id` (async).
4. User poll `GET /jobs/{job_id}` cho tới khi `status = completed` và lấy `result`.

---

## 4. Phạm vi MVP

MVP gồm:
- Core platform: config, kết nối DB, LLM provider abstraction, tool registry.
- Tool Plugin Interface + cơ chế auto-discovery tool.
- Hệ thống job async (queue + worker) cho tác vụ dài.
- API: liệt kê tool, chạy tool, tra cứu job, upload file.
- 3 tool: **doc_summary**, **meeting_summary**, **speech_to_text**.
- Auth dạng API key đơn giản (header `X-API-Key`).
- Docker Compose để chạy local (app + postgres + worker).
- Migration bằng Alembic. Test cơ bản cho core và từng tool.

---

## 5. Kiến trúc tổng thể

```
                 ┌─────────────────────────────────────────────┐
                 │                 FastAPI App                  │
                 │  /tools  /tools/{id}/run  /jobs  /files      │
                 └───────────────┬─────────────────────────────┘
                                 │
              ┌──────────────────┼───────────────────┐
              │                  │                   │
        Tool Registry      Job Service          Storage Service
        (discover &        (tạo/track job)      (lưu file upload)
         load tools)             │
              │                  │
              │            ┌──────▼───────┐        ┌──────────────┐
              │            │  Job Queue   │───────▶│   Worker(s)  │
              │            │  (Postgres)  │        │  chạy tool   │
              │            └──────────────┘        └──────┬───────┘
              │                                           │
              ▼                                           ▼
   ┌────────────────────┐                    ┌────────────────────────┐
   │  Tools (buffet)    │                    │  Workflows (LangGraph)  │
   │  - doc_summary     │  mỗi tool định     │  graph nhiều bước       │
   │  - meeting_summary │  nghĩa 1 graph     │  dùng LangChain để gọi  │
   │  - speech_to_text  │ ─────────────────▶ │  LLM / embedding / STT  │
   └────────────────────┘                    └───────────┬─────────────┘
                                                          │
                                              ┌───────────▼───────────┐
                                              │  LLM / STT providers  │
                                              │  (OpenAI, Whisper…)   │
                                              └───────────────────────┘

        Tất cả state (users, tools meta, jobs, results) ──▶ PostgreSQL
```

**Quyết định kiến trúc then chốt:**
- **Tool = plugin**: mỗi tool là một package độc lập tuân theo `BaseTool`. Core không biết chi tiết tool nào, chỉ làm việc qua interface.
- **Workflow = LangGraph**: logic xử lý nhiều bước của tool được mô hình hóa thành một graph (state machine), dễ thêm bước, retry, branching.
- **Async-first**: tool tự khai báo `is_async`. Tool dài chạy qua worker; tool ngắn chạy đồng bộ trong request.
- **Queue trên Postgres ở MVP**: để giảm phụ thuộc hạ tầng, dùng bảng `jobs` + worker poll (`SELECT ... FOR UPDATE SKIP LOCKED`). Có thể thay bằng Celery/Redis sau (xem §13).

---

## 6. Tech stack

| Lớp | Công nghệ | Ghi chú |
|---|---|---|
| API | **FastAPI** + Uvicorn | async, Pydantic v2 cho schema |
| Orchestration | **LangGraph** | mô hình hóa workflow từng tool |
| LLM abstraction | **LangChain** | gọi LLM, embedding, prompt templates |
| Database | **PostgreSQL** | qua SQLAlchemy 2.x (async) + Alembic migration |
| Job queue | Postgres-backed (MVP) | worker process riêng |
| File storage | Local volume (MVP) | abstraction sẵn để chuyển S3 sau |
| Speech-to-text | Whisper (API hoặc faster-whisper local) | LangChain không transcribe — cần provider riêng |
| Config | Pydantic Settings + `.env` | |
| Đóng gói | Docker + docker-compose | app, worker, postgres |
| Quản lý dependency | `uv` hoặc `poetry` (Claude Code chọn) | Python 3.11+ |
| Test | pytest + pytest-asyncio | |

> **Lưu ý cho Claude Code:** trước khi cố định version của LangChain/LangGraph/FastAPI, hãy kiểm tra phiên bản ổn định mới nhất tại thời điểm code và pin lại trong file dependency. API của LangGraph/LangChain thay đổi khá nhanh giữa các minor version.

---

## 7. Tool Plugin Architecture (phần quan trọng nhất)

Mỗi tool kế thừa một lớp `BaseTool` và khai báo: metadata, schema input/output, cờ async, và một hàm `run` (hoặc một LangGraph graph). Registry tự quét thư mục `app/tools/` để nạp tất cả tool.

### 7.1 Interface (mô tả — Claude Code hoàn thiện code)

```python
# app/tools/base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel

class ToolMeta(BaseModel):
    id: str                 # vd: "doc_summary"
    name: str               # tên hiển thị
    description: str
    version: str = "0.1.0"
    is_async: bool = False  # True nếu cần chạy qua worker
    accepts_file: bool = False
    file_types: list[str] = []   # vd: ["pdf", "docx", "txt"]

class BaseTool(ABC):
    meta: ToolMeta
    InputSchema: type[BaseModel]   # Pydantic model cho input
    OutputSchema: type[BaseModel]  # Pydantic model cho output

    @abstractmethod
    async def run(self, input_data: BaseModel, ctx: "ToolContext") -> BaseModel:
        """Thực thi tool. Với tool phức tạp, gọi vào LangGraph graph bên trong."""
```

- `ToolContext`: chứa các tiện ích dùng chung — LLM client (qua LangChain), đường dẫn file, user_id, logger, hàm cập nhật progress của job.
- **Quy ước thêm tool mới:** tạo `app/tools/<tool_id>/` gồm `tool.py` (class kế thừa `BaseTool`), `schema.py`, `graph.py` (LangGraph nếu cần), `prompts/`. Đăng ký tự động — không sửa core.

### 7.2 Registry
- `app/tools/registry.py` quét `app/tools/*` lúc khởi động, import các class `BaseTool`, validate `meta.id` là duy nhất, và build dict `{tool_id: tool_instance}`.
- API `GET /tools` đọc từ registry để trả về metadata + JSON schema của input.

### 7.3 Workflow bằng LangGraph
- Tool nào có nhiều bước (chunk → map → reduce, hay nhiều agent) thì định nghĩa một `StateGraph` trong `graph.py`.
- State của graph là một TypedDict/Pydantic chứa input, các kết quả trung gian, output.
- Tool đơn giản (1 lần gọi LLM) có thể chạy thẳng trong `run` mà không cần graph.

---

## 8. Data Model (PostgreSQL)

> Đây là mô hình tham chiếu; Claude Code có thể tinh chỉnh tên cột/kiểu cho phù hợp.

**users**
- `id` (uuid, pk), `email`, `api_key_hash`, `is_active`, `created_at`

**jobs**
- `id` (uuid, pk)
- `user_id` (fk → users)
- `tool_id` (text)
- `status` (enum: `pending` | `running` | `completed` | `failed` | `cancelled`)
- `input` (jsonb)          — input đã validate
- `input_file_path` (text, nullable)
- `result` (jsonb, nullable)
- `error` (text, nullable)
- `progress` (int 0–100, default 0)
- `created_at`, `started_at`, `finished_at`
- index: `(status, created_at)` để worker poll hiệu quả

**files**
- `id` (uuid, pk), `user_id`, `original_name`, `stored_path`, `content_type`, `size_bytes`, `created_at`

**tool_runs** (tuỳ chọn — log/analytics)
- `id`, `job_id`, `tool_id`, `tokens_used`, `latency_ms`, `model`, `created_at`

---

## 9. API Design

Tất cả endpoint yêu cầu header `X-API-Key`.

| Method | Path | Mô tả |
|---|---|---|
| `GET` | `/tools` | Liệt kê tool + metadata + input schema |
| `GET` | `/tools/{tool_id}` | Chi tiết 1 tool |
| `POST` | `/tools/{tool_id}/run` | Chạy tool. Sync → trả result; async → trả `job_id` (202) |
| `POST` | `/files` | Upload file (multipart), trả `file_id` |
| `GET` | `/jobs/{job_id}` | Trạng thái + result của job |
| `GET` | `/jobs` | Danh sách job của user (phân trang) |
| `DELETE` | `/jobs/{job_id}` | Huỷ job đang `pending` |
| `GET` | `/health` | Health check |

**Quy ước chạy tool:**
- Body của `/tools/{id}/run` được validate bằng `tool.InputSchema`. Nếu tool nhận file, body tham chiếu `file_id` đã upload trước.
- `tool.meta.is_async == False` → xử lý trong request, trả `200` + result.
- `tool.meta.is_async == True` → tạo `job` (`pending`), trả `202` + `job_id`. Worker sẽ xử lý.

**Ví dụ response của `GET /tools`:**
```json
[
  {
    "id": "doc_summary",
    "name": "Tóm tắt tài liệu",
    "description": "Tóm tắt tài liệu PDF/DOCX/TXT",
    "is_async": true,
    "accepts_file": true,
    "file_types": ["pdf", "docx", "txt"],
    "input_schema": { "...": "JSON schema từ Pydantic" }
  }
]
```

---

## 10. Xử lý Job bất đồng bộ

- **Tạo job:** API ghi 1 dòng `jobs` với `status=pending`.
- **Worker:** process riêng (`app/workers/worker.py`), vòng lặp poll DB:
  - `SELECT ... FROM jobs WHERE status='pending' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1`
  - đặt `status=running`, `started_at=now()`
  - load tool từ registry, gọi `tool.run(input, ctx)`; cập nhật `progress` qua `ctx`
  - thành công → `status=completed`, lưu `result`; lỗi → `status=failed`, lưu `error`
- **Retry/timeout:** job quá thời gian tối đa → đánh dấu `failed`. (Cấu hình số worker, timeout qua env.)
- **Mở rộng sau:** thay bằng Celery + Redis/RabbitMQ nếu cần scale — interface `JobService` giữ nguyên.

---

## 11. Cấu trúc thư mục đề xuất

```
shb-ai/
├── app/
│   ├── main.py                 # khởi tạo FastAPI, load registry
│   ├── core/
│   │   ├── config.py           # Pydantic Settings
│   │   ├── db.py               # async engine, session
│   │   ├── security.py         # xác thực API key
│   │   ├── llm.py              # LangChain LLM/embedding provider
│   │   └── logging.py
│   ├── models/                 # SQLAlchemy models (user, job, file...)
│   ├── schemas/                # Pydantic request/response chung
│   ├── api/
│   │   ├── deps.py             # dependencies (auth, db session)
│   │   └── routers/            # tools.py, jobs.py, files.py, health.py
│   ├── services/
│   │   ├── job_service.py
│   │   └── storage_service.py
│   ├── tools/                  # 🍱 BUFFET
│   │   ├── base.py             # BaseTool, ToolMeta, ToolContext
│   │   ├── registry.py
│   │   ├── doc_summary/
│   │   │   ├── tool.py
│   │   │   ├── schema.py
│   │   │   ├── graph.py        # LangGraph: load → chunk → map → reduce
│   │   │   └── prompts/
│   │   ├── meeting_summary/
│   │   └── speech_to_text/
│   └── workers/
│       └── worker.py
├── alembic/                    # migrations
├── tests/
│   ├── test_registry.py
│   ├── test_api_tools.py
│   └── tools/                  # test riêng từng tool
├── docker-compose.yml          # app + worker + postgres
├── Dockerfile
├── pyproject.toml
├── .env.example
└── README.md
```

---

## 12. Đặc tả 3 tool MVP

### 12.1 `doc_summary` — Tóm tắt tài liệu
- **Input:** `file_id` (PDF/DOCX/TXT), tuỳ chọn `length` (`short`|`medium`|`long`), `language`.
- **Async:** có.
- **Workflow (LangGraph):** parse file → chunk theo token → map (tóm tắt từng chunk) → reduce (gộp thành bản tóm tắt cuối) → (tuỳ chọn) trích key points.
- **Output:** `summary` (text), `key_points` (list), `word_count`, `language`.

### 12.2 `meeting_summary` — Tóm tắt cuộc họp
- **Input:** `transcript` (text) **hoặc** `file_id` audio; tuỳ chọn `language`.
- **Async:** có.
- **Workflow:** nếu là audio → gọi tool/dịch vụ STT lấy transcript trước → tóm tắt → trích **action items** (ai, việc gì, hạn) + **decisions**.
- **Output:** `summary`, `action_items` (list of {owner, task, due}), `decisions` (list), `participants` (nếu suy ra được).
- **Ghi chú:** có thể tái sử dụng `speech_to_text` ở bước transcribe.

### 12.3 `speech_to_text` — Chuyển giọng nói thành văn bản
- **Input:** `file_id` audio (mp3/wav/m4a), tuỳ chọn `language`.
- **Async:** có.
- **Xử lý:** dùng Whisper (OpenAI API hoặc faster-whisper local — Claude Code chọn theo cấu hình env). **Không** dùng LangChain cho bước transcribe.
- **Output:** `transcript` (text), `segments` (tuỳ chọn: {start, end, text}), `language`.

---

## 13. Yêu cầu phi chức năng (NFR)

- **Cấu hình:** mọi secret/khoá API qua biến môi trường; có `.env.example`.
- **Bảo mật:** API key hash khi lưu; validate kích thước/loại file upload; giới hạn dung lượng.
- **Khả năng mở rộng:** thêm tool mới = thêm 1 package, không sửa core; storage và job queue ẩn sau interface để đổi backend (S3, Redis/Celery) mà không phá API.
- **Quan sát:** log có cấu trúc; mỗi `tool_run` ghi tokens/latency/model.
- **Hiệu năng:** tool dài luôn async; worker chạy song song nhiều job (cấu hình số worker).
- **Độ tin cậy:** job lỗi không làm sập worker; có retry/timeout cơ bản.
- **Chất lượng code:** type hints đầy đủ; test cho registry, API tool, và mỗi tool MVP.

---

## 14. Lộ trình triển khai (cho Claude Code)

**Pha 0 — Khởi tạo**
- Scaffold project, pyproject, docker-compose (app + postgres + worker), config, kết nối DB, Alembic, `/health`.

**Pha 1 — Core platform**
- `BaseTool`/`ToolMeta`/`ToolContext`, registry auto-discovery.
- LLM provider qua LangChain (`core/llm.py`).
- API `/tools`, `/tools/{id}/run` (mới hỗ trợ sync), auth API key.

**Pha 2 — Async jobs + files**
- Model `jobs`, `files`; `JobService`, `StorageService`; worker poll Postgres.
- API `/files`, `/jobs/{id}`, `/jobs`, hỗ trợ tool async.

**Pha 3 — Tool MVP**
- `doc_summary` (LangGraph map-reduce) → `speech_to_text` (Whisper) → `meeting_summary` (tái dùng STT + trích action items).

**Pha 4 — Hoàn thiện**
- Test, README hướng dẫn chạy + cách thêm tool mới, ví dụ request mẫu (curl/HTTPie).

---

## 15. Tiêu chí nghiệm thu (Acceptance Criteria)

- `docker compose up` chạy được app + postgres + worker; `GET /health` trả OK.
- `GET /tools` trả về đúng 3 tool kèm input schema.
- Thêm một tool "hello world" mới chỉ bằng cách tạo package trong `app/tools/` mà **không sửa** file core nào → tool tự xuất hiện trong `/tools`.
- Chạy `doc_summary` với 1 PDF nhiều trang → nhận `job_id`, poll tới `completed`, có `summary` hợp lý.
- Chạy `speech_to_text` với 1 file audio → nhận transcript.
- Chạy `meeting_summary` với transcript → nhận summary + action items.
- Job lỗi (vd file sai định dạng) → `status=failed` kèm `error`, worker vẫn sống.
- Có test pass cho registry, API `/tools`, và 3 tool.

---

## 16. Giả định & Câu hỏi mở

**Giả định đã chọn (điều chỉnh nếu cần):**
- A1: Chỉ làm **backend/API**, chưa có UI.
- A2: Auth = **API key** đơn giản, chưa làm OAuth/đăng nhập user đầy đủ.
- A3: Job queue = **Postgres-backed** ở MVP (chưa Celery/Redis).
- A4: File lưu **local volume**, có abstraction để chuyển S3.
- A5: LLM provider mặc định là một nhà cung cấp qua API (cấu hình bằng env); STT dùng Whisper.

**Câu hỏi mở cần bạn xác nhận:**
- Q1: Nhà cung cấp LLM ưu tiên là gì (OpenAI / Anthropic / Azure / local)? Có ràng buộc chi phí không?
- Q2: STT muốn dùng **API** hay chạy **local** (faster-whisper)? Yêu cầu về ngôn ngữ tiếng Việt/Nhật?
- Q3: Có cần multi-user/phân quyền ngay không, hay user đơn giản là đủ cho MVP?
- Q4: Mục tiêu triển khai (chỉ chạy local, hay deploy lên cloud cụ thể)?
- Q5: Có ưu tiên tool nào làm trước trong 3 tool MVP không?
