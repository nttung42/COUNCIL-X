# 🎬 KỊCH BẢN DEMO — SHB PAA (Vietnam AI Innovation Challenge 2026)

> **Thông điệp xuyên suốt (nói ở mở đầu và lặp lại ở kết):**
> *"AI thẩm định tài sản mà cán bộ tín dụng DÁM KÝ TÊN lên kết quả — vì mọi con số
> đều truy vết được về nguồn: từng trường trích xuất chỉ đúng vùng trên giấy tờ gốc,
> từng đồng định giá có công thức, LLM chỉ làm việc phụ trong ranh giới đóng khung."*

**Case demo:** `REQ-2026-2000` — Nhà phố 64 Võ Thành I, P.12, Q.10, TP.HCM (dữ liệu nhân thân hư cấu).
**Thời lượng:** ~8 phút demo + Q&A. **Màn 1 chiếm ~3,5 phút** (điểm nhấn chính).

---

## 0. CHUẨN BỊ TRƯỚC DEMO (checklist 15 phút trước giờ G)

```bash
# 1. Backend (từ e:/COUNCIL-X/ai) — docker phải Up, trỏ DB đúng (.env)
docker compose up -d && docker compose ps           # 4 container Up
curl -s http://localhost:8888/health                 # → 200

# 2. Case demo đầy đủ 5 màn (idempotent — chạy lại nếu nghi ngờ)
.venv/Scripts/python.exe scripts/prepare_demo_case.py   # → "DONE — case demo sẵn sàng"

# 3. Bộ hồ sơ demo (4 PDF) — nếu chưa có thì sinh lại
.venv/Scripts/python.exe scripts/make_demo_docs.py      # → samples/demo/*.pdf

# 4. Frontend (từ e:/COUNCIL-X/apps/frontend)
#    .env phải có:  VITE_API_BASE_URL=http://localhost:8888
npm run dev                                          # → http://localhost:5173
```

**Trên máy trình chiếu:**
- [ ] Mở sẵn thư mục `ai/samples/demo/` (4 PDF) trong Explorer — kéo-thả cho mượt.
- [ ] Mở sẵn 1 PDF (GCN) ở cửa sổ nhỏ → giới thiệu "hồ sơ khách nộp" trước khi vào web.
- [ ] Browser tab 1: `http://localhost:5173` → điều hướng tới workspace thẩm định (case REQ-2026-2000). Tab 2 (dự phòng): Postman.
- [ ] Zoom browser 110–125%, tắt notification, tắt các tab thừa.
- [ ] **Chạy nháp 1 lần extraction** trước giờ demo để LLM "ấm" và chắc chắn ổn định.

---

## 1. MỞ MÀN (30s) — bối cảnh

**Nói:** "Mỗi hồ sơ vay thế chấp, cán bộ mất 2–3 ngày: đọc sổ đỏ, gõ lại từng số,
tra quy hoạch, gọi môi giới hỏi giá, tự chấm rủi ro. SHB PAA nén quy trình đó xuống
**vài phút** — nhưng khác các demo AI thông thường: **mọi kết quả đều có nguồn gốc
và công thức, đủ chuẩn để ngân hàng audit**."

**Làm:** Đưa 4 file PDF trong Explorer lên màn hình: *"Đây là bộ hồ sơ khách hàng nộp —
sổ đỏ 2 trang, tờ khai lệ phí trước bạ, biên bản bàn giao, thông báo thuế đất.
Đúng những gì một bộ hồ sơ thật có."* (Mở nhanh GCN cho giám khảo thấy độ "thật".)

---

## 2. MÀN 1 — NHẬP THÔNG TIN (3,5 phút — TRÁI TIM CỦA DEMO)

### 2.1 Đồng hành cùng Assistant (15s)
Vào workspace → **Collateral Assistant** (khung chat trái) chào và gợi ý bắt đầu.
**Nói:** *"Trợ lý đồng hành suốt quy trình — mỗi bước nó thông báo hệ thống đang làm gì,
và cán bộ có thể ra lệnh chỉnh sửa bằng ngôn ngữ tự nhiên."*

### 2.2 Upload + trích xuất realtime (60s)
1. Click vùng upload → chọn cả **4 PDF** trong `samples/demo/` → danh sách file hiện ra.
2. Bấm **"Trích xuất dữ liệu từ tài liệu"**.
3. **Chỉ vào progress bar chạy %** — **Nói:** *"Tiến độ này là **SSE realtime** đẩy từ
   pipeline: hệ thống đang phân loại từng tài liệu, trích xuất bằng LLM, **thẩm định
   chéo** và **định vị từng giá trị trên trang gốc**. Không phải thanh giả lập."*
4. Chờ hoàn tất (~60–90s — trong lúc chờ nói tiếp ý 2.3). Assistant báo:
   *"Đã trích xuất 24 trường từ 5 tài liệu…"*

**Lấp thời gian chờ — Nói:** *"Phía sau là pipeline 6 bước trên LangGraph:
nhận dạng loại giấy tờ → trích xuất theo schema riêng từng loại → LLM thẩm định lại
từng giá trị → hợp nhất đa nguồn theo độ ưu tiên pháp lý (sổ đỏ > thông báo thuế >
tờ khai > biên bản) → kiểm tra quy tắc số học → gắn nguồn gốc."*

### 2.3 SHOWCASE: References + Bounding box (75s — ĐINH CỦA DEMO)
Form 4 nhóm A/B/C/D đã đầy ~24/30 trường, mỗi trường có **badge % tin cậy** và **chip nguồn**.

1. **Click chip nguồn của "Diện tích đất — 199,30 m²"** → doc viewer nhảy đúng
   tài liệu, đúng trang, **highlight đúng dòng trên sổ đỏ**.
   **Nói:** *"Đây không phải trang trí. Toạ độ này do hệ thống **tìm lại đúng vị trí
   chuỗi gốc trong file PDF** — deterministic, không phải LLM đoán. Cán bộ nghi ngờ số
   nào, một click là thấy nó nằm ở đâu trên giấy tờ."*
2. Click tiếp nguồn của **"Tình trạng thế chấp"** → nhảy sang **trang 2** của GCN,
   highlight "Chưa thế chấp tại TCTD nào" → *"kể cả thông tin nằm ở trang ghi chú biến động."*
3. **Chỉ vào 3 loại trạng thái minh bạch:**
   - `Đã xác thực` (xanh, ~99%) — có nguồn + LLM thẩm định lại đồng ý;
   - `Suy luận` ("Mối quan hệ với tài sản") — *"hệ thống nói thẳng đây là suy luận, không phải đọc từ giấy"*;
   - `Cần xác minh` ("Diện tích sàn") — **mở cảnh báo**: *"245,2m² sàn lệch so với
     đất × số tầng — hệ thống **tự kiểm tra số học chéo** và đòi con người xác nhận
     thay vì im lặng cho qua. Đây là triết lý: AI không được tự tin hơn mức nó đáng được tin."*
4. **Nói:** *"6 trường trống là những gì giấy tờ **thật sự không có** — khoản vay,
   lộ giới… hệ thống không bịa. Cán bộ nhập tay phần của con người."*

### 2.4 Assistant chỉnh sửa + xác nhận (30s)
1. Gõ vào chat: **"sửa diện tích"** (hoặc từ khoá demo tương ứng) → Assistant thao tác
   chỉnh sửa trường, badge **"chờ xác nhận"** hiện lên.
2. **Nói:** *"Mọi chỉnh sửa đều ở trạng thái chờ — bấm **Xác nhận & tiếp theo** mới chốt.
   Con người luôn là người ký."* → Bấm **Xác nhận & tiếp theo →**.

---

## 3. MÀN 2 — KẾT QUẢ TRA CỨU (60s)

Tab 2 mở khoá, Assistant báo đang tra cứu. Màn hiện **7 nguồn tra cứu** + bảng
**giao dịch so sánh khu vực**.

**Nói + chỉ:**
- Badge 3 mức: **Đã xác thực / Lưu ý / Chưa xác thực** — *"nguồn nào đáng tin bao nhiêu, nói rõ."*
- Mở card **Pháp lý (Lưu ý)**: *"phát hiện ghi chú thế chấp đã tất toán chưa xoá đăng ký —
  đúng loại chi tiết cán bộ hay bỏ sót."*
- Card **Dư luận/tâm linh**: *"tin đồn chỉ được gắn 'chưa xác thực' — nó sẽ **không bao giờ**
  được dùng để từ chối khoản vay, chỉ để cảnh báo."*

→ **Xác nhận & tiếp theo**.

## 4. MÀN 3 — ĐỊNH GIÁ (75s)

KPI hiện **29,63 tỷ** (khoảng 27,8–32,2 tỷ, tin cậy 83%) + bar chart 3 phương pháp + sparkline chỉ số giá.

**Nói (thông điệp quan trọng thứ 2):**
- *"3 phương pháp — so sánh giao dịch, hedonic, chi phí — **tính bằng công thức**,
  trọng số hiển thị ngay đây, bảng quy đổi ngay đây. Ai cũng kiểm lại được bằng máy tính bỏ túi."*
- Chỉ vào khối điều chỉnh cảm tính: *"Duy nhất chỗ này có LLM: yếu tố **hướng nhà,
  phong thủy** — và nó bị đóng khung **±5%**, ghi rõ lý do, tách riêng khỏi công thức.
  LLM lỗi? Hệ thống tự về 0% và định giá thuần công thức vẫn chạy."*
- *"5 yếu tố cấu thành độ tin cậy 83% cũng là công thức — không phải cảm giác."*

→ **Xác nhận & tiếp theo**.

## 5. MÀN 4 — RỦI RO (60s)

2 đồng hồ: **điểm rủi ro 37/100 (trung bình)** + **LTV đề xuất 65%**, bar 5 nhóm, flags.

**Nói (thông điệp quan trọng thứ 3):**
- *"Điểm rủi ro quyết định LTV — tức là quyết định **tiền**. Nên khối này **0% LLM**:
  5 nhóm trọng số 30/25/20/15/10, mỗi nhóm ghi rõ điểm cộng từ đâu (đang thế chấp +20,
  nhà >30 năm +15…). Chạy lại 100 lần ra đúng 1 kết quả — audit được."*
- Chỉ khung LTV: *"37 điểm rơi vào khung 21–40 → tối đa 65%. Khung này là **chính sách
  cấu hình trong DB**, ngân hàng đổi không cần sửa code."*
- Flag môi trường/pháp lý: *"mỗi cảnh báo link ngược về nhóm rủi ro sinh ra nó."*

→ **Xác nhận & tiếp theo**.

## 6. MÀN 5 — DASHBOARD KÝ DUYỆT (60s)

KPI tổng hợp + **Kết luận: Đề xuất cho vay theo mức LTV chuẩn — hạn mức tối đa 19,26 tỷ**
+ tóm tắt 4 bước + **timeline trace thực thi**.

**Nói + làm:**
- *"Hạn mức = 29,63 tỷ × 65% = 19,26 tỷ — phép nhân ai cũng kiểm được, kèm chuỗi lý do."*
- Chỉ tóm tắt 4 bước: *"Văn ở đây do LLM viết lại cho mượt — nhưng **mọi con số bị khoá**,
  LLM không sửa được; LLM chết thì hệ thống tự về bản template. Click một dòng là nhảy
  về đúng màn tương ứng."*
- Chỉ **trace**: *"Toàn bộ phiên chạy của agent được ghi vết — ai làm gì, lúc nào. Compliance."*
- Bấm **"Xuất báo cáo thẩm định"** → mở file HTML biên bản vừa tải: *"Biên bản hoàn chỉnh
  cho hồ sơ tín dụng."*

## 7. CHỐT (30s)

*"5 bước, một hồ sơ thật, vài phút thay vì vài ngày. Và điều chúng tôi tự hào nhất
không phải tốc độ — mà là **từng con số đều dám cho audit**: trích xuất có toạ độ nguồn,
định giá có công thức, rủi ro 100% xác định, LLM chỉ đứng ở nơi được đóng khung.
Đó là AI mà ngân hàng ký tên lên được."*

---

## 🛡️ PHƯƠNG ÁN DỰ PHÒNG

| Sự cố | Xử lý ngay trên sân khấu |
|---|---|
| Extraction chậm >2' | Cứ nói tiếp phần pipeline (mục 2.2); SSE vẫn cập nhật khi xong |
| LLM lỗi / hết quota | Màn 3/5 tự **fail-safe**: định giá thuần công thức, tóm tắt về template — *biến nó thành điểm cộng: "đây chính là fail-safe đang hoạt động"* |
| SSE treo | FE tự giữ dữ liệu demo + hiện cảnh báo — chuyển sang kể theo màn hình; hoặc F5 (reload) chạy lại màn đó |
| Backend chết hẳn | Tắt `VITE_API_BASE_URL` trong `apps/frontend/.env`, restart `npm run dev` → **chế độ fixture** giống hệt UI, demo tiếp không lộ |
| Mạng tới DB remote (3.26.176.204) chập | `docker compose exec` kiểm tra; nếu hỏng → xoá `docker-compose.override.yml` + `docker compose up -d` → về Postgres local (nạp seed bằng `scripts/load_seed.sh` từ trước) |

## ❓ Q&A DỰ KIẾN (trả lời 1 câu)

- **"LLM hallucination thì sao?"** → 3 lớp: verifier thẩm định lại từng giá trị + kiểm tra số học chéo + trạng thái `suy_luận/cần xác minh` bắt con người xác nhận; còn tiền (định giá/rủi ro) thì không cho LLM quyết.
- **"Bounding box do AI đoán à?"** → Không — sau khi LLM trích giá trị, hệ thống tìm lại đúng chuỗi đó trong text layer PDF bằng thuật toán, toạ độ là của file gốc.
- **"Tài liệu scan (ảnh chụp) thì sao?"** → Pipeline hybrid: trang scan được render và đọc bằng vision model; bbox khi đó tắt an toàn (chỉ còn snippet nguồn) — không giả vờ chính xác hơn thực tế.
- **"Đổi chính sách LTV phải sửa code?"** → Không, khung LTV nằm trong bảng DB; trọng số công thức nằm trong config.
- **"Số liệu tra cứu Màn 2 lấy đâu ra?"** → Demo dùng dữ liệu nghiên cứu nạp sẵn; kiến trúc adapter đã sẵn để cắm nguồn thật (API quy hoạch, sàn giao dịch) — roadmap kế tiếp.
- **"Sửa thông tin xong hệ số có tính lại không?"** → Có — các màn sau luôn đọc bản dữ liệu mới nhất trong DB; xác nhận xong bước nào hệ thống chạy lại từ bước đó.

## 📋 THAM SỐ CHUẨN CỦA CASE DEMO (để đối chiếu nhanh khi nói)

| Chỉ số | Giá trị |
|---|---|
| Trích xuất Màn 1 | **24/30 trường · 24 bbox · 0 mâu thuẫn** (2 field cần xác minh — chủ đích) |
| Định giá | **29,63 tỷ** (27,8–32,2 tỷ) · tin cậy 83% · 3 phương pháp 65/19/16 |
| Rủi ro | **37/100 trung bình** → LTV **65%** (khung 21–40) |
| Kết luận | **Đề xuất cho vay** · hạn mức **19.259.500.000 đ** |
