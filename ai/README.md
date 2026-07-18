# SHB AI — PAA (Property Appraisal Agent)

> Một trợ lý số cho thẩm định viên bất động sản thế chấp: đọc hộ giấy tờ, tra cứu hộ dữ
> liệu khu vực, tính hộ định giá và điểm rủi ro — nhưng **không bao giờ tự quyết thay
> con người**.

Mỗi hồ sơ thế chấp bất động sản đều bắt đầu bằng một chồng giấy tờ và kết thúc bằng một
con số duy nhất: hạn mức cho vay. Ở giữa hai đầu đó là một quy trình vốn rất thủ công —
đọc sổ đỏ, tra giá thị trường, đối chiếu quy hoạch, cân đo rủi ro — mà chất lượng phụ
thuộc nhiều vào kinh nghiệm cá nhân của từng thẩm định viên, và gần như không thể tra
soát lại "vì sao con số này ra như vậy" một khi hồ sơ đã đóng.

**PAA** thu hẹp đúng khoảng trống đó. Nó là sản phẩm đầu tiên chạy trên **SHB AI** — một
nền tảng dịch vụ AI dùng chung một hạ tầng xác thực, hàng đợi tác vụ và cổng LLM, nơi mỗi
nghiệp vụ mới chỉ cần "cắm" vào dưới dạng một plugin độc lập thay vì dựng lại từ đầu.
Frontend đi kèm nằm ở [`../apps/frontend`](../apps/frontend) (xem README riêng để chạy);
repo này là toàn bộ API và các plugin AI đứng sau nó.

---

## 1. Bài toán và cách PAA giải quyết

Khi khách hàng thế chấp bất động sản để vay vốn, thẩm định viên phải tự tay: đọc hồ sơ
giấy tờ tài sản, tra cứu dữ liệu khu vực (giá thị trường, quy hoạch, pháp lý, môi
trường...), định giá tài sản, chấm điểm rủi ro, đề xuất mức cho vay (LTV — Loan-to-Value),
rồi lập biên bản thẩm định. Đây là công việc tốn thời gian, lặp lại nhiều bước tra cứu
giống nhau giữa các hồ sơ, và khó chuẩn hoá giữa các thẩm định viên khác nhau.

PAA đóng vai một trợ lý làm sẵn phần tốn công nhất — thu thập, trích xuất, tra cứu, tính
toán — trong khi **thẩm định viên vẫn giữ toàn quyền quyết định**: rà soát từng bước, sửa
trực tiếp hoặc yêu cầu PAA sửa qua chat, rồi mới xác nhận và ký duyệt. Không một bước nào
trong pipeline được phép tự động hoá quyết định cho vay hay từ chối hồ sơ — đó là ranh
giới thiết kế cứng, không phải một tính năng tuỳ chọn.

### Bốn nguyên tắc không thể thoả hiệp

Vì kết quả PAA đưa ra ảnh hưởng trực tiếp tới một quyết định tài chính, mọi module trong
hệ thống — dù đã code hay còn nằm trên roadmap — đều phải tuân thủ:

1. **Có nguồn gốc (provenance).** Mỗi dữ kiện đi kèm `source`/`source_doc` và trạng thái
   xác thực rõ ràng (`da_xac_thuc` hay `chua_xac_thuc`). PAA không được phép "đoán" và
   trình bày như thể đó là sự thật đã kiểm chứng.
2. **Có độ tin cậy (confidence).** Mọi kết luận đi kèm một điểm tin cậy 0–100%. Dữ liệu
   tin cậy thấp — ví dụ tin đồn dư luận quanh một căn nhà — **chỉ mang tính cảnh báo tham
   khảo, tuyệt đối không được dùng làm căn cứ từ chối hồ sơ**.
3. **Có thể truy vết (auditable).** Mỗi bước xử lý ghi lại dấu vết thực thi — chạy lúc
   nào, mất bao lâu, ra kết quả gì — để tra soát lại bất cứ lúc nào sau này.
4. **Con người luôn ở vòng lặp (human-in-the-loop).** PAA chỉ tạo ra **nháp**. Mọi chỉnh
   sửa, dù qua form hay qua chat, đều dừng ở trạng thái "chờ xác nhận" cho tới khi thẩm
   định viên chủ động bấm xác nhận thì mới được tính là chốt.

### Hành trình một hồ sơ, qua 5 bước

Toàn bộ trải nghiệm bám sát mockup gốc (`PAA_Mockup_SHB_8.html`) và mô hình dữ liệu
(`PAA_Schema_PostgreSQL.sql`) — 5 bước tuần tự, mở khoá dần từng bước một khi bước trước
đã được xác nhận:

| Bước | Màn hình | Nghiệp vụ |
|---|---|---|
| 1 | **Nhập thông tin** | Thẩm định viên tải lên giấy tờ tài sản (sổ đỏ/sổ hồng, tờ khai lệ phí trước bạ, biên bản bàn giao, thông báo thuế đất...). PAA tự đọc và điền vào form: thông tin bên vay, pháp lý tài sản, đặc điểm tài sản, thông tin khoản vay. Trường nào tài liệu không nhắc tới thì để trống cho thẩm định viên tự nhập — **PAA không suy đoán** những trường này. |
| 2 | **Kết quả tra cứu** | Tra cứu song song **7 nguồn**: giá thị trường, quy hoạch, pháp lý, tiện ích xung quanh, rủi ro môi trường, thanh khoản khu vực, dư luận/tâm linh — mỗi nguồn gắn badge xác thực và độ tin cậy riêng. |
| 3 | **Định giá** | Kết hợp **3 phương pháp** — so sánh trực tiếp (trọng số 50%), hedonic/ML (30%), chi phí xây dựng (20%) — cho ra giá trị đề xuất kèm khoảng tin cậy. Độ tin cậy tổng là trung bình có trọng số của 5 yếu tố: số lượng/chất lượng giao dịch so sánh (30%), mức đồng thuận giữa 3 phương pháp (25%), độ đầy đủ dữ liệu pháp lý/quy hoạch (20%), biến động thị trường gần đây (15%), độ tương đồng giao dịch so sánh (10%). |
| 4 | **Rủi ro** | Chấm điểm rủi ro **của chính tài sản** (không phải rủi ro tín dụng người vay) từ **5 nhóm**: pháp lý (30%), thanh khoản (25%), biến động giá (20%), vật lý/môi trường (15%), danh tiếng/tâm linh (10%) → điểm 0–100, rồi tra theo khung chính sách để ra **LTV đề xuất**: 0–20 điểm → tối đa 75%, 21–40 → 65%, 41–60 → 55%, trên 60 điểm → tối đa 45% hoặc cần thẩm định lại. |
| 5 | **Dashboard** | Tổng hợp toàn bộ KPI, tóm tắt từng bước, trace thực thi, và xuất biên bản thẩm định sẵn sàng để ký. |

Xuyên suốt cả hành trình là một khung chat: thẩm định viên có thể hỏi PAA hoặc yêu cầu
sửa dữ liệu bất cứ lúc nào, và mọi thay đổi — dù đến từ form hay từ chat — đều phải đi
qua đúng một cửa: **chờ xác nhận → xác nhận** trước khi được coi là dữ liệu chính thức.

---

## 2. Đã xây được gì, còn thiếu gì — nói thẳng

Toàn bộ mô hình dữ liệu cho cả 5 bước đã sẵn sàng ở tầng lưu trữ: 23 bảng port 1:1 từ
`PAA_Schema_PostgreSQL.sql` sang ORM tại `src/shb/db/models_paa.py`. Nhưng một schema đẹp
không phải là một sản phẩm chạy được — hiện tại **2 trong 5 bước đã có API thật, chạy
được đầu-cuối**; 3 bước còn lại vẫn đang chờ ở dạng bảng dữ liệu và hàm truy vấn, chưa có
đường ra HTTP:

| Bước | Plugin / endpoint | Trạng thái |
|---|---|---|
| 1. Nhập thông tin | `property_intake` (bất đồng bộ, qua Celery) | ✅ **Chạy được** — trích xuất tài liệu tải lên bằng LLM, đã kiểm thử với dữ liệu thật |
| 2. Kết quả tra cứu | `property_lookup` (đồng bộ) | ✅ **Chạy được**, nhưng chỉ đọc DB — trả về 7 mục rỗng kèm cảnh báo nếu hồ sơ chưa được seed dữ liệu (xem mục 4.3) |
| 3. Định giá | — | ❌ Chưa có plugin/route. Bảng `valuation_result`/`valuation_method` và các hàm truy vấn ở `capabilities/valuation/` đã có sẵn, chỉ còn thiếu lớp kết nối |
| 4. Rủi ro | — | ❌ Tương tự — bảng `risk_assessment_result`/`risk_group` và `capabilities/risk/` đã sẵn sàng, chưa có plugin |
| 5. Dashboard, chat, xác nhận chỉnh sửa | — | ❌ Mới dừng ở mức phác thảo hợp đồng API (`docs/ARCHITECTURE.md` §8.3–8.4), chưa có một dòng code nào |

Nói cách khác: **nền móng đã được đặt vững cho toàn bộ sản phẩm, và hai viên gạch đầu
tiên — đúng hai bước tốn công sức nhất của thẩm định viên — đã dựng xong và chạy được
với dữ liệu thật.** Phần còn lại là lặp lại đúng khuôn mẫu đã chứng minh hiệu quả ở
`property_intake`/`property_lookup`, không phải thiết kế lại từ đầu.

Ở phía frontend, mọi phần chưa có API thật ở trên tự động rơi về dữ liệu mẫu tĩnh
(`apps/frontend/src/mocks/fixtureCase.ts`), nên toàn bộ trải nghiệm 5 bước vẫn xem/demo
được ngay hôm nay — chỉ có 2 bước đầu là dữ liệu thật, phần sau là minh hoạ. Xem README
của frontend để biết chính xác màn nào đã nối API, màn nào còn là demo.

### Vì sao có 2 tài liệu kiến trúc, và nên tin cái nào

- **`docs/ARCHITECTURE.md`** là bản thiết kế đầy đủ — một khung "Domain Agent" tổng quát
  dùng LangGraph (`agents/paa/` với state machine `intake → lookup (song song) →
  valuation → risk → checklist → report`), đủ tổng quát để sau này cắm thêm agent khác
  (Credit, Legal...) theo cùng một khuôn. Đây là **đích đến**, chưa phải hiện trạng.
- **Cách đã code thật** đi một con đường thực dụng hơn: mỗi bước là một plugin
  `BaseAIService` độc lập, interface đơn giản, gọi thẳng vào lớp `capabilities/` (các
  hàm SQL đọc/ghi) mà không cần dựng cả state machine LangGraph. Cách này bám sát
  `docs/contracts/property-intake-contract.md` và `docs/contracts/property-lookup-contract.md`
  — **hai file này mới là nguồn sự thật chính xác nhất** cho shape JSON hiện tại; nên đọc
  trước `ARCHITECTURE.md` khi cần biết chính xác API trả về gì.

---

## 3. Tech stack

| Lớp | Công nghệ | Ghi chú |
|---|---|---|
| API | **FastAPI** (async) + Uvicorn | Pydantic v2 cho schema/validate |
| ORM / DB | **SQLAlchemy 2.x** (async) + **PostgreSQL** | migration bằng **Alembic** |
| Hàng đợi tác vụ nền | **Celery 5.3+** + **Redis 7+** (broker + result backend) | phục vụ plugin `is_async=True` — điển hình là `property_intake`, vì gọi LLM mất nhiều giây |
| Orchestration LLM nhiều bước | **LangChain / LangGraph** | pipeline PAA đầy đủ ở `ARCHITECTURE.md` sẽ dùng; `property_intake` hiện đã dùng LangGraph nội bộ (`graph.py`) |
| LLM | Gateway **tương thích OpenAI** qua `LLM_BASE_URL` (trỏ tới OpenRouter hay gateway nội bộ đều được) | `LLM_API_KEY`, `LLM_MODEL`, `LLM_VISION_MODEL` cho OCR tài liệu scan |
| Auth | API key đơn giản qua header `X-API-Key` (hash SHA-256, lưu DB) | không có màn đăng nhập — tự đăng ký 1 lần qua `POST /auth/register` |
| Containerize | Docker + Docker Compose | app + Postgres + Redis + Celery worker, 1 lệnh khởi động toàn bộ |
| Quản lý dependency | `uv` | Python 3.12 |
| Chất lượng code | pre-commit: black, isort, flake8, mypy, bandit | |
| Test | pytest + pytest-asyncio | phần `capabilities`/plugin chạy offline trên SQLite in-memory, không cần hạ tầng thật |

---

## 4. Cài đặt

### 4.1 Docker Compose — cách nhanh nhất, đủ mọi thành phần

```bash
cd ai
cp .env.example .env
# Sửa .env: LLM_BASE_URL + LLM_API_KEY (gateway LLM tương thích OpenAI, vd OpenRouter),
# SECRET_KEY (tạo bằng: uv run python scripts/generate_secret_key.py)

docker compose up
# API:        http://localhost:8888
# PostgreSQL: localhost:5433
# Redis:      localhost:6379
```

Một lệnh `docker compose up` là đủ khởi động cả 4 service — `postgres`, `redis`, `app`
(uvicorn), và `celery_worker` — nên không có gì bị thiếu để chạy cả plugin bất đồng bộ.

### 4.2 Chạy native, không Docker (kể cả trên Windows)

Cần Postgres và Redis chạy sẵn — có thể tự cài, hoặc mượn tạm 2 service này từ Docker
(`docker compose up postgres redis`) rồi chạy app/worker native để tiện debug/hot-reload
Python trực tiếp.

```bash
cd ai
uv sync                      # cài dependency, cần Python 3.12+
cp .env.example .env
# Sửa .env: LLM_API_KEY, DATABASE_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND, SECRET_KEY

alembic upgrade head         # tạo schema, bao gồm cả 23 bảng PAA

# Terminal 1 — API server
uv run uvicorn shb.main:app --reload

# Terminal 2 — Celery worker (BẮT BUỘC để plugin bất đồng bộ như property_intake chạy được)
uv run celery -A shb.core.celery_app worker --loglevel=info
# Trên Windows, thêm --pool=solo: pool mặc định của Celery (prefork) cần fork(),
# mà Windows không có fork() — thiếu cờ này thì worker sẽ không khởi động được.

# Terminal 3 (tuỳ chọn) — theo dõi sự kiện Celery theo thời gian thực
uv run celery -A shb.core.celery_app events
```

> **Lỗi phổ biến nhất khi mới chạy lần đầu:** chỉ bật Terminal 1 mà quên Terminal 2. Job
> bất đồng bộ vẫn được tạo ra bình thường, nhưng **không có ai xử lý nó** — `GET
> /jobs/{id}` sẽ đứng yên ở trạng thái `pending` (`started_at: null`) cho tới khi hết
> giờ. Trước khi nghi ngờ có bug, luôn kiểm tra lại cả hai terminal đang chạy song song.

### 4.3 Nạp dữ liệu mẫu cho `property_lookup` (tuỳ chọn)

```bash
bash scripts/load_seed.sh
```

Cần Postgres (qua Docker) đang chạy. Script này đọc dữ liệu từ
`../apps/datasource/paa_seed_data.sql` — tại thời điểm viết README này, file đó **chưa
tồn tại trong repo**, nên chạy thẳng sẽ báo lỗi. Cần tạo file seed này trước (hoặc `INSERT`
tay vào `lookup_finding`/`market_comparable`) thì `property_lookup` mới trả về dữ liệu
thật thay vì 7 mục rỗng.

---

## 5. Kiến trúc & luồng dữ liệu

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

Điểm mấu chốt của kiến trúc này là **plugin nào cũng thay thế được mà không đụng tới
phần còn lại**: `AIServiceRegistry` tự quét thư mục plugin lúc khởi động, nên thêm một
nghiệp vụ mới chỉ là thêm một package tuân theo interface, chứ không phải sửa router hay
core.

**Luồng job bất đồng bộ** (`is_async=True`, ví dụ `property_intake`):

1. `POST /services/{id}/run` → tạo bản ghi `jobs` (`pending`), đẩy task vào Redis.
2. API trả ngay `{job_id, status: "pending"}` (202) — không chờ.
3. Celery worker rảnh sẽ nhặt task, chuyển `running`, chạy `plugin.run(...)`.
4. Hoàn tất → `completed` (kèm `result`) hoặc `failed` (kèm `error`) — job không bao giờ
   để worker crash theo, dù plugin bên trong lỗi.
5. Client `GET /jobs/{job_id}` để poll tới khi có trạng thái cuối cùng.

**Luồng đồng bộ** (`is_async=False`, ví dụ `property_lookup`): chạy thẳng trong request,
trả `{result: ...}` ngay lập tức — không tạo job, không cần poll, phù hợp cho những
nghiệp vụ chỉ đọc dữ liệu đã có sẵn.

---

## 6. API chính

Mọi endpoint dưới `/api/v1` (trừ `/health`) đều yêu cầu header `X-API-Key`.

### 6.1 Auth

```bash
# Đăng ký (1 lần) — nhận về api_key, sau đó KHÔNG hiển thị lại lần nào nữa
curl -X POST http://localhost:8888/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "ten@shb.local"}'

curl -H "X-API-Key: <key>" http://localhost:8888/api/v1/auth/me
```

### 6.2 Services (plugin)

```bash
curl -H "X-API-Key: <key>" http://localhost:8888/api/v1/services
curl -H "X-API-Key: <key>" http://localhost:8888/api/v1/services/{service_id}

# property_lookup — đồng bộ, trả kết quả ngay
curl -X POST -H "X-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"input": {"case_id": "REQ-2026-0001"}}' \
  http://localhost:8888/api/v1/services/property_lookup/run

# property_intake — bất đồng bộ: upload file trước, rồi poll /jobs
curl -X POST -H "X-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"input": {"file_ids": ["<file-id-từ-/files>"], "case_id": "REQ-2026-0001"}}' \
  http://localhost:8888/api/v1/services/property_intake/run
```

### 6.3 Jobs

```bash
curl -H "X-API-Key: <key>" http://localhost:8888/api/v1/jobs/{job_id}
curl -H "X-API-Key: <key>" "http://localhost:8888/api/v1/jobs?limit=10&offset=0"
curl -X DELETE -H "X-API-Key: <key>" http://localhost:8888/api/v1/jobs/{job_id}
```

### 6.4 Files

```bash
curl -X POST -H "X-API-Key: <key>" -F "file=@so-hong.pdf" http://localhost:8888/api/v1/files
```

Tài liệu Swagger/OpenAPI đầy đủ, tự sinh, luôn khớp code — có sẵn tại
`http://localhost:8888/docs`.

---

## 7. Hai plugin đang có

### `property_intake` — Trích xuất hồ sơ (Chức năng 1 / Màn 1)

Đây là plugin phức tạp nhất trong hệ thống hiện tại, và cũng là phần chứng minh rõ nhất
giá trị của PAA: đưa vào một tệp PDF/scan, nhận về một bộ dữ liệu có cấu trúc, có nguồn
gốc, sẵn sàng đổ thẳng vào form — thay vì thẩm định viên phải gõ tay từng trường.

- **Việc làm:** đọc file tải lên (sổ đỏ/sổ hồng, tờ khai LPTB, biên bản bàn giao, thông
  báo thuế đất...), dùng LLM trích xuất từng trường theo đúng shape form màn "Nhập thông
  tin", kèm `confidence`, trạng thái xác thực (`da_xac_thuc` / `can_xac_minh` /
  `mau_thuan` / `nhap_tay` / `suy_luan`), và trích dẫn nguồn (`source_doc`,
  `source_snippet`, cùng `bbox` — toạ độ vùng chứa dữ kiện trên trang).
- **Loại:** bất đồng bộ (`is_async=True`) — chạy qua Celery job.
- **Input:** `file_ids` (bắt buộc, upload qua `/files` trước), `language` (mặc định
  `vi`), `case_id` (tuỳ chọn).
- **Trung thực về giới hạn:** chưa phải loại tài liệu nào cũng trích xuất được — loại
  chưa hỗ trợ sẽ được báo rõ trong `warnings[]` thay vì âm thầm bỏ qua hay làm hỏng cả
  job, ví dụ: `"'…thue_dat.pdf' (loại thong_bao_thue_dat) chưa được hỗ trợ trích xuất
  (PR sau)."`
- Chi tiết đầy đủ: [`src/shb/ai/plugins/property_intake/README.md`](src/shb/ai/plugins/property_intake/README.md) ·
  [`docs/contracts/property-intake-contract.md`](docs/contracts/property-intake-contract.md)

### `property_lookup` — Kết quả tra cứu (Chức năng 2 / Màn 2)

Đơn giản hơn về mặt xử lý nhưng nghiêm ngặt về hợp đồng dữ liệu: đọc thẳng những gì đã có
trong DB và trình bày đúng shape màn "Kết quả tra cứu", không suy diễn thêm.

- **Việc làm:** đọc bảng `lookup_finding` và `market_comparable` theo `case_id`, trả về
  **luôn đủ 7 mục** — đúng 1 mục cho mỗi nguồn tra cứu (`market_price`,
  `planning_zoning`, `legal_status`, `neighborhood_amenity`, `environmental_risk`,
  `liquidity_stat`, `stigma_reputation`) — cùng bảng giao dịch so sánh. Plugin **chỉ đọc,
  không ghi**; dữ liệu phải được nạp trước qua seed demo hoặc một pipeline tra cứu ghi
  vào sau này.
- **Loại:** đồng bộ (`is_async=False`) — trả kết quả ngay trong request, không cần poll.
- **Input:** `case_id`.
- Một hồ sơ chưa có dữ liệu vẫn nhận đủ 7 mục — chỉ là rỗng, `status_badge:
  "chua_xac_thuc"`, kèm `warnings` giải thích rõ lý do. **Không bao giờ trả lỗi 500 hay
  thiếu mục** chỉ vì hồ sơ mới.
- Lưu ý nghiệp vụ quan trọng: `stigma_reputation` (dư luận/tâm linh) vốn có độ tin cậy
  thấp theo bản chất nguồn tin — **chỉ mang tính cảnh báo tham khảo, không được dùng để
  từ chối hồ sơ**.
- Chi tiết đầy đủ: [`src/shb/ai/plugins/property_lookup/README.md`](src/shb/ai/plugins/property_lookup/README.md) ·
  [`docs/contracts/property-lookup-contract.md`](docs/contracts/property-lookup-contract.md)

### Thêm một plugin mới

```
src/shb/ai/plugins/my_plugin/
├── __init__.py
├── schema.py     # MyPluginInput / MyPluginOutput (Pydantic)
└── service.py    # class MyPlugin(BaseAIService): meta = AIServiceMeta(id=..., is_async=...)
```

`AIServiceRegistry.discover_and_register()` tự quét toàn bộ `src/shb/ai/plugins/*` lúc
khởi động — chỉ cần tạo đúng 3 file trên, plugin mới sẽ tự xuất hiện ở `GET
/api/v1/services` mà không cần sửa một dòng nào ở core hay router.

---

## 8. Cấu hình (`.env`)

Xem đầy đủ ở `.env.example`. Các biến quan trọng nhất:

| Biến | Ý nghĩa |
|---|---|
| `DATABASE_URL` | Chuỗi kết nối Postgres, dạng `postgresql+asyncpg://user:pass@host/db` |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | URL Redis (mặc định `redis://localhost:6379/0` và `/1`) |
| `CELERY_WORKER_CONCURRENCY` | Số worker chạy song song (mặc định 4) |
| `LLM_BASE_URL` | Base URL gateway LLM tương thích OpenAI (OpenRouter hoặc gateway nội bộ) |
| `LLM_API_KEY` | API key của gateway trên — **bắt buộc** để `property_intake` chạy đúng; thiếu sẽ khiến job vẫn `completed` nhưng mọi field `null`, kèm cảnh báo `"LLM_API_KEY is required"` (không làm crash job) |
| `LLM_MODEL` | Model chat dùng để trích xuất text, ví dụ `cx/gpt-5.5` |
| `LLM_VISION_MODEL` | Model vision riêng cho OCR tài liệu scan (để trống thì dùng lại `LLM_MODEL`) |
| `PDF_SCAN_CHAR_THRESHOLD` / `PDF_SCAN_DOC_FRACTION` / `PDF_RENDER_DPI` | Ngưỡng phát hiện một trang PDF là bản scan (ít ký tự trích được) để chuyển sang xử lý bằng OCR/vision thay vì đọc text trực tiếp |
| `EMBEDDING_MODEL` / `EMBEDDING_DIM` | Model và số chiều embedding — dành cho bước RAG sinh biên bản ở roadmap sau |
| `SECRET_KEY` | Tạo bằng `uv run python scripts/generate_secret_key.py` |
| `STORAGE_DIR` | Thư mục lưu file upload (mặc định `storage/`) |
| `MAX_FILE_SIZE_MB` | Giới hạn dung lượng file upload (mặc định 100MB) |

---

## 9. Testing

```bash
uv run pytest                                              # toàn bộ
uv run pytest tests/plugins/test_property_intake.py -v
uv run pytest tests/plugins/test_property_lookup.py tests/capabilities/test_paa_tools.py -v
uv run pytest --cov=shb
uv run pre-commit run --all-files                           # black / isort / flake8 / mypy / bandit
```

Bộ test cho `capabilities/` và `property_lookup` chạy hoàn toàn **offline trên SQLite
in-memory** — không cần Postgres, Redis hay LLM key thật để xác nhận logic đúng, giúp
vòng lặp phát triển nhanh và không phụ thuộc hạ tầng ngoài.

---

## 10. Xử lý sự cố thường gặp

**Job `property_intake` kẹt mãi ở `pending`, `started_at: null`**
→ Chưa chạy Celery worker (mới chỉ có `uvicorn`). Mở thêm một terminal, chạy `uv run
celery -A shb.core.celery_app worker --loglevel=info` (thêm `--pool=solo` nếu đang ở
Windows).

**Job `completed` nhưng mọi trường đều `null`, `warnings` báo `LLM_API_KEY is required`**
→ `.env` đang thiếu `LLM_API_KEY`, hoặc worker đã khởi động **trước khi** bạn sửa `.env`
— worker không tự nạp lại `.env` như `uvicorn --reload` vẫn làm. Sửa xong `.env` thì phải
**khởi động lại Celery worker**, không chỉ restart API.

**`property_lookup` luôn trả về 7 mục rỗng**
→ Bình thường nếu `case_id` đó chưa có dữ liệu trong `lookup_finding`/`market_comparable`
— xem mục 4.3 để nạp dữ liệu mẫu.

**Celery worker không nhận task**
```bash
docker compose logs celery_worker
celery -A shb.core.celery_app inspect active
redis-cli ping   # phải trả về PONG
```

**Plugin không xuất hiện ở `GET /api/v1/services`**
→ Kiểm tra log lỗi import trong module plugin lúc khởi động app; xác nhận class kế thừa
đúng `BaseAIService` và `__init__.py` export đúng class đó.

---

## 11. Chặng đường tiếp theo

1. Tạo `apps/datasource/paa_seed_data.sql` để `property_lookup` có dữ liệu demo thật
   thay vì luôn trả về 7 mục rỗng.
2. Xây `property_valuation` (Chức năng 3) và `property_risk` (Chức năng 4) theo đúng
   khuôn hai plugin hiện có — phần khó nhất (hàm truy vấn SQL ở `capabilities/valuation/`
   và `capabilities/risk/`) đã sẵn sàng, chỉ còn thiếu lớp plugin và tài liệu hợp đồng.
3. Thiết kế và hiện thực API cho Màn 5 (dashboard, trace thực thi) cùng chat/xác nhận
   chỉnh sửa — hiện `docs/ARCHITECTURE.md` §8.3–8.4 mới dừng ở mức phác thảo hợp đồng,
   chưa có code.
4. Trước khi cân nhắc lên production: bỏ `Base.metadata.create_all` cùng việc seed user
   mặc định trong `init_db()` (chuyển hẳn sang Alembic để kiểm soát schema), siết lại
   CORS (hiện đang mở `["*"]`) — xem đầy đủ danh sách ở `docs/ARCHITECTURE.md` §11.

## 12. Đóng góp

1. Tạo branch feature từ nhánh đang phát triển.
2. Chạy `uv run pre-commit run --all-files` trước khi commit (black, isort, flake8, mypy, bandit).
3. Viết test cho phần mới — ưu tiên test chạy được offline như đã làm với `property_lookup`.
4. Tạo pull request, mô tả rõ nghiệp vụ thay đổi (không chỉ phần code).
