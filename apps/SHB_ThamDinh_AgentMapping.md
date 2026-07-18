# Từ quy trình thẩm định thực tế đến kiến trúc Multi-Agent: SHB Hack CX Together 2026

*Phân tích: "Digital Expert Agents – A Team of AI Specialists for Banking Operations", áp cho luồng thẩm định vay vốn doanh nghiệp (5 bước trong tài liệu SHB).*

---

## Phần 1 — Trong thực tế, nhân viên thẩm định làm gì?

Trước khi map sang agent, cần hiểu rõ **bản chất công việc thẩm định là gì**: không phải là "đọc hồ sơ rồi cho điểm", mà là một chuỗi **đối chiếu chéo (cross-verification)** giữa nhiều nguồn thông tin độc lập để phát hiện mâu thuẫn, rồi dùng kinh nghiệm/kiến thức ngành để đánh giá tính hợp lý. Dưới đây là chi tiết theo từng bước trong luồng bạn gửi.

### [1] Khởi tạo & tiếp nhận — RM / Chuyên viên QHKH

- Gặp trực tiếp khách hàng, phỏng vấn về mục đích vay, tình hình kinh doanh thực tế. Đây là bước **"mắt thấy tai nghe"** — RM quan sát trực tiếp cửa hàng/nhà xưởng, thái độ chủ doanh nghiệp, không giấy tờ nào thể hiện được điều này.
- Sàng lọc sơ bộ (pre-screening): ngành nghề có thuộc danh mục hạn chế cấp tín dụng không, quy mô có phù hợp khẩu vị rủi ro chi nhánh không, có dấu hiệu nợ xấu rõ ràng ngay từ đầu không.
- Hướng dẫn khách hàng chuẩn bị hồ sơ theo checklist 4 trụ cột (pháp lý, tài chính, phương án vay, tài sản đảm bảo) như ảnh thứ 2 bạn gửi.

### [2] Thu thập hồ sơ

- Đối chiếu **bản gốc và bản sao**: kiểm tra con dấu, chữ ký, tình trạng tẩy xóa, thời hạn hiệu lực của Đăng ký kinh doanh (ĐKKD).
- Đối chiếu chéo thông tin giữa các giấy tờ: tên công ty, mã số thuế, người đại diện pháp luật có khớp nhau xuyên suốt hồ sơ không.
- Kiểm tra đủ/thiếu theo checklist quy định nội bộ.

### [3] Thẩm định tín dụng — Phòng thẩm định (tuyến 2, độc lập với RM)

Đây là phần thẩm định chuyên sâu nhất, tách khỏi RM để tránh xung đột lợi ích (nguyên tắc "3 tuyến phòng vệ" — 3 lines of defense).

- **Thẩm định tư cách pháp lý**: tra cứu Cổng thông tin đăng ký doanh nghiệp quốc gia để xác minh DN còn hoạt động (không giải thể/tạm ngừng), ngành nghề đăng ký có phù hợp mục đích vay, người ký hợp đồng có đúng thẩm quyền đại diện pháp luật không.
- **Thẩm định tài chính**: phân tích 2–3 năm BCTC (đối chiếu BCTC nội bộ với BCTC/tờ khai nộp thuế — thực tế ở VN hai bộ này thường lệch nhau, đòi hỏi kinh nghiệm để nhận biết "làm đẹp" số liệu); tính các tỷ số thanh khoản, đòn bẩy, và đặc biệt **DSCR (Debt Service Coverage Ratio)** để xem dòng tiền có đủ trả gốc + lãi không; đối chiếu **sao kê tài khoản ngân hàng 6–12 tháng** để kiểm tra dòng tiền thực tế có khớp doanh thu khai báo không.
- **Thẩm định phương án vay**: đánh giá tính khả thi của phương án/dự án — đối chiếu hợp đồng đầu vào/đầu ra, hóa đơn, có phù hợp thực tế thị trường ngành đó không (đòi hỏi kiến thức ngành cụ thể).
- **Định giá tài sản đảm bảo**: thẩm định viên (hoặc đơn vị định giá độc lập) đi thực địa xem tài sản, đối chiếu pháp lý (sổ đỏ, đăng ký xe...), kiểm tra tài sản có đang tranh chấp/thế chấp ở nơi khác không qua hệ thống đăng ký giao dịch bảo đảm.
- **Chấm điểm xếp hạng tín dụng nội bộ**: mô hình scorecard kết hợp yếu tố định lượng (tài chính) và định tính (kinh nghiệm quản lý, vị thế ngành, lịch sử quan hệ tín dụng) → xếp hạng AAA–D, quyết định lãi suất và tỷ lệ tài sản đảm bảo yêu cầu.

### [4] Kiểm tra tuân thủ & rủi ro — Compliance/Risk (tuyến 2)

- **Tra CIC**: tra cứu hệ thống Trung tâm Thông tin Tín dụng Quốc gia (CIC, thuộc NHNN) để xem lịch sử nợ, nhóm nợ hiện tại tại các TCTD khác. Nhóm nợ 3–5 = nợ xấu, gần như loại ngay.
- **Sàng lọc AML/blacklist/sanction**: đối chiếu danh sách đen nội bộ, danh sách cấm vận quốc tế (OFAC/UN/EU), danh sách chính trị gia có ảnh hưởng (PEP) — cho cả doanh nghiệp và cá nhân liên quan (chủ sở hữu, người đại diện).
- **Giới hạn cấp tín dụng**: kiểm tra tổng dư nợ của khách hàng + nhóm khách hàng liên quan (công ty con, liên kết, người có liên quan) có vượt giới hạn theo Luật Các TCTD/Thông tư 22 không.
- **Đối chiếu quy định NHNN**: Thông tư 39/2016/TT-NHNN (vừa được sửa đổi bởi Thông tư 52/2025/TT-NHNN, ban hành 25/12/2025 — nên kiểm tra bản hợp nhất mới nhất khi triển khai thực tế), Thông tư 22/2019, Thông tư 41/2016 về tỷ lệ an toàn vốn.

### [5] Lập tờ trình & đề xuất — Chuyên viên thẩm định

- Tổng hợp toàn bộ phân tích ở bước 3–4 thành **tờ trình thẩm định**, nêu rõ rủi ro, điều kiện đề xuất (duyệt/từ chối/duyệt có điều kiện).
- *(Bước tiếp theo ngoài phạm vi ảnh nhưng luôn tồn tại trong thực tế)*: trình cấp có thẩm quyền hoặc Hội đồng tín dụng phê duyệt theo phân cấp thẩm quyền — đây là bước có trách nhiệm pháp lý, luôn phải là con người ký.

---

## Phần 2 — Mapping sang Agent: agent nào làm được gì

Nguyên tắc chung: agent (LLM + RAG + tool-calling) làm tốt việc **trích xuất — đối chiếu chéo — tính toán theo công thức — tra cứu dữ liệu có cấu trúc — soạn thảo văn bản từ dữ liệu đã phân tích**. Agent **không** thay thế được phán đoán dựa trên bối cảnh thị trường, xác minh vật lý, và trách nhiệm pháp lý ký duyệt.

| Bước | Việc cụ thể | Agent đề xuất | Agent làm được gì | Cần con người ở đâu |
|---|---|---|---|---|
| 1. Khởi tạo | Tiếp xúc, thu thập nhu cầu | *(Không có agent — trước khi có hồ sơ số hóa)* | Có thể có "Intake Agent" tóm tắt ghi chú cuộc gặp, tạo checklist hồ sơ cần nộp theo loại hình vay | Gặp gỡ, quan sát thực địa, đánh giá thái độ/uy tín khách hàng — **100% con người** |
| 2. Thu thập hồ sơ | Đối chiếu bản gốc/sao, đủ/thiếu | **Document/Intake Agent** | OCR + trích xuất trường dữ liệu (tên DN, MST, người đại diện...) từ ảnh scan; đối chiếu chéo tự động giữa các giấy tờ; báo thiếu hồ sơ theo checklist | Xác thực con dấu/chữ ký thật, phát hiện giấy tờ giả tinh vi vượt khả năng OCR |
| 3. Thẩm định pháp lý | Tra cứu ĐKKD, thẩm quyền ký | **Legal Agent** (RAG: Luật DN, Luật các TCTD + tool: API tra cứu ĐKKD quốc gia) | Tự động tra cứu tình trạng pháp lý DN, đối chiếu ngành nghề đăng ký với mục đích vay, kiểm tra thẩm quyền người ký | Diễn giải các trường hợp pháp lý phức tạp/mơ hồ (đồng sở hữu, ủy quyền chồng chéo) |
| 3. Thẩm định tài chính | Phân tích BCTC, tính DSCR, đối chiếu sao kê | **Financial/Credit Agent** (tool: parser BCTC, calculator tài chính) | Trích xuất số liệu từ BCTC/tờ khai thuế, tính toán hàng loạt tỷ số (thanh khoản, đòn bẩy, DSCR), đối chiếu dòng tiền sao kê vs doanh thu khai báo, phát hiện bất thường (dao động lớn, số liệu không khớp) | Đánh giá "câu chuyện" đằng sau con số (vì sao lệch, có hợp lý theo đặc thù ngành/mùa vụ không), quyết định có chấp nhận giải trình của KH không |
| 3. Thẩm định phương án vay | Đánh giá tính khả thi phương án | **Business Plan Agent** (RAG: dữ liệu ngành, benchmark thị trường) | Đối chiếu hợp đồng đầu vào/ra, hóa đơn có nhất quán với phương án không; so sánh với benchmark ngành có sẵn | Đánh giá triển vọng thị trường, rủi ro cạnh tranh, cảm quan kinh doanh — cần kinh nghiệm chuyên viên |
| 3. Định giá TSBĐ | Định giá, kiểm tra tranh chấp | **Collateral Agent** (tool: tra cứu đăng ký giao dịch bảo đảm, dữ liệu giá thị trường) | Tra cứu tài sản có đang thế chấp nơi khác không, đề xuất định giá sơ bộ theo dữ liệu thị trường/khung giá | Thẩm định thực địa (đi xem tài sản thật), định giá cuối cùng có chữ ký thẩm định viên |
| 3. Chấm điểm tín dụng | Xếp hạng nội bộ | **Scoring Agent** | Tự động hoá phần định lượng scorecard | Phần định tính (đánh giá năng lực quản lý, uy tín) vẫn cần input đánh giá của con người |
| 4. CIC | Tra lịch sử nợ | **Risk/CIC Agent** (tool: API CIC hoặc dữ liệu mô phỏng) | Tự động tra cứu, phân loại nhóm nợ, tổng hợp | Không nhiều — chủ yếu là xử lý ngoại lệ khi dữ liệu CIC không khớp |
| 4. AML/Sanction | Sàng lọc danh sách đen | **Compliance/AML Agent** (tool: fuzzy-match danh sách cấm vận/PEP) | Quét tự động toàn bộ tên liên quan, gắn cờ các match khả nghi | **Bắt buộc theo quy định PCRT**: mọi cảnh báo khớp tên (kể cả match yếu — false positive) phải được cán bộ tuân thủ xác minh thủ công trước khi loại trừ |
| 4. Giới hạn tín dụng | Kiểm tra nhóm KH liên quan | **Risk Agent** | Tính toán tổng dư nợ nhóm liên quan, so với giới hạn quy định | Xác định "người có liên quan" trong các trường hợp phức tạp (sở hữu chéo) cần thẩm tra thêm |
| 5. Lập tờ trình | Soạn thảo, tổng hợp | **Reporting/Orchestrator Agent** | Tổng hợp output của tất cả agent trên thành **bản dự thảo tờ trình** có cấu trúc, trích dẫn rõ nguồn dữ liệu | Chuyên viên thẩm định đọc, chỉnh sửa, chịu trách nhiệm nội dung trước khi trình ký |
| *(Ngoài luồng)* | Phê duyệt cuối | — | Có thể tạo "Decision-support dashboard" tóm tắt để người duyệt xem nhanh | **Phê duyệt/ký luôn là con người** — đây là yêu cầu bắt buộc theo Thông tư 39/2016 (đã sửa đổi bởi TT 52/2025) và phân cấp thẩm quyền nội bộ, không thể ủy quyền cho AI |

---

## Phần 3 — Vì sao một số bước bắt buộc phải có con người (không chỉ là "AI chưa đủ giỏi")

1. **Trách nhiệm pháp lý ký duyệt**: theo quy định về hoạt động cho vay, quyết định cấp tín dụng phải do người có thẩm quyền (được phân cấp) chịu trách nhiệm. Đây là ràng buộc pháp lý, không phải giới hạn kỹ thuật.
2. **Xác minh vật lý/thực địa**: xem nhà xưởng, tài sản đảm bảo, gặp trực tiếp khách hàng — AI hiện tại (kể cả agent có tool-use) không "hiện diện" được.
3. **Xử lý ngoại lệ AML**: quy định phòng chống rửa tiền yêu cầu cán bộ tuân thủ xác minh thủ công các cảnh báo trùng khớp tên, đặc biệt để giảm false positive — không được tự động loại trừ cảnh báo bằng máy.
4. **Phán đoán định tính**: đánh giá năng lực quản lý, uy tín, triển vọng ngành — đây là phán đoán dựa trên kinh nghiệm, ngữ cảnh thị trường thực tế, khó lượng hóa đầy đủ cho agent.
5. **Diễn giải mơ hồ**: các tình huống pháp lý/tài chính không rõ ràng (sở hữu chéo, giải trình chênh lệch số liệu) cần con người quyết định có chấp nhận hay yêu cầu bổ sung.

---

## Phần 4 — Gợi ý kiến trúc tổng thể (khớp với gợi ý kỹ thuật trong Problem Statement)

Theo đúng tinh thần "Planner agent decomposes work → specialist executor agents" mà đề bài đã gợi ý:

- **Planner/Orchestrator Agent**: nhận yêu cầu ("thẩm định hồ sơ vay khách hàng X"), phân rã thành task con, điều phối các agent chuyên biệt, tổng hợp kết quả.
- **Specialist agents** (ít nhất 2–3 để có demo thuyết phục, đề bài yêu cầu tối thiểu 2-3): Legal/Pháp lý, Financial/Tín dụng, Compliance/AML — đây có vẻ là 3 domain rõ nhất để làm demo (khớp gợi ý "Credit, Legal/Compliance, Operations agents" trong đề bài).
- **Tool layer**: document parser/OCR, financial calculator, mock API tra cứu ĐKKD/CIC/sanction list (vì thực tế không có quyền truy cập trực tiếp hệ thống CIC/NHNN, nên hackathon thường dùng dữ liệu giả lập).
- **RAG layer**: mỗi agent có knowledge base riêng (quy định nội bộ, văn bản pháp luật liên quan đến domain của nó).
- **Human-in-the-loop checkpoint**: rõ ràng đặt ở (a) sau khi Compliance Agent gắn cờ AML/sanction, (b) trước khi tờ trình được "chốt" để trình ký — dashboard hiển thị agent trace + decision log để con người dễ dàng review nhanh (đây cũng là "Key Deliverable" thứ 4 trong đề bài: dashboard cho thấy agent traces, task status, decisions).

---

## Câu hỏi để làm rõ trước khi đi tiếp

1. Team bạn muốn demo tập trung vào bao nhiêu agent chuyên biệt (2–3 theo đề bài) — ưu tiên Legal + Financial + Compliance, hay có domain khác bạn quan tâm hơn (vd. Collateral)?
2. Có dữ liệu mẫu nào sẵn có không (hồ sơ DN mẫu, BCTC mẫu, danh sách sanction mẫu), hay cần mình giúp tạo synthetic data để build & test?
3. Về hạ tầng: bạn đã chọn framework orchestration chưa (LangGraph/CrewAI/AutoGen như đề bài gợi ý), và muốn dùng LLM nào (Claude, GPT-4...)?
4. Thời gian còn lại cho hackathon là bao lâu, để mình ưu tiên đúng phần MVP demo được thay vì làm dàn trải?
