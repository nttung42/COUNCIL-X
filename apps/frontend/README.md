# PAA Frontend — Không gian làm việc của thẩm định viên (SHB)

Frontend React + TypeScript cho **PAA (Property Appraisal Agent)** — trợ lý số thẩm định
tài sản bảo đảm của SHB. Giao diện được dựng từ đúng mockup tĩnh
`../../ai/PAA_Mockup_SHB_8.html` và bám sát mô hình dữ liệu
`../../ai/PAA_Schema_PostgreSQL.sql`, để mọi màn hình nhìn và chạy giống hệt bản thiết kế
gốc chứ không phải một diễn giải lại. Backend mà ứng dụng này gọi vào nằm ở
[`../../ai`](../../ai) — xem README của repo đó để biết cách khởi động.

Điểm khác biệt của frontend này so với một bản dựng giao diện thuần tuý: nó được thiết kế
để **sống được ở cả hai trạng thái của backend cùng lúc** — chạy đầy đủ với dữ liệu mẫu
khi chưa có API nào, và tự động chuyển sang dữ liệu thật ngay khi từng endpoint lần lượt
hoàn thiện, không cần đụng vào một dòng code component nào để chuyển đổi.

## Tech stack

- **Vite + React 18 + TypeScript** — không dùng thêm framework nào khác; cũng không có
  router vì đây là một không gian làm việc một trang, điều hướng bằng tab chứ không có
  route nào cần rời khỏi.
- **Zustand** (`src/state/caseStore.ts`) — một store duy nhất giữ toàn bộ trạng thái: dữ
  liệu hồ sơ, luồng chat, cơ chế khoá/mở tab, và cơ chế theo dõi chỉnh sửa
  chờ-xác-nhận → đã-xác-nhận.
- CSS thuần (`src/theme/`), không dùng framework CSS — toàn bộ design token của mockup
  gốc được chuyển thể nguyên vẹn.
- Chưa cấu hình bộ chạy test tự động.

## Chạy nhanh

```bash
npm install
npm run dev      # http://localhost:5173
```

```bash
npm run build     # kiểm tra kiểu bằng tsc rồi build production -> dist/
npm run preview   # xem thử bản build production tại máy
npm run lint      # eslint
```

## Hai chế độ: demo (mặc định) và nối API thật

Ứng dụng chạy được **hoàn toàn không cần backend** ngay khi vừa cài xong — mọi dữ liệu
lấy từ fixture tĩnh ở `src/mocks/fixtureCase.ts`. Muốn trỏ sang backend `ai/` thật, chỉ
cần tạo file `.env` (đã được gitignore; sao chép từ `.env.example`):

```bash
# apps/frontend/.env
VITE_API_BASE_URL=http://127.0.0.1:8000   # hoặc http://localhost:8888 nếu chạy ai/ qua docker compose
```

`src/services/apiClient.ts` đọc biến này ngay lúc build (`isApiConfigured()`), và cờ
`apiMode` trong store sẽ tự điều chỉnh hành vi toàn bộ ứng dụng theo đó. **Không cần sửa
thêm bất kỳ dòng code nào khác để chuyển chế độ** — mọi component đều đọc dữ liệu qua
store, không component nào đọc thẳng từ fixture.

Không có xác thực: backend không yêu cầu API key hay đăng nhập, mọi request gọi thẳng
tới `VITE_API_BASE_URL`.

### Màn nào đã nối API thật, màn nào còn là dữ liệu mẫu

| Màn hình | Ở `apiMode`? | Ghi chú |
|---|---|---|
| 1. Nhập thông tin | ✅ Thật | Tải tài liệu lên → gọi `property_intake` (job bất đồng bộ, tự poll tới khi xong) → kết quả được **gộp** vào form theo `key` của từng trường. Trường nào trích xuất không trả về (hoặc trước khi trích xuất lần nào) vẫn hiện trống và gõ tay được bình thường — toàn bộ bộ trường của mockup luôn hiển thị đủ, trích xuất chỉ điền thêm được phần nào hay phần đó. Có nút "🎲 Điền dữ liệu mẫu" để điền nhanh dữ liệu giả, tiện kiểm tra giao diện mà không cần tài liệu thật. |
| 2. Kết quả tra cứu | ❌ Mẫu | Backend hiện đã có plugin `property_lookup` trả đúng shape cần thiết (`POST /services/property_lookup/run`, đồng bộ) — **chưa nối vào frontend**, đây là việc tiếp theo dễ làm nhất nếu DB đã có dữ liệu `lookup_finding`/`market_comparable`. |
| 3. Định giá | ❌ Mẫu | Backend chưa có endpoint cho bước này. |
| 4. Rủi ro | ❌ Mẫu | Backend chưa có endpoint cho bước này. |
| 5. Dashboard | ❌ Mẫu (nhưng vẫn phản ứng thời gian thực) | Số liệu tự cập nhật theo mọi chỉnh sửa ở các màn 2-4 (vì cùng đọc từ 1 store), nhưng bản thân dữ liệu gốc vẫn là mẫu, không phải từ backend. |
| Chat / luồng chờ-xác-nhận→xác-nhận | ❌ Kịch bản dựng sẵn | `src/mocks/chatScripts.ts` — các câu trả lời soạn sẵn cùng vài chỉnh sửa demo kích hoạt theo từ khoá (diện tích, môi trường, định giá, rủi ro). Backend `ai/` chưa có endpoint `/chat` nào. |

Khi tắt `apiMode`, màn 1 được điền sẵn đầy đủ từ `fixtureCase.ts` (đúng hồ sơ demo của
mockup gốc) nên toàn bộ giao diện xem/thao tác thử được ngay mà không cần bật backend.

## Cấu trúc thư mục

```
src/
  types.ts                   Kiểu dữ liệu miền nghiệp vụ (Tab1Field, LookupFinding, ValuationResult, RiskGroup...)
  state/caseStore.ts          Store Zustand duy nhất: dữ liệu hồ sơ, khoá/mở tab, chat, chỉnh sửa
  mocks/
    fixtureCase.ts            Dữ liệu hồ sơ demo (trường màn 1, kết quả tra cứu, định giá, rủi ro...)
    chatScripts.ts            Kịch bản trả lời chat + từ khoá kích hoạt chỉnh sửa demo
  services/
    apiClient.ts               Gọi backend thật: xác thực, tải file, property_intake + poll job
    apiTypes.ts                 Kiểu "trên dây" khớp nguyên văn schema Pydantic của ai/ (snake_case)
  utils/
    mapPropertyIntake.ts        Map response của property_intake -> Tab1Field[]/DocPage[]
    tab1Field.ts                 Suy ra nhãn/tooltip chip "nguồn" từ trạng thái 1 Tab1Field
    severity.ts, format.ts, exportReport.ts   Định dạng hiển thị + xuất báo cáo HTML độc lập
  components/
    Sidebar/                   Danh sách lịch sử hồ sơ
    ChatPane/                   Khung chat (30% bên trái)
    InfoPanel/                  Thanh subtab + footer + 5 màn Tab1..Tab5 (70% bên phải)
    common/                     Card, Badge, StatTile, Meter, BarRow, LookupDetailCard...
  theme/                       tokens.css (biến CSS) + global.css (toàn bộ style component)
```

### Vì sao `Tab1Field` là một mảng phẳng, không phải object lồng nhau

Mô hình dữ liệu của màn 1 (`Tab1Field[]` trong `types.ts`) cố tình mô phỏng đúng shape mà
`property_intake` trả về thật: một danh sách phẳng gồm `{ key, section, label, value,
confidence, status, source_doc, source_snippet, bbox }`, chứ không phải một object lồng
kiểu `{ borrower: {...}, legal: {...} }`. Lựa chọn này giúp cùng một đoạn code hiển thị
dùng được cho cả hai trường hợp — trường đến từ trích xuất thật hay do gõ tay đều render
giống nhau. `runExtraction()` trong store **gộp** kết quả API vào danh sách này theo
`key` thay vì thay thế toàn bộ, nên các giá trị gõ tay cho những trường backend không
trích xuất được (số điện thoại, thông tin khoản vay, "kích thước mặt tiền" — hoàn toàn
không có trong schema của `property_intake`) không bao giờ bị mất hay nhân đôi khi có
kết quả trích xuất mới đổ về.

### Luồng chỉnh sửa chờ-xác-nhận → đã-xác-nhận

Bất kỳ thay đổi nào — gõ trực tiếp vào một ô trên form, hay một chỉnh sửa demo kích hoạt
từ chat — đều đánh dấu trường đó là `pending` (viền xanh dương) qua `markPending(screen,
key)`. Bấm "Xác nhận & Tiếp theo" sẽ xác nhận toàn bộ chỉnh sửa đang chờ ở màn hiện tại
(`confirmScreen`), chuyển sang xanh lá, và mở khoá tab kế tiếp. Toàn bộ trạng thái này
nằm gọn trong store (`pendingEdits`/`confirmedKeys`), không quan tâm giá trị bên dưới đến
từ API hay do gõ tay — cùng một cơ chế cho cả hai nguồn.

## Những gì còn thiếu / việc tiếp theo

- Nối màn 2 vào endpoint `property_lookup` hiện đã sẵn sàng ở backend (xem bảng ở trên).
- Chưa có error boundary riêng cho từng thao tác bất đồng bộ ngoài `ErrorBoundary` tổng ở
  gốc cây component — khi upload/trích xuất lỗi, thông báo chỉ hiện qua tin nhắn trạng
  thái trong khung chat, dễ bị bỏ sót nếu người dùng đang không nhìn vào khung chat
  (riêng cảnh báo trích xuất đã có banner riêng dễ thấy hơn — xem khối "Nguồn tài liệu
  đính kèm").
- Chưa có test tự động.
