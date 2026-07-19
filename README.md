# Collateral Appraisal Platform

Nền tảng thẩm định tài sản bảo đảm có AI hỗ trợ, tập trung vào trải nghiệm làm việc của chuyên viên thẩm định: tiếp nhận hồ sơ, đọc tài liệu, tra cứu dữ liệu, định giá, đánh giá rủi ro, kiểm tra evidence và xuất báo cáo.

Sản phẩm hiện có MVP cho **thẩm định Bất động sản** và khung mở rộng cho 3 phân hệ tiếp theo: **Động sản**, **Giấy tờ có giá**, **Quyền tài sản / tài sản hình thành trong tương lai**.

AI trong hệ thống đóng vai trò trợ lý xử lý và đề xuất. Kết quả quan trọng vẫn cần chuyên viên xác nhận, chỉnh sửa hoặc bổ sung evidence trước khi dùng trong báo cáo.

---

## Product hiện có gì

### 1. Bất động sản — MVP đang vận hành

Phân hệ Bất động sản là phần đã được triển khai sâu nhất, gồm frontend workspace và backend AI services cho các bước chính của quy trình thẩm định.

| Năng lực | Trạng thái | Mô tả |
|---|---|---|
| Nhập thông tin tài sản | Đã có backend AI | Upload tài liệu, chạy `property_intake`, trích xuất field bằng LLM/OCR, trả confidence, nguồn tài liệu, snippet và bbox. |
| Tra cứu dữ liệu | Đã có backend logic | `property_lookup` đọc dữ liệu tra cứu từ DB, trả đủ 7 nhóm: giá thị trường, quy hoạch, pháp lý, tiện ích, môi trường, thanh khoản, dư luận/tâm linh. |
| Định giá | Đã có backend engine | `property_valuation` tính giá trị bằng 3 phương pháp: so sánh trực tiếp, hedonic/ML, chi phí; có confidence factors và điều chỉnh AI bị chặn trong ±5%. |
| Rủi ro & LTV | Đã có backend engine | `property_risk` tính risk score tài sản theo 5 nhóm trọng số và map sang LTV policy band. Không dùng LLM cho phần quyết định tiền. |
| Dashboard / báo cáo | Lai thật + demo | Frontend tổng hợp dữ liệu đã có; một phần trace/report vẫn dùng mock để demo luồng đầy đủ. |
| Human review | Frontend flow | Có pending edit, confirm, review action; backend audit/review đầy đủ là bước production hóa tiếp theo. |

### 2. Nền tảng đa phân hệ tài sản

Frontend đã có navigation và workspace mock cho 4 phân hệ tài sản bảo đảm:

| Phân hệ | Trạng thái | Nội dung sản phẩm |
|---|---|---|
| Bất động sản | MVP | Nhà đất, căn hộ, đất ở, tài sản gắn liền với đất. |
| Động sản | Coming soon backend | Xe, máy móc thiết bị, hàng hóa, hàng tồn kho; kiểm tra serial, quyền sở hữu, tình trạng, khấu hao, thanh khoản. |
| Giấy tờ có giá | Coming soon backend | Trái phiếu, cổ phiếu, chứng chỉ tiền gửi, kỳ phiếu; kiểm tra lưu ký, issuer risk, market liquidity, haircut. |
| Quyền tài sản | Coming soon backend | Quyền đòi nợ, khoản phải thu, quyền phát sinh từ hợp đồng, tài sản hình thành trong tương lai; đánh giá pháp lý, dòng tiền, recovery scenario, milestone. |

---

## Kiến trúc ngắn gọn

```text
apps/frontend
  React + TypeScript + Vite
  ├─ Collateral platform pages
  ├─ Real-estate MVP workspace
  ├─ Future-domain workspaces
  └─ Evidence / Report center

ai
  FastAPI + Celery + PostgreSQL + Redis
  ├─ AIServiceRegistry
  ├─ property_intake
  ├─ property_lookup
  ├─ property_valuation
  ├─ property_risk
  └─ capabilities/ engines + SQL access
```

Backend dùng mô hình plugin: mỗi năng lực AI/engine là một service độc lập trong `ai/src/shb/ai/plugins/*`. `AIServiceRegistry` tự quét và đăng ký plugin khi app khởi động, nên thêm nghiệp vụ mới không cần sửa router core.

Tác vụ nhanh chạy đồng bộ. Tác vụ dài như OCR, định giá hoặc risk chạy qua Celery job và có thể stream tiến độ bằng SSE.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Zustand, CSS tokens |
| Backend API | FastAPI, Pydantic v2, SQLAlchemy 2.x |
| Worker | Celery |
| Queue / result backend | Redis |
| Database | PostgreSQL, Alembic |
| AI/OCR | Gateway tương thích OpenAI qua `LLM_BASE_URL` |
| Python package manager | uv |
| Frontend package manager | npm |

---

## Routes chính

| Route | Màn hình |
|---|---|
| `/` | Tổng quan nền tảng |
| `/appraisals` | Danh sách hồ sơ thẩm định |
| `/appraisals/:caseId` | Chi tiết hồ sơ |
| `/asset-domains` | Hub phân hệ tài sản |
| `/asset-domains/real-estate/:caseId` | Workspace Bất động sản MVP |
| `/asset-domains/movable-assets/:caseId` | Workspace Động sản |
| `/asset-domains/valuable-papers/:caseId` | Workspace Giấy tờ có giá |
| `/asset-domains/property-rights/:caseId` | Workspace Quyền tài sản |
| `/evidence` | Evidence Center |
| `/reports` | Report Center |

Legacy routes `/cases/...` vẫn được giữ để không vỡ demo cũ.

---

## Backend services

| Service | Type | Endpoint | Status |
|---|---|---|---|
| `property_intake` | Async job | `POST /api/v1/services/property_intake/run` | Implemented |
| `property_lookup` | Sync | `POST /api/v1/services/property_lookup/run` | Implemented |
| `property_valuation` | Async job + SSE | `POST /api/v1/services/property_valuation/run` | Implemented |
| `property_risk` | Async job + SSE | `POST /api/v1/services/property_risk/run` | Implemented |

API docs tự sinh tại:

```text
http://localhost:8888/docs
```

---

## Chạy local

### Backend

```bash
cd ai
cp .env.example .env
# Sửa .env: LLM_BASE_URL, LLM_API_KEY, SECRET_KEY

docker compose up
```

Backend chạy tại:

```text
http://localhost:8888
```

Chạy native:

```bash
cd ai
uv sync
cp .env.example .env
alembic upgrade head
uv run uvicorn shb.main:app --reload
uv run celery -A shb.core.celery_app worker --loglevel=info
```

Trên Windows, Celery có thể cần:

```bash
uv run celery -A shb.core.celery_app worker --loglevel=info --pool=solo
```

### Frontend

```bash
cd apps/frontend
npm install
npm run dev
```

Frontend chạy tại:

```text
http://localhost:5173
```

Mặc định frontend chạy được bằng mock data. Muốn nối backend thật:

```bash
# apps/frontend/.env
VITE_API_BASE_URL=http://localhost:8888
```

---

## Kiểm tra

```bash
# Backend
cd ai
uv run pytest

# Frontend
cd apps/frontend
npm run build
npm run lint
```

---

## Cấu trúc repo

```text
COUNCIL-X/
├── README.md
├── docs/
│   ├── collateral-appraisal-platform-plan.md
│   └── fe-spec-3-phan-he-tham-dinh-tuong-lai-clear.md
├── ai/
│   ├── README.md
│   ├── docs/
│   │   ├── ARCHITECTURE.md
│   │   ├── valuation-methodology.md
│   │   ├── risk-methodology.md
│   │   └── contracts/
│   ├── src/shb/ai/plugins/
│   │   ├── property_intake/
│   │   ├── property_lookup/
│   │   ├── property_valuation/
│   │   └── property_risk/
│   └── PAA_Schema_PostgreSQL.sql
└── apps/frontend/
    ├── README.md
    └── src/
        ├── app/
        ├── components/
        ├── features/
        ├── mocks/
        ├── services/
        └── state/
```

---

## Tài liệu liên quan

- [Implementation plan](docs/collateral-appraisal-platform-plan.md)
- [Frontend spec cho 3 phân hệ tương lai](docs/fe-spec-3-phan-he-tham-dinh-tuong-lai-clear.md)
- [Backend README](ai/README.md)
- [Frontend README](apps/frontend/README.md)
- [Valuation methodology](ai/docs/valuation-methodology.md)
- [Risk methodology](ai/docs/risk-methodology.md)
- [Property intake contract](ai/docs/contracts/property-intake-contract.md)
- [Property lookup contract](ai/docs/contracts/property-lookup-contract.md)
- [Property valuation contract](ai/docs/contracts/property-valuation-contract.md)
- [Property risk contract](ai/docs/contracts/property-risk-contract.md)
