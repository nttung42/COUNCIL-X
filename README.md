# SME Credit Assessment Platform

Nền tảng AI dạng module cho công đoạn thẩm định tín dụng SME của ngân hàng. Mỗi nhóm
nghiệp vụ là một module độc lập, có thể chạy riêng, tích hợp vào LOS/workflow hiện có,
hoặc kết hợp với các module khác thành một hệ thống thẩm định hoàn chỉnh. Kiến trúc đầy đủ của toàn nền tảng nằm ở
[`docs/kien-truc-ai-modular-tham-dinh-tin-dung-sme.md`](docs/kien-truc-ai-modular-tham-dinh-tin-dung-sme.md).

## Bản đồ toàn nền tảng

```
SME CREDIT ASSESSMENT PLATFORM
│
├── 0. Shared Foundation           Case Context · Orchestrator · Document/Entity
│                                  Intelligence · Policy & Knowledge · Calculation
│                                  Engine · Evidence Graph · QA · Human Review · Audit
│
├── 1. Business & Industry Assessment    Mô hình kinh doanh, ngành, tập trung khách
│                                        hàng/nhà cung cấp, mùa vụ, rủi ro người chủ chốt
├── 2. Legal Assessment                  Tư cách pháp nhân, thẩm quyền ký, giấy phép
├── 3. Financial Analysis                Chuẩn hoá & phân tích BCTC, tỷ số tài chính
├── 4. Cash-flow & Repayment Capacity    Dòng tiền thực, DSCR, dự báo, stress test
├── 5. Collateral Assessment
│   └── Real Estate Appraisal
│       (Vehicle / Machinery / Inventory / Receivable Appraisal)
├── 6. Credit Rating                     Tổng hợp điểm tài chính + phi tài chính + hành vi
├── 7. Credit Structuring                Hạn mức, kỳ hạn, covenant, phương án thay thế
└── 8. Cross-module Review & Synthesis   Phát hiện mâu thuẫn, phản biện, tổng hợp cuối
```

Mỗi module giải quyết đúng một năng lực, không lấn sang việc của module khác (Financial
Analysis không tự định giá tài sản, Collateral Assessment không tự chấm credit rating...).
Site map đầy đủ, kể cả theo từng vai trò người dùng (RM, chuyên viên tín dụng, pháp lý,
định giá, Risk, Checker), nằm ở §3 và §11 của tài liệu kiến trúc.

## Lộ trình & cách các module liên kết

| GĐ | Module | Trạng thái |
|---|---|---|
| **1** | **Thẩm định Bất động sản bảo đảm** (repo này) | ✅ **Released** |
| 2 | Financial Analysis + Cash-flow Verification | 🔜 Coming soon |
| 3 | Business & Industry Assessment | 🔜 Coming soon |
| 4 | Legal Assessment | 🔜 Coming soon |
| 5 | Credit Rating | 🔜 Coming soon |
| 6 | Credit Structuring | 🔜 Coming soon |
| 7 | Cross-module Review & Devil's Advocate | 🔜 Coming soon |
| 8 | Tích hợp ngân hàng thật (LOS, DMS, Core Banking, IAM, model/policy registry) | 🔜 Coming soon |

Các module không đứng độc lập tuyệt đối — chúng liên kết qua **output contract chuẩn**:
mỗi module trả về `findings`, `metrics`, `risk flags`, `confidence`, `evidence`,
`assumptions`, `policy references`, `human review status`, `module version`, `data
version`, để module sau dùng lại trực tiếp thay vì nhập lại từ đầu. Ví dụ chuỗi tái sử
dụng theo đúng thiết kế:

```
Dữ liệu doanh thu đã xác minh (Financial Analysis, GĐ2)
  → Cash-flow Analysis (GĐ2)
  → Credit Rating (GĐ5)
  → Credit Structuring (GĐ6)
  → Approval Summary (GĐ7)
```

Và ở GĐ2: kết quả định giá tài sản (từ module này) kết hợp với kết quả dòng tiền để ra
hai giới hạn hạn mức — theo khả năng trả nợ và theo tài sản bảo đảm. Chi tiết cơ chế
Module Orchestrator, Evidence Graph và Policy Layer dùng chung cho việc kết nối này nằm ở
§8 tài liệu kiến trúc.

## Module đã released: Thẩm định Bất động sản bảo đảm

### Kiến trúc

```
Frontend (apps/frontend)
        │  X-API-Key
        ▼
┌─────────────────────────────────────────────────────────┐
│ FastAPI  /api/v1/{auth,services,jobs,files}              │
├─────────────────────────────────────────────────────────┤
│ AIServiceRegistry — tự quét & đăng ký plugin lúc khởi động│
│   ├─ property_intake  (is_async=True)  ──▶ Celery job     │
│   └─ property_lookup  (is_async=False) ──▶ chạy trong request│
├─────────────────────────────────────────────────────────┤
│ capabilities/  — lớp SQL tái sử dụng (đọc bảng paa.*)     │
│   lookup/ (7 adapter)  · valuation/  · risk/  · dashboard/│
├─────────────────────────────────────────────────────────┤
│ PostgreSQL (schema paa, 23 bảng) · Redis (Celery broker)  │
└─────────────────────────────────────────────────────────┘
```

### Trạng thái theo từng thành phần

Thiết kế đầy đủ của module này (§10 tài liệu kiến trúc) là một pipeline 10 agent:
`Orchestrator → Intake & Extraction → Legal Screening → Research → Comparable Selection →
Valuation → Risk & Liquidity → Field Inspection → LTV Engine → Report → QA & Evidence`.

| Thành phần | Trong code | Trạng thái |
|---|---|---|
| Intake & Extraction Agent | Plugin `property_intake` | ✅ Chạy được, có `confidence` + trích dẫn nguồn |
| Research Agent (một phần) | Plugin `property_lookup` | ✅ Chạy được, đọc 7 nguồn tra cứu đã seed sẵn |
| Comparable Selection Agent | Bảng `market_comparable` | 🟡 Có dữ liệu, chưa có logic chọn/loại outlier |
| Legal Screening (hard blocker) | Category `legal_status` | 🟡 Có dữ liệu, chưa có bước dừng cứng |
| Valuation Agent | `valuation_result`/`capabilities/valuation/` | ⚪ Có mô hình dữ liệu, chưa có plugin |
| Risk & Liquidity Agent | `risk_assessment_result`/`capabilities/risk/` | ⚪ Có mô hình dữ liệu, chưa có plugin |
| LTV Calculation Engine | Bảng `risk_ltv_policy_band` (đã seed 4 khung) | ⚪ Có cấu hình, chưa có engine tính |
| Field Inspection Agent | — | ⚪ Chưa thiết kế |
| Report Agent | Xuất HTML tĩnh phía frontend | 🟡 Có báo cáo, chưa qua AI/RAG |
| QA & Evidence Agent | `confidence`/`source_doc`/`status` có sẵn trong output | 🟡 Có evidence ở tầng dữ liệu, chưa có agent kiểm tra chéo |
| Appraisal Orchestrator | `AIServiceRegistry` | 🟡 Gọi được plugin qua API, chưa điều phối phụ thuộc giữa các bước |

Chi tiết kỹ thuật đầy đủ — tech stack, cách cài đặt, API, hợp đồng JSON từng plugin — nằm
ở [`ai/README.md`](ai/README.md) (backend) và [`apps/frontend/README.md`](apps/frontend/README.md)
(giao diện).

## Cấu trúc repo

```
aiinnovation/
├── README.md
├── docs/
│   └── kien-truc-ai-modular-tham-dinh-tin-dung-sme.md   Kiến trúc đầy đủ 8 module + roadmap
├── ai/                         Backend: FastAPI + plugin property_intake/property_lookup
│   ├── README.md
│   ├── docs/                   ARCHITECTURE.md, PRD, hợp đồng JSON của từng plugin
│   ├── PAA_Schema_PostgreSQL.sql   Mô hình dữ liệu 23 bảng
│   └── PAA_Mockup_SHB_8.html        Mockup tĩnh — nguồn thiết kế UI gốc
└── apps/
    └── frontend/               Giao diện thẩm định viên (React + TypeScript)
        └── README.md
```

## Chạy thử nhanh

```bash
# Backend (cần 2 terminal: API + Celery worker — xem ai/README.md mục 4)
cd ai && cp .env.example .env   # rồi sửa LLM_API_KEY
docker compose up               # hoặc chạy native, xem ai/README.md

# Frontend
cd apps/frontend
npm install && npm run dev      # http://localhost:5173, mặc định chạy demo không cần backend
```

## Tài liệu liên quan

- [Kiến trúc nền tảng đầy đủ (8 module + roadmap)](docs/kien-truc-ai-modular-tham-dinh-tin-dung-sme.md)
- [README backend](ai/README.md) · [README frontend](apps/frontend/README.md)
- [Kiến trúc kỹ thuật module hiện tại](ai/docs/ARCHITECTURE.md) · [Schema dữ liệu 23 bảng](ai/PAA_Schema_PostgreSQL.sql)
