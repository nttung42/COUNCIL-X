# PAA — SQL schema + SQL-backed tools (Alembic)

> Ghi chú đi kèm PR/commit thêm schema PAA + lớp "tool" SQL cho agent. Xem
> `docs/ARCHITECTURE.md` §6, §7, §12 cho bối cảnh thiết kế gốc.

## Những gì được thêm

1. **`src/shb/db/models_paa.py`** — ORM (SQLAlchemy 2.0) cho toàn bộ 23 bảng
   PAA (Màn 1–5 + bảng dùng chung), port 1:1 từ `PAA_Schema_PostgreSQL.sql`
   (đã validate độc lập trên Postgres 16), điều chỉnh để tương thích cả
   SQLite (test) lẫn Postgres (production) — xem docstring đầu file để biết
   chi tiết các điều chỉnh (JSON thay TEXT[], enum generic thay vì trigger/view
   Postgres-only...).
2. **`src/shb/db/__init__.py`** — import `models_paa` làm side-effect để
   `Base.metadata` luôn có đủ bảng PAA dù ai import `shb.db.models` từ đâu
   (Alembic, test, hay code khác) — không cần sửa `alembic/env.py` hay
   `tests/conftest.py`.
3. **`alembic/versions/002_paa_schema.py`** — migration tạo toàn bộ enum +
   bảng + index + seed 4 dòng `risk_ltv_policy_band`, nối tiếp `001`.
4. **`src/shb/capabilities/`** — lớp "tool" SQL cho agent, theo đúng khung
   `LookupAdapter` phác thảo ở `docs/ARCHITECTURE.md` §6.1:
   - `lookup/base.py` — `AdapterResult`, `LookupAdapter`, `AdapterRegistry`
     (có `run_all()` để fan-out song song, khớp node `lookup` trong graph PAA
     ở §5.2).
   - `lookup/paa/*.py` — 7 adapter cụ thể (`comparable_sales`, `zoning`,
     `legal`, `amenities`, `environment`, `liquidity`, `reputation`), mỗi cái
     đọc `lookup_finding` theo đúng `lookup_category`; `comparable_sales` đọc
     thêm `market_comparable`.
   - `lookup/registry.py` — `get_lookup_registry()`, đăng ký sẵn cả 7.
   - `valuation/queries.py`, `risk/queries.py`, `dashboard/queries.py` — các
     hàm SQL đọc kết quả Định giá / Rủi ro / Dashboard (bao gồm bản thay thế
     portable cho 2 view `v_case_history` / `v_dashboard_kpi`).
5. **`tests/capabilities/test_paa_tools.py`** — smoke test cho adapter +
   resolver LTV + KPI dashboard, chạy trên SQLite in-memory (fixture `test_db`
   có sẵn ở `tests/conftest.py`).

## Cách chạy migration

```bash
export DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/shb
alembic upgrade head
```

## ⚠️ Lưu ý quan trọng — chưa chạy thử được trong sandbox

Phiên làm việc tạo ra các file này **không có quyền truy cập mạng để cài
`sqlalchemy`/`alembic`/`asyncpg`** (pip/apt đều bị chặn ở phiên hiện tại), nên
tôi **không chạy được** `alembic upgrade head` hay `pytest` thật để xác nhận
migration/tool chạy đúng trên Postgres/SQLite. Thay vào đó tôi đã:

- Kiểm tra cú pháp Python từng file bằng `ast.parse` (không lỗi cú pháp).
- Đối chiếu thủ công từng cột/constraint với `PAA_Schema_PostgreSQL.sql` —
  file DDL gốc đã được validate thật trên Postgres 16 trong phiên trước (tạo
  DB thật, insert mẫu, test constraint vi phạm bằng `DO $$ ... EXCEPTION $$`).

**Việc bạn nên làm trước khi merge:** chạy `alembic upgrade head` trên một DB
Postgres test, và `pytest tests/capabilities/ -v`. Nếu SQLAlchemy báo lỗi ở
bước tạo bảng/enum (khả năng cao nhất nằm ở đoạn xử lý enum dùng chung
`severity_level` trong `002_paa_schema.py`, hoặc cú pháp `sa.JSON()` trên
SQLite), báo lại — tôi sẽ sửa ngay.

## Bước tiếp theo (chưa làm trong lần này)

- `agents/paa/` (state + graph LangGraph nối `intake → lookup(fan-out) →
  valuation → risk → checklist → report`) — khung này gọi trực tiếp
  `capabilities/lookup/registry.get_lookup_registry().run_all(...)` và các
  hàm trong `capabilities/valuation`/`risk`/`dashboard` vừa thêm.
- `api/v1/endpoints/appraisals.py` — REST endpoints map theo §8 của
  `ARCHITECTURE.md`, gọi lại đúng các hàm tool này.
- Script nạp `paa_seed_data.sql` (đã tạo ở lần trước) vào DB dev để có dữ
  liệu demo trước khi nối agent thật.
