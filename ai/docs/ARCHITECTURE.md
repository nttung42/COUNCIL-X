# Kiến trúc SHB AI — Digital Expert Agents

> **Trạng thái:** Design doc v1 (draft để code theo)
> **Sản phẩm đầu tiên:** PAA — Property Appraisal Agent (Thẩm định BĐS)
> **Nền tảng:** FastAPI (async) · SQLAlchemy 2 · Celery/Redis · LangGraph/LangChain · OpenRouter LLM

Tài liệu này mô tả kiến trúc **tổng quát cho một bộ Digital Expert Agent** (PAA, Credit, Legal…), lấy **PAA làm agent tham chiếu**. Mục tiêu: mỗi agent mới = thêm một package theo khuôn, không sửa core; expose ra **REST API** để BE/FE tiêu thụ.

---

## 1. Bối cảnh & phạm vi

SHB AI là nền tảng host các **agent chuyên gia số** phục vụ nghiệp vụ ngân hàng. Mỗi agent nhận một yêu cầu nghiệp vụ, chạy một quy trình nhiều bước (tra cứu → phân tích → chấm điểm → sinh báo cáo), và trả kết quả **có nguồn gốc + độ tin cậy + vết thực thi** để con người xem xét và ký duyệt.

- **Agent #1 — PAA (Thẩm định BĐS):** định giá tài sản đảm bảo, chấm rủi ro tài sản, đề xuất LTV, sinh nháp biên bản.
- **Agent #2, #3 (roadmap):** Credit Agent, Legal/Compliance Agent — dùng chung khung này.

Ranh giới: tài liệu này định nghĩa **khung + PAA**. Logic nghiệp vụ chi tiết (thuật toán ML định giá thật, tích hợp nguồn dữ liệu thật) được cắm dần qua các interface đã định sẵn.

---

## 2. Nguyên tắc kiến trúc

Vì là môi trường ngân hàng, mọi thiết kế bám 6 nguyên tắc:

1. **Provenance-first** — mọi dữ kiện đều kèm `source` (nguồn) và trạng thái `verified/unverified`.
2. **Confidence-scored** — mọi kết quả đều có `confidence ∈ [0,1]`; dữ liệu thấp tin cậy (vd tin đồn) chỉ để **cảnh báo tham khảo**, không được dùng để từ chối hồ sơ.
3. **Auditable** — toàn bộ pipeline ghi `ExecutionTrace` (ai chạy, khi nào, mất bao lâu, output gì) → tab Dashboard/Trace.
4. **Human-in-the-loop** — agent tạo *nháp*; trạng thái hồ sơ đi qua `draft → reviewed → signed`. Không tự động ra quyết định cuối.
5. **Pluggable** — Domain Agent, Lookup Adapter, Valuation Method, Risk Group đều là plugin có interface chuẩn + registry.
6. **Stateless services, stateful data** — service không giữ state trong RAM; mọi state nằm ở DB, cho phép scale ngang.

---

## 3. Tổng quan phân tầng

```
┌──────────────────────────────────────────────────────────────────┐
│ L1 · API REST (FastAPI)   — hợp đồng cho BE/FE                     │
│   /agents · /appraisals · /jobs · /files · /auth                  │
├──────────────────────────────────────────────────────────────────┤
│ L2 · Domain Agent Registry — khung tổng quát (PAA, Credit, Legal) │
│   BaseDomainAgent + AgentRegistry (auto-discovery)                │
├──────────────────────────────────────────────────────────────────┤
│ L3 · Agent Pipeline (LangGraph)  — riêng từng agent               │
│   PAA: Intake→[Lookup ∥]→Valuation→Risk→Checklist→Report          │
├──────────────────────────────────────────────────────────────────┤
│ L4 · Capability building blocks (tái sử dụng)                     │
│   Lookup Adapters · Valuation Engine · Risk Engine · Report/RAG   │
├──────────────────────────────────────────────────────────────────┤
│ L5 · Platform services                                            │
│   LLM gateway · Storage · Job queue (Celery) · Trace · Vector DB  │
├──────────────────────────────────────────────────────────────────┤
│ L6 · Persistence — PostgreSQL (+ pgvector) · Redis · Object store │
└──────────────────────────────────────────────────────────────────┘
```

Nguyên tắc phụ thuộc: **tầng trên gọi tầng dưới**, không ngược lại. L4 (capability) không biết gì về L1 (API).

---

## 4. Tầng L2 — Khung Domain Agent tổng quát

Đây là **điểm mở rộng cốt lõi**: mỗi agent mới hiện thực khung này.

### 4.1 Interface

```python
# shb/agents/base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel

class AgentCapability(BaseModel):
    """Mô tả một năng lực agent expose ra (tab trong UI)."""
    key: str                 # "lookup" | "valuation" | "risk" | "checklist" | "report"
    label: str               # nhãn hiển thị
    description: str

class AgentMeta(BaseModel):
    id: str                  # "paa"
    name: str                # "Thẩm định BĐS"
    domain: str              # "real_estate_appraisal"
    version: str = "0.1.0"
    capabilities: list[AgentCapability]
    input_schema_ref: str    # trỏ tới pydantic InputSchema
    is_async: bool = True    # agent nghiệp vụ nặng → luôn chạy async job

class AgentContext(BaseModel):
    """Context truyền xuyên suốt pipeline (DI cho nodes)."""
    request_id: str
    user_id: str
    agent_id: str
    # handles tới platform services (được inject lúc runtime)
    llm: object              # LLM gateway
    storage: object          # StorageService
    trace: object            # TraceRecorder
    emit: object             # callback đẩy status realtime (SSE/progress)

class BaseDomainAgent(ABC):
    meta: AgentMeta
    InputSchema: type[BaseModel]
    OutputSchema: type[BaseModel]

    @abstractmethod
    def build_graph(self) -> "CompiledGraph":
        """Trả về LangGraph đã compile cho agent này."""

    @abstractmethod
    async def run(self, input_data: BaseModel, ctx: AgentContext) -> BaseModel:
        """Entrypoint: khởi tạo state, chạy graph, trả OutputSchema."""
```

### 4.2 Registry (kế thừa cơ chế auto-discovery đang có)

`shb/agents/registry.py` quét thư mục `shb/agents/*/agent.py`, tìm lớp con `BaseDomainAgent`, đăng ký theo `meta.id`. Giống `AIServiceRegistry` hiện tại nhưng cho agent. **Giữ nguyên pattern discover_and_register** đã kiểm chứng.

> **Quan hệ với `BaseAIService` cũ:** `BaseAIService` (request→response đơn giản) vẫn dùng được cho "tool" nhẹ. `BaseDomainAgent` là bản mở rộng cho quy trình nhiều bước. Có thể để `BaseDomainAgent(BaseAIService)` hoặc tách hẳn `shb/agents/` — khuyến nghị **tách package `shb/agents/`** cho rõ ràng, `shb/ai/plugins/` giữ lại cho tool đơn giản.

---

## 5. Tầng L3 — PAA Pipeline (LangGraph)

PAA là một **state machine** chạy bằng LangGraph. Một `AppraisalState` chảy qua các node; node fan-out (lookup) chạy song song.

### 5.1 State

```python
# shb/agents/paa/state.py
class PropertySubject(BaseModel):
    address: str
    property_type: str        # "nha_pho" | "chung_cu" | "dat_nen"...
    area_m2: float
    declared_legal: str       # "so_hong" | "so_do"...
    loan_amount: float
    loan_purpose: str

class Provenance(BaseModel):
    source: str               # tên nguồn tra cứu
    verified: bool
    confidence: float         # 0..1
    retrieved_at: str

class LookupResult(BaseModel):
    adapter_key: str          # "comparable_sales" | "zoning" | ...
    status: str               # "verified" | "unverified" | "flag"
    data: dict                # payload riêng từng adapter
    provenance: Provenance

class ValuationResult(BaseModel):
    proposed_value: float
    value_low: float
    value_high: float
    price_per_m2: float
    confidence: float
    methods: list[dict]       # [{name, value, weight}]
    price_index_series: list[dict]

class RiskResult(BaseModel):
    score: int                # 0..100 (rủi ro TÀI SẢN, không phải tín dụng người vay)
    band: str                 # "thap" | "trung_binh" | "cao"
    ltv_recommended: float
    groups: list[dict]        # [{key, weight, score}]
    flags: list[dict]         # [{severity, title, detail, confidence, verified}]

class AppraisalState(BaseModel):
    request_id: str
    subject: PropertySubject
    lookups: list[LookupResult] = []
    valuation: ValuationResult | None = None
    risk: RiskResult | None = None
    checklist: list[dict] = []
    report_draft: str | None = None
    trace: list[dict] = []
```

### 5.2 Graph (các node)

```
          ┌──────────┐
   START →│  intake  │  chuẩn hóa PropertySubject, validate
          └────┬─────┘
               ▼
        ┌────────────── fan-out song song ──────────────┐
        │ comparable_sales · zoning · legal · amenities │   (Lookup Adapters)
        │ environment · liquidity · reputation          │
        └───────────────────┬───────────────────────────┘
                             ▼  (join: gộp list[LookupResult])
                       ┌───────────┐
                       │ valuation │  3 method → ensemble
                       └─────┬─────┘
                             ▼
                        ┌────────┐
                        │  risk  │  5 nhóm trọng số → score + LTV
                        └───┬────┘
                            ▼
                     ┌────────────┐
                     │ checklist  │  sinh checklist động từ flags
                     └─────┬──────┘
                           ▼
                     ┌────────────┐
                     │  report    │  RAG + kết quả → nháp biên bản
                     └─────┬──────┘
                           ▼
                          END → OutputSchema (aggregate)
```

Mỗi node: (1) đọc/ghi `AppraisalState`, (2) append một bản ghi vào `state.trace` với `t+`, (3) gọi `ctx.emit(status)` để đẩy tiến độ realtime. Fan-out lookup dùng `parallel` node của LangGraph hoặc `asyncio.gather` trong một node.

---

## 6. Tầng L4 — Capability building blocks

### 6.1 Lookup Adapter framework (dùng chung mọi agent)

```python
# shb/capabilities/lookup/base.py
from typing import Protocol

class AdapterResult(BaseModel):
    data: dict
    confidence: float
    source: str
    verified: bool

class LookupAdapter(Protocol):
    key: str                  # "comparable_sales"
    label: str
    async def lookup(self, subject: "PropertySubject") -> AdapterResult: ...
```

**7 adapter PAA** (mỗi cái 1 file, hiện thực interface trên):

| key | Trả về | verified | Ghi chú |
|---|---|---|---|
| `comparable_sales` | list giao dịch so sánh trong bán kính, giá/m² | ✔ | Nền cho valuation |
| `zoning` | tình trạng quy hoạch, lộ giới | ✔ | conf ~0.85 |
| `legal` | tình trạng sổ, tranh chấp, thế chấp | ✔ | conf ~0.95 |
| `amenities` | trường/chợ/bus/BV quanh khu | ✔ | |
| `environment` | ngập lụt, ô nhiễm | ✔/⚠ | ảnh hưởng risk vật lý |
| `liquidity` | ngày bán TB, tỷ lệ thành công | ✔ | ảnh hưởng risk thanh khoản |
| `reputation` | dư luận/tâm linh | ✘ | conf thấp, **chỉ cảnh báo** |

> **Cắm data thật:** mỗi adapter khai báo cấu hình nguồn (endpoint/DB) qua `Settings`. Giai đoạn đầu adapter đọc từ nguồn giả định có sẵn (bảng/DB nội bộ do bạn nạp); về sau thay bằng call API thật — **không đổi interface, không đụng pipeline**.

Adapter cũng đăng ký qua một `AdapterRegistry`; mỗi agent khai báo danh sách `adapter_keys` nó dùng → dễ thêm/bớt nguồn.

### 6.2 Valuation Engine

```python
# shb/capabilities/valuation/base.py
class ValuationMethod(Protocol):
    name: str                 # "direct_comparison" | "hedonic_ml" | "cost"
    async def estimate(self, subject, lookups) -> dict:  # {value, weight, detail}
        ...
```

Ensembler nhận kết quả 3 method → tính `proposed_value` (weighted), `value_low/high` (khoảng), `confidence` (dựa trên số & độ tương đồng giao dịch so sánh). Thêm method mới = thêm 1 class.

### 6.3 Risk Engine

```python
# shb/capabilities/risk/base.py
class RiskGroup(Protocol):
    key: str                  # "legal" | "liquidity" | "price_volatility" | "physical" | "reputation"
    weight: float             # 0.30, 0.25, 0.20, 0.15, 0.10
    async def score(self, state) -> dict:  # {score 0..100, evidence, confidence}
        ...
```

Tổng hợp có trọng số → `score` tổng, `band`, và **LTV đề xuất** theo bảng chính sách (map score→LTV, cấu hình được). Sinh `flags` từ các group có score/severity cao.

### 6.4 Report + Checklist

- **Checklist generator:** quy tắc — từ mỗi flag chưa xác thực / rủi ro cao → sinh một mục checklist hành động (vd "Khảo sát thực địa xác minh tin đồn"). Trạng thái mục lưu ở DB, FE toggle được.
- **Report drafter (RAG):** truy hồi mẫu biên bản + quy định nội bộ từ **vector store (pgvector)**, ghép với kết quả valuation/risk → LLM sinh nháp. Nháp lưu `ReportDraft`, thẩm định viên sửa & ký.

---

## 7. Mô hình dữ liệu (PostgreSQL)

Giữ `User/File` hiện có; thêm các bảng cho agent. Chuẩn hóa phần cần query, phần payload linh hoạt để JSONB.

| Bảng | Cột chính | Ghi chú |
|---|---|---|
| `agents` (tùy chọn) | id, name, domain, version, enabled | catalog agent (hoặc lấy từ registry) |
| `appraisals` | id, user_id, agent_id, subject(JSONB), status(`draft/processing/reviewed/signed/cancelled`), created_at | hồ sơ = 1 lần chạy PAA |
| `appraisal_lookups` | id, appraisal_id, adapter_key, status, data(JSONB), source, verified, confidence | 1 dòng / adapter |
| `valuations` | id, appraisal_id, proposed_value, low, high, price_per_m2, confidence, methods(JSONB), index_series(JSONB) | |
| `risk_assessments` | id, appraisal_id, score, band, ltv_recommended, groups(JSONB), flags(JSONB) | |
| `checklist_items` | id, appraisal_id, text, checked, auto_generated, source_flag | |
| `report_drafts` | id, appraisal_id, content(text), version, signed_by, signed_at | HITL |
| `chat_messages` | id, appraisal_id, role(`user/agent/status`), content, created_at | cho tab chat (giai đoạn sau) |
| `execution_traces` | id, appraisal_id, step, t_offset_ms, status, detail(JSONB) | tab Dashboard/Trace, phục vụ audit |
| `jobs` | (đã có) + agent_id | theo dõi async |

Dùng **Alembic** cho mọi thay đổi schema (bỏ `create_all` ở startup — xem §11).

---

## 8. Tầng L1 — Hợp đồng REST API (cho BE/FE)

Thiết kế **resource-oriented** quanh `appraisal`, ánh xạ 1-1 với 6 tab + chat của mockup. Auth qua header (xem §11). Mọi response bọc `provenance/confidence` ở cấp dữ kiện.

### 8.1 Catalog & tạo hồ sơ

```
GET  /api/v1/agents
     → [{id, name, domain, capabilities, input_schema}]   # FE render menu trái + form

POST /api/v1/appraisals
     body: { subject: PropertySubject }
     → 201 { appraisal_id, status: "processing", job_id }  # kick off async job
```

### 8.2 Đọc kết quả (map theo tab)

```
GET /api/v1/appraisals/{id}                → full aggregate (mọi tab)
GET /api/v1/appraisals/{id}/lookups        → tab 2  (list LookupResult)
GET /api/v1/appraisals/{id}/valuation      → tab 3
GET /api/v1/appraisals/{id}/risk           → tab 4
GET /api/v1/appraisals/{id}/checklist      → tab 5a
GET /api/v1/appraisals/{id}/report         → tab 5b
GET /api/v1/appraisals/{id}/trace          → tab 6  (execution timeline)
GET /api/v1/appraisals?limit&offset&status → sidebar "Lịch sử hồ sơ"
```

### 8.3 Tương tác (human-in-the-loop)

```
PATCH  /api/v1/appraisals/{id}/checklist/{item_id}   body: {checked: bool}
PUT    /api/v1/appraisals/{id}/report                body: {content}   # sửa nháp
POST   /api/v1/appraisals/{id}/report/sign           body: {role}      # ký duyệt
DELETE /api/v1/appraisals/{id}                        # huỷ hồ sơ
```

### 8.4 Realtime & chat (giai đoạn 2 — chỉ định nghĩa contract)

```
GET  /api/v1/appraisals/{id}/stream   (SSE)   # đẩy status "Đang gọi 7 adapter…", % tiến độ
POST /api/v1/appraisals/{id}/chat     body: {message}  → {reply}  (LLM over hồ sơ)
GET  /api/v1/appraisals/{id}/messages         # lịch sử chat
```

### 8.5 Shape ví dụ (một dữ kiện có provenance)

```json
// GET /appraisals/{id}/lookups → 1 phần tử
{
  "adapter_key": "reputation",
  "status": "unverified",
  "data": { "summary": "Tin đồn dân cư chưa xác thực về sự việc 2019" },
  "provenance": { "source": "tra cứu dư luận khu vực", "verified": false,
                  "confidence": 0.30, "retrieved_at": "2026-07-18T09:12:03Z" }
}
```

FE dùng `verified` + `confidence` để render badge (Đã xác thực / Chưa xác thực / lưu ý).

---

## 9. Thực thi async & streaming

- **Pipeline nặng chạy Celery job** (đã có hạ tầng). `POST /appraisals` tạo bản ghi + `send_task` → worker chạy `build_graph().ainvoke(state)`.
- **Tiến độ:** node gọi `ctx.emit(step, pct)` → ghi `execution_traces` + publish lên **Redis pub/sub**. Endpoint `/stream` (SSE) subscribe kênh của `appraisal_id` → đẩy về FE. Giai đoạn 1 có thể **poll** `GET /appraisals/{id}` (field `status`,`progress`) trước khi làm SSE.
- **Idempotency:** `POST /appraisals` nhận `Idempotency-Key` (header) để tránh tạo trùng khi FE retry.

---

## 10. Cấu trúc thư mục đề xuất

```
src/shb/
├── agents/                      # L2+L3 — mỗi agent 1 package
│   ├── base.py                  # BaseDomainAgent, AgentMeta, AgentContext
│   ├── registry.py              # AgentRegistry (auto-discovery)
│   └── paa/
│       ├── agent.py             # PAAAgent(BaseDomainAgent)
│       ├── schemas.py           # InputSchema / OutputSchema
│       ├── state.py             # AppraisalState + sub-models
│       ├── graph.py             # định nghĩa LangGraph
│       └── nodes/
│           ├── intake.py
│           ├── lookup.py        # fan-out gọi adapters
│           ├── valuation.py
│           ├── risk.py
│           ├── checklist.py
│           └── report.py
├── capabilities/                # L4 — khối tái sử dụng cho mọi agent
│   ├── lookup/
│   │   ├── base.py              # LookupAdapter, AdapterResult, AdapterRegistry
│   │   └── paa/                 # 7 adapter của PAA (comparable_sales.py, zoning.py …)
│   ├── valuation/               # ValuationMethod + ensembler
│   ├── risk/                    # RiskGroup + aggregator
│   └── report/                  # RAG drafter + checklist rules
├── api/v1/endpoints/
│   ├── agents.py                # GET /agents
│   ├── appraisals.py            # CRUD + sub-resources (§8)
│   ├── jobs.py  files.py  auth.py   # (đã có)
├── core/                        # config, db, security, celery (đã có)
├── db/models.py                 # + bảng §7
├── services/                    # job_service, storage_service (đã có) + trace_service
├── ai/
│   ├── llm.py                   # LLM gateway (đã có)
│   └── rag/                     # vector store (pgvector) client
└── workers/tasks.py             # celery task chạy agent graph
```

Thêm agent mới (Credit/Legal) = thêm `agents/<id>/` + `capabilities/<...>/<id>/`, **không sửa core/api chung** (endpoint `/agents` + registry tự nhận). Nếu agent cần resource riêng (không phải "appraisal") thì thêm router riêng theo cùng khuôn.

---

## 11. Cross-cutting (bắt buộc trước production)

Kế thừa các blocker đã nêu ở review kiến trúc trước:

- **Auth:** API-key (BE↔BE) đã có; với FE nên đi **FE → BE của bạn → SHB AI** (đừng để key ở browser). Cân nhắc JWT ngắn hạn nếu FE gọi thẳng.
- **Migrations:** dùng **Alembic**, bỏ `Base.metadata.create_all` + seed user mặc định ở `init_db()` (backdoor). Seed chỉ chạy ở môi trường dev qua script riêng.
- **CORS:** whitelist domain FE, **không** `["*"] + allow_credentials`.
- **Secrets:** `secret_key`/`LLM_API_KEY` bắt buộc từ env/secret manager, fail-fast nếu thiếu.
- **Rate limit / quota:** chặn abuse endpoint gọi LLM (tốn tiền) — theo user & theo agent.
- **Storage:** chuyển file sang **object storage (S3/MinIO)** khi chạy >1 instance.
- **Observability:** request-id, structured logging, tách `/health` (liveness) & `/ready` (readiness: DB+Redis), Sentry, metrics token/latency (đã có bảng `plugin_runs`/trace).
- **Compliance:** `execution_traces` là bản ghi audit — không xoá, gắn `request_id` xuyên suốt; PII trong `subject` cần chính sách lưu trữ/mã hoá.

---

## 12. Ánh xạ vào skeleton hiện có

| Thành phần hiện có | Hành động |
|---|---|
| `BaseAIService` + `registry` (`ai/plugins`) | **Giữ** — dùng cho tool đơn giản; PAA dùng `agents/` mở rộng |
| Celery + Redis + `jobs` | **Tái dùng** nguyên cho async agent |
| `ai/llm.py` (OpenRouter) | **Tái dùng** làm LLM gateway |
| `storage_service` / `files` | **Tái dùng**; nâng lên object storage sau |
| `db/models.py` | **Mở rộng** thêm bảng §7 (qua Alembic) |
| `core/config.py` | **Mở rộng** thêm cấu hình adapter/agent/vector store |
| `main.py` lifespan discovery | **Nhân bản** cho `AgentRegistry` |

Không cần viết lại; đây là **mở rộng có kiểm soát** trên nền đã có.

---

## 13. Roadmap theo giai đoạn

- **GĐ0 — Khung agent:** `agents/base.py` + `registry` + endpoint `/agents`; migrate sang Alembic; hardening blocker §11.
- **GĐ1 — PAA lõi (6 tab, sync-ish):** state + graph + 7 adapter (data giả định) + valuation/risk (heuristic) + checklist/report (LLM) + `/appraisals` REST + chạy qua Celery, FE poll.
- **GĐ2 — Realtime & chat:** SSE `/stream` (Redis pub/sub) + `/chat`.
- **GĐ3 — Chiều sâu nghiệp vụ:** thay adapter bằng nguồn thật; hedonic-ML thật; RAG mẫu biên bản (pgvector); bảng chính sách LTV.
- **GĐ4 — Agent #2/#3:** Credit, Legal theo cùng khuôn.

---

*Ghi chú: tài liệu là bản thiết kế để hiện thực dần. Cập nhật khi chốt chi tiết từng capability.*
