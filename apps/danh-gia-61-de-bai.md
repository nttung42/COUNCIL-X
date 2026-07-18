# Đánh giá 61 đề bài — AI for Vietnam Hackathon

**Nguồn dữ liệu:** `hub-api.aiforvietnam.org/problem-statements` (ID 131–191), lấy ngày 2026-07-17.
**Phương pháp:** đọc `detailed_description` + tiêu chí chấm điểm (nếu có) của từng đề, xếp hạng theo mức độ khả thi trong thời gian hackathon và độ khớp với năng lực đội.
**Đội:** 2 kỹ sư AI, 2 kỹ sư phần mềm (SE), 1 phụ trách marketing/tài chính — thế mạnh trải đều ở RAG/Agent, Computer Vision/Edge AI, và Data/Forecasting/Voice.

**Chú thích tier:**
- **S** — ưu tiên số 1: dữ liệu/API sẵn có, tiêu chí chấm rõ ràng, khớp năng lực đội, ít rủi ro thực thi.
- **A** — khả thi cao: có thể hoàn thiện tốt trong thời gian hackathon, rủi ro chấp nhận được.
- **B** — cần thu hẹp scope: ý tưởng tốt nhưng phải cắt bớt phạm vi hoặc thiếu dữ liệu, cần xử lý khéo.
- **C** — nên tránh: thiếu dữ liệu nghiêm trọng, scope quá lớn (cấp thành phố/tập đoàn), hoặc bản chất không phải bài toán phần mềm.

**Tổng kết nhanh:** Tier S = 7 đề · Tier A = 20 đề · Tier B = 13 đề · Tier C = 21 đề.

---

## Phát hiện chính

1. **3 sponsor chiếm hơn nửa số đề.** Duy Tân University (13 đề), Cần Thơ People's Committee (12 đề), Vbee AITalk (10 đề) — tổng cộng 35/61 đề đến từ 3 nguồn.
2. **Bẫy "đề quy hoạch cấp thành phố".** 12 đề của Cần Thơ People's Committee + 3 đề của Vietnam Rubber Group (VRG) + 1 đề của Tổng Công ty Đường sắt Việt Nam (VNR) — tổng **15 đề** — được viết ở tầm chiến lược/quy hoạch cho cả thành phố hoặc tập đoàn, không kèm dữ liệu, không có API, không có tiêu chí chấm cụ thể. Rất khó ra được demo phần mềm chạy thật trong vài ngày.
3. **Đề "dễ chấm điểm" nhất** là nhóm có mục *Minimum Submission Requirements* + *Judging criteria* định lượng rõ ràng: #131, #153, #154, #157, #160, và cụm #182–191 (Vbee) — giám khảo có checklist cụ thể để so sánh giữa các đội.
4. **Bẫy cạnh tranh ở cụm Vbee.** 10 đề của Vbee (182–191) có brief chuẩn nhất, API thật, SLA rõ ràng — nên rất nhiều đội sẽ đổ vào đây. Nếu chọn nhóm này, nên chọn đề lệch khỏi khuôn mẫu "voice agent hội thoại" (ví dụ #185, #186, #187) để tránh bị so sánh trực diện với hàng loạt đội khác.

---

## 5 lựa chọn ưu tiên hàng đầu

### 1. #131 — Advanced RAG Knowledge Base (SHB Bank) — *Tier S*
**Track:** Tài chính-Ngân hàng · **Cạnh tranh:** Thấp

Bài toán RAG nâng cao rõ ràng nhất trong 61 đề — có tài liệu mẫu đính kèm, sponsor uy tín, đúng 100% sở trường LLM/RAG của 2 kỹ sư AI.

- **Kiến trúc đề xuất:** Hybrid retrieval (dense + BM25) trên document graph theo dõi quan hệ tu chính/thay thế văn bản; LLM tổng hợp câu trả lời kèm trích dẫn và cờ cảnh báo xung đột quy định.
- **Rủi ro:** tài liệu ngân hàng thật có thể ít/khó lấy ngoài file đính kèm — cần hỏi BTC bổ sung corpus sớm.
- **Phân công:** AI xây pipeline retrieval + document graph, đánh giá độ chính xác trích dẫn · SE dựng vector DB, API backend, giao diện chat demo · Marketing chuẩn hoá corpus chính sách mẫu, viết kịch bản demo cho giám khảo ngân hàng.

### 2. #157 — AI Product Comparison Advisor (Điện Máy Xanh) — *Tier S*
**Track:** Năng suất DN · **Cạnh tranh:** Thấp

Brief chuẩn nhất trong toàn bộ 61 đề: rubric theo % công khai, SLA độ trễ cụ thể, có dữ liệu catalog, pilot 3 tháng có điều kiện thật — rất hợp để thành viên marketing/tài chính dựng roadmap và ROI.

- **Kiến trúc đề xuất:** RAG có anti-hallucination guardrail bắt buộc trích nguồn catalog/API, chatbot chủ động hỏi lại khi thiếu thông tin, so sánh top-3 sản phẩm theo lợi ích thay vì bảng thông số.
- **Rủi ro:** SLA phản hồi 3–5 giây bắt buộc kiểm thử tải kỹ trước khi trình diễn.
- **Phân công:** AI làm RAG + guardrail chống bịa thông tin, logic so sánh top-3 · SE tích hợp catalog/API, đảm bảo SLA, load test · Marketing dựng pilot roadmap 3 tháng, mô hình ROI, kịch bản pitch bám đúng rubric %.

### 3. #153 — Weather analysis & forecasting (Sở KH&CN Điện Biên) — *Tier S*
**Track:** Phòng chống thiên tai · **Cạnh tranh:** Thấp

Hiếm đề có nguồn dữ liệu mở thật rõ ràng (Open-Meteo, OpenWeatherMap, dữ liệu thiên tai lịch sử); yêu cầu tối thiểu rất cụ thể; track chỉ có 2 đề nên ít cạnh tranh trực tiếp.

- **Kiến trúc đề xuất:** Downscale dự báo cấp xã từ dữ liệu vùng bằng mô hình thống kê nhẹ, sinh bản tin cảnh báo bằng luật + LLM diễn giải, phát qua kênh đa ngôn ngữ (Thái, Mông) dùng TTS.
- **Rủi ro:** bản dịch sang tiếng Thái/Hmong khó kiểm định chất lượng — có thể giới hạn bản demo ở tiếng Việt + 1 ngôn ngữ dân tộc.
- **Phân công:** AI làm mô hình downscale dự báo + sinh bản tin cảnh báo · SE tích hợp API thời tiết, kênh phân phối Zalo/SMS/loa · Marketing xây câu chuyện tác động xã hội cho vùng dân tộc thiểu số, thiết kế giao diện cảnh báo dễ hiểu.

### 4. #181 — Speech-to-meaning platform (VALSEA) — *Tier S*
**Track:** Đổi mới mở · **Cạnh tranh:** Thấp

Có sandbox API key ASR thật, yêu cầu mở ("chứng minh 1 vertical/workflow cụ thể") cho phép đội tự chọn hướng khớp năng lực nhất; là đề Voice riêng lẻ (không như cụm 10 đề Vbee) nên ít cạnh tranh hơn.

- **Kiến trúc đề xuất:** Gọi VALSEA ASR endpoint bắt buộc, chuyển transcript thành output có cấu trúc (ticket/ghi chú) cho 1 vertical cụ thể, chứng minh giá trị bằng so sánh quy trình thủ công trước/sau.
- **Rủi ro:** chọn sai vertical sẽ khiến demo thiếu thuyết phục — nên chọn 1 ngành đội có hiểu biết thật (y tế, logistics, hoặc CSKH).
- **Phân công:** AI xử lý output ASR thành dữ liệu có cấu trúc cho workflow đã chọn · SE tích hợp sandbox API VALSEA, dựng demo trước/sau · Marketing chọn và xác thực vertical mục tiêu, định lượng giá trị tiết kiệm thời gian/chi phí.

### 5. #185 — QA & analytics 100% hotline calls (Vbee AITalk) — *Tier S*
**Track:** Năng suất DN · **Cạnh tranh:** TB

Trong cụm 10 đề Vbee, đây là đề duy nhất dạng batch analytics thay vì voice-agent hội thoại real-time — giảm rủi ro kỹ thuật (không cần độ trễ dưới 2 giây), giá trị doanh nghiệp rõ, ít bị trộn lẫn với các đội chọn voice-agent.

- **Kiến trúc đề xuất:** Batch STT xử lý hàng loạt file ghi âm, chấm điểm mỗi cuộc gọi theo checklist QA cấu hình được, gắn nhãn rủi ro khiếu nại/rời bỏ, dashboard theo agent/team, cảnh báo tức thời qua n8n.
- **Rủi ro:** cần chuẩn bị ≥20 bản ghi âm giả lập đa dạng tình huống để chứng minh checklist hoạt động đúng.
- **Phân công:** AI làm mô hình chấm điểm cuộc gọi theo checklist, phát hiện rủi ro khiếu nại · SE dựng pipeline batch song song, dashboard, cảnh báo qua n8n · Marketing ước tính chi phí xử lý mỗi phút âm thanh, câu chuyện tiết kiệm chi phí QA.

---

## Bẫy cần tránh — 15 đề "quy hoạch cấp thành phố/tập đoàn"

Không kèm dữ liệu, không có API, không có tiêu chí chấm cụ thể — bản chất là đề bài quy hoạch/chiến lược, không phải bài toán AI có thể demo trong vài ngày:

| ID | Sponsor | Đề bài |
|---|---|---|
| #163 | VNR | Dynamic pricing tách/ghép chặng tàu — tích hợp hệ thống vé thật cấp doanh nghiệp |
| #164 | VRG | Generative AI quy hoạch đất KCN — cần dữ liệu GIS/DEM thật |
| #165 | VRG | Energy digital twin cho KCN — cần dữ liệu SCADA thật |
| #166 | VRG | AI điều khiển tối ưu xử lý nước thải — bài toán nghiên cứu điều khiển |
| #167 | Cần Thơ | Smart urban traffic command |
| #168 | Cần Thơ | Nhận diện nguồn phát thải real-time |
| #169 | Cần Thơ | Dự báo ngập lụt & sponge-city (cần cả hạ tầng vật lý) |
| #170 | Cần Thơ | Tái thiết đô thị xanh giữ hồn khu phố |
| #171 | Cần Thơ | Số hoá đất đai & minh bạch BĐS |
| #172 | Cần Thơ | Logistics đa phương thức liên vùng |
| #173 | Cần Thơ | Nông nghiệp công nghệ cao thích ứng khí hậu |
| #174 | Cần Thơ | Công nghiệp hoá công nghệ cao |
| #175 | Cần Thơ | Hệ sinh thái UAV/Drone dùng chung (cần phần cứng thật) |
| #176 | Cần Thơ | Private 5G/IoT & testbed 6G (hạ tầng viễn thông vật lý) |
| #178 | Cần Thơ | AI tiếng Việt cho hành chính công — nên chọn #160 (NIDit) thay thế, cùng dạng bài nhưng scope rõ hơn |

*(#177 — An sinh xã hội Big Data — cũng thuộc nhóm Cần Thơ nhưng "phần mềm hoá" được dễ hơn nếu buộc phải chọn trong nhóm này; xem bảng đầy đủ bên dưới.)*

---

## Bảng đầy đủ 61 đề

### Tier S — Ưu tiên số 1

| ID | Đề bài | Sponsor | Track | Khớp năng lực | Ghi chú |
|---|---|---|---|---|---|
| 131 | Advanced RAG Knowledge Base | SHB Bank | Tài chính-Ngân hàng | RAG/LLM | Brief RAG nâng cao rõ nhất, có tài liệu mẫu, ít cạnh tranh |
| 133 | Real-time VI–EN meeting translator | AI Singapore (AISG) | Đổi mới mở | Voice | Hackathon 2 ngày riêng, live-judging rủi ro cao nhưng đúng sở trường Voice |
| 153 | Weather analysis & forecasting | Sở KH&CN Điện Biên | Phòng chống thiên tai | Data/Forecast+Voice | Có API thời tiết mở thật, yêu cầu tối thiểu rất cụ thể |
| 157 | AI Product Comparison Advisor | Điện Máy Xanh | Năng suất DN | RAG/LLM + biz | Rubric % rõ nhất, SLA cụ thể, pilot 3 tháng thật |
| 181 | Speech-to-meaning platform | VALSEA | Đổi mới mở | Voice | Sandbox API thật, đề mở, ít cạnh tranh hơn cụm Vbee |
| 185 | QA & analytics 100% hotline calls | Vbee AITalk | Năng suất DN | Data+Voice (batch) | Khác biệt trong cụm Vbee, không cần real-time <2s |
| 187 | Read Anything — OCR/dịch/đọc | Vbee AITalk | Đổi mới mở | CV(OCR)+Voice | Demo "wow" nhanh nhất, scope gọn, đúng cả CV lẫn Voice |

### Tier A — Khả thi cao

| ID | Đề bài | Sponsor | Track | Khớp năng lực | Ghi chú |
|---|---|---|---|---|---|
| 132 | Digital expert agents | SHB Bank | Tài chính-Ngân hàng | Agent | Multi-agent khó demo trọn vẹn hơn #131, dùng chung hạ tầng |
| 134 | AI customer care assistant | Hanoi Heart Hospital | Y tế | RAG/LLM | Scope hẹp, chắc tay, hợp làm đề dự phòng |
| 136 | Policy & grant navigator | NIC | Đổi mới mở | RAG/LLM | Dữ liệu chính sách công khai dễ crawl |
| 141 | Vietnamese agricultural extension assistant | Duy Tân | Nông nghiệp | RAG/LLM+Voice | Tiêu chí nặng nhất là hallucination rate — đúng sở trường guardrail |
| 146 | Adaptive tutor cho lớp học đa trình độ | Duy Tân | Giáo dục | Data+Agent | Tiêu chí rõ, có khung GDPT 2018 công khai |
| 148 | Career compass | Duy Tân | Giáo dục | Data+RAG | Dữ liệu tuyển dụng crawl được, output giải thích được |
| 151 | Task reminders & progress tracking | Sở KH&CN Điện Biên | Chính phủ số | Agent/Ops | Yêu cầu tối thiểu rất chi tiết, dễ chấm điểm, hợp 2 SE |
| 154 | Paperless Meetings — xử lý tài liệu | Sở KH&CN Điện Biên | Chính phủ số | RAG/Agent | Checklist định lượng cực rõ |
| 155 | Guardian of the mother tongue | Sở VHTT Điện Biên | Đổi mới mở | NLP (text) | Tiêu chí định lượng rõ, độc đáo, gần như chưa ai làm |
| 158 | Personalization & Content Creation | STEAM for Vietnam | Giáo dục | Data+Agent | Rubric có ghi rõ anti-pattern cần tránh |
| 160 | AI-guided public service procedures | NIDit | Chính phủ số | RAG/Agent | Dữ liệu công khai (dichvucong.gov.vn), demo qua URL công khai |
| 162 | Legal knowledge graph | AIZ | Đổi mới mở | RAG + Knowledge Graph | Thu hẹp vào 1 bộ luật sẽ có độ "wow" cao |
| 179 | Cross Team Operation Management | AI for Vietnam | Đổi mới mở | RAG/Agent (nội bộ) | Đề của chính BTC, rủi ro kỹ thuật thấp |
| 180 | Tối ưu lộ trình khám & giảm thời gian chờ | VNPT IT | Đổi mới mở | Data/Agent | Bài toán tối ưu hoá thú vị, chấp nhận đo trên mô phỏng |
| 182 | Voice agent xác nhận đơn hàng TMĐT | Vbee AITalk | Năng suất DN | Voice+Ops | Chuẩn nhưng "vanilla" nhất trong cụm Vbee |
| 183 | Voice agent nhắc thanh toán/nợ | Vbee AITalk | Tài chính-Ngân hàng | Voice+Compliance | Nằm trong track ít đề hơn, góc compliance hợp marketing |
| 186 | Số hoá sách giấy thành audiobook | Vbee AITalk | Giáo dục | CV(OCR)+Voice | Khác biệt tốt trong cụm Vbee, kết hợp CV+Voice |
| 188 | Meeting assistant | Vbee AITalk | Năng suất DN | Voice+RAG | Vbee không có diarization sẵn — thử thách kỹ thuật thật |
| 189 | Slide/giáo án → video bài giảng | Vbee AITalk | Giáo dục | LLM+Voice+CV nhẹ | Thị trường giáo dục rõ, dễ đo lường |
| 191 | Content factory — RSS → podcast + video | Vbee AITalk | Đổi mới mở | LLM+Voice+Ops | Demo ấn tượng, có pipeline publish qua n8n |

### Tier B — Cần thu hẹp scope

| ID | Đề bài | Sponsor | Track | Ghi chú |
|---|---|---|---|---|
| 135 | Deal-flow Matchmaker | NIC | Đổi mới mở | Cần dữ liệu startup/nhà đầu tư thật, dễ demo hời hợt |
| 138 | Biodiversity monitoring qua âm học sinh thái | Duy Tân | Nông nghiệp | Độc đáo nhưng thiếu dữ liệu âm thanh VN thật |
| 142 | Reviving living heritage | Duy Tân | Đổi mới mở | Nội dung văn hoá phải được chuyên gia xác thực |
| 143 | Tourist shield — anti-scam | Duy Tân | Đổi mới mở | Dữ liệu giá tham chiếu gần như không có sẵn |
| 145 | Revenue Brain — pricing homestay nhỏ | Duy Tân | Đổi mới mở | Cold-start forecasting thú vị nhưng thiếu dữ liệu đặt phòng thật |
| 147 | The silent shield — cảnh báo bỏ học sớm | Duy Tân | Giáo dục | Rủi ro đạo đức cao, khó "wow" công nghệ |
| 150 | AI Report Assistant | Duy Tân | Chính phủ số | Thiếu mẫu báo cáo cụ thể để test |
| 152 | AI Platform hỗ trợ quản lý nông nghiệp | Sở KH&CN Điện Biên | Nông nghiệp | 4 chức năng quá rộng, nên chọn 2/4 |
| 156 | AI visual design cho biểu diễn văn hoá | Sở VHTT Điện Biên | Đổi mới mở | Rủi ro cultural fidelity với text-to-image thuần |
| 159 | Clinical compliance automation | DentalTech | Y tế | Đề mơ hồ về nguồn tín hiệu đầu vào |
| 161 | Toolkit chuẩn hoá dataset LLM tiếng Việt | NIDit | Chính phủ số | Công cụ hạ tầng, khó demo ấn tượng |
| 184 | Telesales voice agent | Vbee AITalk | Năng suất DN | Ít khác biệt trong cụm Vbee, cạnh tranh cao |
| 190 | Multi-character audio-story studio | Vbee AITalk | Đổi mới mở | Wow-factor cao nhưng giá trị thương mại kém rõ |

### Tier C — Nên tránh

| ID | Đề bài | Sponsor | Track | Ghi chú |
|---|---|---|---|---|
| 137 | Facility & Event concierge | NIC | Đổi mới mở | Hàm lượng AI mỏng, thiên về vận hành nội bộ |
| 139 | Shrimp pond doctor | Duy Tân | Nông nghiệp | Cần time-series + camera dưới nước thật, không có |
| 140 | Barn Watchdog | Duy Tân | Nông nghiệp | Thiếu dữ liệu hành vi vật nuôi bệnh thật |
| 144 | The road home to the village | Duy Tân | Nông nghiệp | 3 chức năng lớn, điều kiện vùng sóng yếu — quá rộng |
| 149 | AI GreenMap — quản lý cây đô thị | Duy Tân | Nông nghiệp | Cốt lõi là app CRUD, phần AI mỏng |
| 163 | Dynamic pricing tách/ghép chặng tàu | VNR | Năng suất DN | Bài toán vận hành doanh nghiệp thật, quy mô dự án nhiều tháng |
| 164 | Generative AI quy hoạch đất KCN | VRG | Nông nghiệp | Cần dữ liệu GIS/DEM thật, không có |
| 165 | Energy digital twin cho KCN | VRG | Nông nghiệp | Cần dữ liệu SCADA thật, không có |
| 166 | AI điều khiển xử lý nước thải | VRG | Đổi mới mở | Bài toán nghiên cứu điều khiển, cần SCADA thật |
| 167 | Smart urban traffic command | Cần Thơ | Đổi mới mở | Đề quy hoạch cấp thành phố, không dữ liệu |
| 168 | Nhận diện nguồn phát thải real-time | Cần Thơ | Phòng chống thiên tai | Đề chiến lược Net Zero, không dữ liệu quan trắc |
| 169 | Dự báo ngập lụt & sponge-city | Cần Thơ | Đổi mới mở | Cần cả hạ tầng vật lý lẫn phần mềm |
| 170 | Tái thiết đô thị xanh giữ hồn khu phố | Cần Thơ | Đổi mới mở | Bài toán chính sách đô thị, không dữ liệu |
| 171 | Số hoá đất đai & minh bạch BĐS | Cần Thơ | Đổi mới mở | Cần dữ liệu địa chính thật |
| 172 | Logistics đa phương thức liên vùng | Cần Thơ | Nông nghiệp | Đề quy hoạch vùng ĐBSCL, không dữ liệu |
| 173 | Nông nghiệp công nghệ cao thích ứng khí hậu | Cần Thơ | Đổi mới mở | Quy mô cả vùng, không dữ liệu kèm theo |
| 174 | Công nghiệp hoá công nghệ cao | Cần Thơ | Đổi mới mở | Đề chính sách, không bài toán kỹ thuật cụ thể |
| 175 | Hệ sinh thái UAV/Drone dùng chung | Cần Thơ | Đổi mới mở | Cần phần cứng drone thật + khung pháp lý |
| 176 | Private 5G/IoT & testbed 6G | Cần Thơ | Đổi mới mở | Hạ tầng viễn thông vật lý, ngoài phạm vi hackathon |
| 177 | An sinh xã hội đa tầng trên Big Data | Cần Thơ | Chính phủ số | "Phần mềm hoá" dễ nhất trong nhóm Cần Thơ nếu buộc phải chọn |
| 178 | AI tiếng Việt cho hành chính công | Cần Thơ | Nông nghiệp | Nên chọn #160 (NIDit) thay thế — cùng dạng bài, scope rõ hơn |

---

## Phân bổ nhân lực nếu chọn Top 5

| Đề | AI Engineer (x2) | Software Engineer (x2) | Marketing/Tài chính |
|---|---|---|---|
| #131 | Pipeline retrieval + document graph, đánh giá độ chính xác trích dẫn | Vector DB, API backend, giao diện chat demo | Chuẩn hoá corpus chính sách mẫu, kịch bản demo |
| #157 | RAG + guardrail chống bịa thông tin, logic so sánh top-3 | Tích hợp catalog/API, đảm bảo SLA 3–5s, load test | Pilot roadmap 3 tháng, mô hình ROI, pitch theo rubric % |
| #153 | Mô hình downscale dự báo + sinh bản tin cảnh báo | Tích hợp API thời tiết, kênh phân phối Zalo/SMS/loa | Câu chuyện tác động xã hội, giao diện cảnh báo dễ hiểu |
| #181 | Xử lý output ASR thành dữ liệu có cấu trúc | Tích hợp sandbox API VALSEA, demo trước/sau | Chọn/xác thực vertical, định lượng giá trị tiết kiệm |
| #185 | Mô hình chấm điểm cuộc gọi, phát hiện rủi ro khiếu nại | Pipeline batch song song, dashboard, cảnh báo n8n | Ước tính chi phí xử lý, câu chuyện tiết kiệm chi phí QA |

---

*Bản phân tích độc lập dựa trên dữ liệu công khai từ API, không phải đánh giá chính thức của BTC. Bản tương tác (bảng lọc/sắp xếp) xem tại: https://claude.ai/code/artifact/b86602db-4891-4cd6-b527-7f0a27080929*
