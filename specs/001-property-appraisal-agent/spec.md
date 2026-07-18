# Feature Specification: Property Appraisal Agent (PAA) — MVP Workspace

**Feature Branch**: `001-property-appraisal-agent`

**Created**: 2026-07-18

**Status**: Draft

**Input**: User description: "Xây MVP Property Appraisal Agent (PAA) cho SHB — chat hội thoại + info
panel 6 tab (Nhập thông tin, Kết quả tra cứu, Định giá, Rủi ro, Checklist, Dashboard), đúng theo
PROBLEM-STATEMENT-SHB2.pdf, PAA_KienTruc_HighLevel.md, PAA_Mockup_SHB.html,
SHB_ThamDinhBDS_DesignDoc_2.md. Cần dữ liệu mock chi tiết cho toàn bộ pipeline tra cứu/định giá/rủi ro."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Thẩm định viên nộp hồ sơ và nhận kết quả tự động (Priority: P1)

Một thẩm định viên (hoặc chuyên viên QHKH) nhập thông tin tài sản bảo đảm (địa chỉ, loại BĐS,
diện tích, tình trạng pháp lý khai báo, số tiền vay) qua form hoặc qua chat. Hệ thống tự động
tra cứu dữ liệu khu vực, tính định giá, chấm điểm rủi ro tài sản, và sinh checklist + nháp biên
bản thẩm định — tất cả hiển thị đồng bộ giữa khung chat và info panel, chuyển tab tự động theo
tiến độ xử lý.

**Why this priority**: Đây là toàn bộ giá trị cốt lõi của PAA — nếu thiếu, sản phẩm không giải
quyết được vấn đề "tối ưu công việc thẩm định viên" mà đề bài yêu cầu. Không có luồng này thì
không có MVP để demo.

**Independent Test**: Gửi 1 `property_appraisal_request` mẫu (địa chỉ có sẵn trong mock data) và
xác nhận nhận được đầy đủ `AppraisalReport` (định giá, điểm rủi ro, checklist, nháp báo cáo) trong
thời gian hợp lý, hiển thị đúng trên cả 5 tab liên quan (2–6) mà không cần tính năng nào khác.

**Acceptance Scenarios**:

1. **Given** thẩm định viên đã nhập đủ thông tin tài sản ở tab "Nhập thông tin" và bấm "Bắt đầu
   thẩm định", **When** hệ thống xử lý, **Then** khung chat hiển thị tuần tự các thông báo trạng
   thái ("đang tra cứu...", "đã có kết quả tra cứu...", "định giá đề xuất...", "điểm rủi ro...") và
   info panel tự động chuyển sang tab "Kết quả tra cứu" ngay khi bước tra cứu hoàn tất.
2. **Given** bước tra cứu đã hoàn tất với ít nhất 1 yếu tố cần lưu ý (vd. tin đồn khu vực chưa xác
   thực), **When** hệ thống tiếp tục sang bước định giá, **Then** tab "Định giá" hiển thị giá trị đề
   xuất kèm khoảng tin cậy, phần trăm độ tin cậy, và breakdown theo 3 phương pháp định giá.
3. **Given** định giá đã hoàn tất, **When** hệ thống chạy chấm điểm rủi ro, **Then** tab "Rủi ro"
   hiển thị điểm rủi ro tổng (0–100), tier (thấp/trung bình/cao), LTV đề xuất, và danh sách flag kèm
   mức độ nghiêm trọng + độ tin cậy.
4. **Given** toàn bộ pipeline đã chạy xong, **When** thẩm định viên mở tab "Checklist", **Then** hệ
   thống hiển thị checklist động theo loại tài sản và các flag phát hiện được, cùng 1 bản nháp biên
   bản thẩm định có đủ 3 mục thông tin/định giá/rủi ro.
5. **Given** người dùng đang ở màn hình di động (mobile), **When** họ bấm nút chuyển "Chat"/"Thông
   tin", **Then** đúng 1 khung tương ứng hiển thị toàn màn hình, khung còn lại ẩn đi.

---

### User Story 2 - Thẩm định viên hỏi đáp và chỉnh sửa qua Copilot (Priority: P2)

Sau khi có kết quả tự động, thẩm định viên đặt câu hỏi tình huống trực tiếp trong khung chat (ví
dụ: "tài sản đang thế chấp nơi khác thì xử lý sao?") và nhận câu trả lời có trích dẫn nguồn từ kho
tri thức quy trình/quy định nội bộ. Thẩm định viên cũng có thể tick/untick từng mục checklist.

**Why this priority**: Đây là phần "tối ưu công việc nhân viên thẩm định" — tăng giá trị nhưng hệ
thống vẫn dùng được (ở mức tối thiểu) nếu thiếu tính năng này, vì User Story 1 đã tạo ra kết quả.

**Independent Test**: Gửi 1 câu hỏi tự do trong chat của 1 case đã có kết quả, xác nhận nhận được
câu trả lời kèm trích dẫn nguồn tài liệu, không phá vỡ state của case đang xử lý.

**Acceptance Scenarios**:

1. **Given** một case đã có kết quả tra cứu/định giá/rủi ro, **When** thẩm định viên gõ câu hỏi tự
   do vào ô chat, **Then** hệ thống trả lời có trích dẫn nguồn từ kho tri thức, không làm thay đổi
   kết quả định giá/rủi ro đã có.
2. **Given** checklist đang hiển thị với một số mục đã tick sẵn, **When** thẩm định viên click vào 1
   mục chưa tick, **Then** mục đó chuyển trạng thái đã hoàn thành và được lưu lại cho case đó.

---

### User Story 3 - Quản lý và theo dõi nhiều hồ sơ qua sidebar & dashboard (Priority: P3)

Thẩm định viên xem danh sách "Lịch sử hồ sơ" ở sidebar (đang xử lý / hoàn tất / huỷ), chọn lại 1
hồ sơ cũ để xem lại kết quả, hoặc tạo yêu cầu thẩm định mới. Ở tab "Dashboard", họ xem được trace
thực thi chi tiết (agent nào chạy lúc nào, kết quả gì) của case đang mở.

**Why this priority**: Cải thiện khả năng vận hành nhiều hồ sơ song song và tính minh bạch/audit,
nhưng không chặn việc demo giá trị cốt lõi của 1 hồ sơ đơn lẻ (User Story 1).

**Independent Test**: Tạo 2 case riêng biệt, xác nhận chuyển qua lại giữa chúng ở sidebar không làm
lẫn dữ liệu, và tab Dashboard của mỗi case hiển thị đúng trace riêng của case đó.

**Acceptance Scenarios**:

1. **Given** đã có ≥2 hồ sơ trong lịch sử, **When** thẩm định viên click 1 hồ sơ khác trong sidebar,
   **Then** toàn bộ chat + info panel chuyển sang đúng state của hồ sơ được chọn.
2. **Given** một case đã chạy xong toàn bộ pipeline, **When** thẩm định viên mở tab "Dashboard",
   **Then** timeline hiển thị đúng thứ tự các bước (tiếp nhận → tra cứu song song → định giá → rủi
   ro → soạn nháp) kèm mốc thời gian tương đối của từng bước.

### Edge Cases

- Địa chỉ tài sản không có trong mock data (không tìm thấy giao dịch so sánh nào trong bán kính
  yêu cầu) → hệ thống phải trả kết quả với `confidence_score` thấp và flag "không đủ dữ liệu so
  sánh, cần thẩm định viên bổ sung", không được từ chối hay báo lỗi cứng.
- Một hoặc nhiều lookup tool (trong 7 tool song song) trả lỗi/timeout → các tool còn lại vẫn phải
  trả kết quả bình thường; phần bị thiếu hiển thị rõ "chưa tra cứu được" thay vì chặn toàn bộ pipeline.
- Toàn bộ dữ liệu "tin đồn/tâm linh" phải luôn hiển thị nhãn độ tin cậy thấp + "chưa xác thực" —
  không được để giao diện hiển thị lẫn với dữ liệu đã xác thực (vi phạm Nguyên tắc III của
  constitution).
- Thẩm định viên gửi yêu cầu thẩm định mới trong khi 1 case khác đang xử lý → 2 case phải chạy độc
  lập, không ghi đè state của nhau.
- Giá trị vay yêu cầu (`requested_amount`) vượt xa giá trị định giá đề xuất → hệ thống vẫn phải trả
  kết quả bình thường kèm cảnh báo rõ ràng trong flags/checklist, không tự chặn hồ sơ.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống MUST cho phép người dùng nhập thông tin tài sản cần thẩm định (địa chỉ, toạ
  độ, loại BĐS, diện tích, tình trạng pháp lý khai báo, số tiền vay, mục đích vay) qua tab "Nhập
  thông tin" hoặc qua khung chat.
- **FR-002**: Hệ thống MUST tra cứu song song 7 nhóm dữ liệu khu vực/tài sản: giá thị trường so
  sánh, quy hoạch/lộ giới, tình trạng pháp lý, tiện ích lân cận, dư luận/tâm linh, rủi ro môi
  trường, thống kê thanh khoản khu vực.
- **FR-003**: Mọi kết quả tra cứu MUST kèm theo mức độ tin cậy (0–1) và phân loại nguồn
  (`mock` / `verified` / `unverified_rumor`).
- **FR-004**: Hệ thống MUST tính giá trị định giá đề xuất bằng 3 phương pháp (so sánh trực tiếp,
  mô hình hedonic, chi phí xây dựng) và kết hợp thành 1 giá trị blend kèm khoảng tin cậy
  (value_range) và điểm tin cậy tổng (confidence_score).
- **FR-005**: Hệ thống MUST quy đổi giá giao dịch quá khứ về thời điểm hiện tại bằng chỉ số giá khu
  vực theo quý, và ghi rõ kỳ chỉ số giá đã dùng.
- **FR-006**: Hệ thống MUST tính điểm rủi ro tài sản (0–100) từ 5 nhóm rủi ro có trọng số (pháp lý
  30%, thanh khoản 25%, biến động giá 20%, vật lý/môi trường 15%, danh tiếng/tâm linh 10%), kèm
  tier (thấp/trung bình/cao) và LTV đề xuất.
- **FR-007**: Hệ thống MUST tách biệt hoàn toàn nhóm dữ liệu "tin đồn/tâm linh chưa xác thực" khỏi
  nhóm dữ liệu pháp lý/môi trường đã xác thực trong mọi hiển thị và trong cách tính điểm rủi ro,
  và MUST NOT dùng nhóm chưa xác thực làm căn cứ duy nhất để từ chối/khoá hồ sơ.
- **FR-008**: Hệ thống MUST sinh checklist động theo loại tài sản và theo các flag rủi ro đã phát
  hiện, cho phép người dùng tick/untick từng mục và lưu lại trạng thái.
- **FR-009**: Hệ thống MUST sinh bản nháp biên bản thẩm định gồm tối thiểu: thông tin tài sản, kết
  quả định giá, điểm rủi ro & LTV đề xuất, và khu vực chữ ký/xác nhận còn trống chờ con người.
- **FR-010**: Hệ thống MUST cho phép người dùng đặt câu hỏi tự do trong chat và nhận câu trả lời có
  trích dẫn nguồn từ kho tri thức quy trình/quy định nội bộ, mà không làm thay đổi kết quả định
  giá/rủi ro của case đang mở.
- **FR-011**: Hệ thống MUST hiển thị đồng bộ theo thời gian thực giữa khung chat và info panel: mỗi
  khi 1 bước xử lý hoàn tất, info panel MUST tự động chuyển sang tab tương ứng, đồng thời người
  dùng MUST vẫn có thể tự bấm chuyển tab bất kỳ lúc nào.
- **FR-012**: Hệ thống MUST lưu trạng thái đầy đủ của từng hồ sơ thẩm định (case/session) — đủ để
  người dùng quay lại xem đúng kết quả cũ từ sidebar "Lịch sử hồ sơ" mà không mất dữ liệu.
- **FR-013**: Hệ thống MUST ghi lại trace thực thi (thời điểm, thành phần xử lý, tóm tắt input/
  output) của mỗi bước trong pipeline và hiển thị dạng timeline trên tab "Dashboard".
- **FR-014**: Hệ thống MUST luôn đính kèm cờ `requires_human_verification` (hoặc tương đương) trong
  kết quả trả về khi có bất kỳ yếu tố chưa xác thực/độ tin cậy thấp nào, và MUST hiển thị rõ ràng
  disclaimer "dữ liệu mô phỏng, không phải số liệu ngân hàng thật" trong giao diện.
- **FR-015**: Hệ thống MUST cho phép một agent/dữ liệu tra cứu bị lỗi hoặc thiếu mà không chặn toàn
  bộ pipeline — phần thiếu MUST hiển thị rõ trạng thái "chưa tra cứu được" thay vì làm sập luồng xử
  lý hoặc trả kết quả sai lệch.
- **FR-016**: Hệ thống MUST hỗ trợ nhiều hồ sơ thẩm định độc lập cùng lúc mà không để trạng thái
  của case này ảnh hưởng đến case khác.

### Key Entities

- **PropertyAppraisalRequest**: yêu cầu thẩm định đầu vào — địa chỉ, toạ độ, loại BĐS, diện tích,
  tình trạng pháp lý khai báo, số tiền vay, mục đích vay, mã yêu cầu.
- **ComparableTransaction**: 1 giao dịch/tin rao bán so sánh — địa chỉ, khoảng cách, diện tích,
  ngày giao dịch, giá/m², tình trạng pháp lý, đặc điểm công trình.
- **PriceIndexSeries**: chuỗi chỉ số giá khu vực theo quý, dùng để quy đổi giá giao dịch quá khứ
  về thời điểm hiện tại.
- **AddressProfile**: hồ sơ "tốt/xấu/tâm linh" gắn theo địa chỉ — yếu tố tích cực, tiêu cực, và tin
  đồn/tâm linh, mỗi yếu tố kèm độ tin cậy và trạng thái xác thực.
- **ValuationResult**: kết quả định giá — giá trị đề xuất, khoảng tin cậy, giá/m², điểm tin cậy,
  breakdown theo 3 phương pháp, số giao dịch so sánh đã dùng, ghi chú điều chỉnh.
- **AssetRiskAssessment**: kết quả chấm điểm rủi ro — điểm tổng, tier, LTV đề xuất, danh sách flag
  (loại, mức độ nghiêm trọng, mô tả, độ tin cậy, hành động đề xuất), điều kiện cấp tín dụng đề xuất.
- **ChecklistItem**: 1 mục checklist động — mô tả, trạng thái hoàn thành, loại tài sản áp dụng, flag
  rủi ro liên quan (nếu có).
- **AppraisalReportDraft**: bản nháp biên bản thẩm định — các mục nội dung theo cấu trúc chuẩn, khu
  vực chữ ký còn trống.
- **CaseSession**: 1 phiên hồ sơ thẩm định — request gốc, kết quả từng bước, trạng thái (đang xử lý/
  hoàn tất/huỷ), lịch sử chat.
- **TraceEvent**: 1 sự kiện trong pipeline xử lý — thời điểm, thành phần thực hiện, tóm tắt input/
  output, dùng cho tab Dashboard.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Từ lúc thẩm định viên bấm "Bắt đầu thẩm định" đến khi cả 4 tab kết quả (Tra cứu,
  Định giá, Rủi ro, Checklist) có dữ liệu đầy đủ mất dưới 15 giây với dữ liệu mock.
- **SC-002**: 100% kết quả tra cứu/định giá/rủi ro hiển thị cho người dùng đều có kèm độ tin cậy
  hoặc khoảng giá trị — không có con số tuyệt đối "trần trụi" nào xuất hiện trên giao diện.
- **SC-003**: 100% yếu tố thuộc nhóm tin đồn/tâm linh hiển thị đúng nhãn "chưa xác thực" và không
  xuất hiện lẫn trong danh sách yếu tố pháp lý/môi trường đã xác thực.
- **SC-004**: Thẩm định viên có thể xem lại đầy đủ, chính xác kết quả của 1 hồ sơ cũ bất kỳ trong
  "Lịch sử hồ sơ" mà không có sai lệch dữ liệu so với lúc hồ sơ đó được xử lý lần đầu.
- **SC-005**: Với 1 địa chỉ không có trong mock data, hệ thống vẫn trả về kết quả có cấu trúc đầy đủ
  (không lỗi cứng/crash), kèm cảnh báo rõ ràng thiếu dữ liệu so sánh.
- **SC-006**: Người đánh giá demo (giám khảo) có thể tự trả lời được câu hỏi "vì sao hệ thống đề
  xuất định giá và điểm rủi ro này" chỉ bằng cách đọc thông tin hiển thị trên giao diện, không cần
  hỏi thêm đội phát triển.

## Assumptions

- Phạm vi MVP chỉ xử lý 1 loại yêu cầu tại 1 thời điểm cho 1 tài sản (nhà phố / nhà trong hẻm / đất
  nền), ưu tiên nhà ở đô thị — chưa xử lý BĐS thương mại/công nghiệp.
- Toàn bộ dữ liệu tra cứu (giao dịch, chỉ số giá, hồ sơ pháp lý/môi trường/dư luận, kho tri thức
  quy trình) là dữ liệu mock/synthetic được thiết kế sẵn cho 1–2 khu vực mẫu, không kết nối nguồn
  dữ liệu thật (Sở TN&MT, CIC, trang rao bán BĐS...) trong phạm vi MVP này.
- "Planner Agent" hệ thống và các digital expert agent khác (Credit, Legal/Compliance, Operations)
  nằm ngoài phạm vi — được giả lập bằng 1 mock caller đơn giản gửi `PropertyAppraisalRequest` mẫu
  và nhận `AppraisalReport`.
- Người dùng chính là thẩm định viên/chuyên viên QHKH nội bộ SHB, dùng trên desktop là chính, có hỗ
  trợ responsive cơ bản cho mobile (chuyển đổi chat/info panel).
- Xác thực người dùng (đăng nhập/phân quyền) không thuộc phạm vi MVP — giả định 1 người dùng single-
  session cho mỗi lần demo.
- Quyết định cấp tín dụng cuối cùng, xác minh thực địa, và ký duyệt biên bản luôn là hành động thủ
  công của con người, nằm ngoài phạm vi hệ thống tự động hoá.
