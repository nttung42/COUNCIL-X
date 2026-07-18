---
doc_type: case_cu
property_type: all
title: Case đã thẩm định trước đây — tham khảo tình huống tương tự (mock)
---

# Case tham khảo 1 — Tài sản đang thế chấp nơi khác

**Tình huống**: Khách hàng đề nghị thế chấp nhà phố tại Phường Tân Định, Quận 1, nhưng
`legal_status_lookup` phát hiện tài sản đang thế chấp tại 1 tổ chức tín dụng khác
(`mortgaged_elsewhere = true`).

**Khuyến nghị đã áp dụng**: Không từ chối ngay — yêu cầu khách hàng cung cấp văn bản cam kết giải
chấp hoặc thực hiện đồng thời giải chấp + thế chấp mới (tất toán khoản vay cũ bằng 1 phần khoản vay
mới, có xác nhận của bên nhận thế chấp cũ). Hồ sơ chỉ được xử lý tiếp sau khi có xác nhận giải chấp
hoàn tất hoặc cam kết giải chấp đồng thời hợp lệ.

---

# Case tham khảo 2 — Yếu tố dư luận/tâm linh chưa xác thực

**Tình huống**: Nhà phố trong hẻm có tin đồn dân cư (chưa xác thực) về 1 sự việc xảy ra nhiều năm
trước. Risk Scoring Engine gắn flag `type=stigma`, `severity=medium`, `confidence=0.3`,
`verified=false`.

**Khuyến nghị đã áp dụng**: KHÔNG dùng flag này để từ chối hồ sơ. Thêm vào checklist: "khảo sát
thực địa xác minh dư luận dân cư" — thẩm định viên phỏng vấn nhanh 2–3 hộ dân xung quanh, ghi nhận
kết quả vào biên bản. Nếu không phát hiện thêm bằng chứng cụ thể, hồ sơ tiếp tục xử lý bình thường
theo kết quả định giá và các yếu tố đã xác thực khác.

---

# Case tham khảo 3 — Không đủ giao dịch so sánh

**Tình huống**: Đất nền ở khu vực mới phát triển, `market_price_lookup` chỉ tìm được 1 giao dịch so
sánh trong bán kính yêu cầu.

**Khuyến nghị đã áp dụng**: Hạ `confidence_score` của định giá xuống dưới 0.4, ưu tiên trọng số cho
phương pháp chi phí xây dựng (cost approach) thay vì so sánh trực tiếp, và bắt buộc thêm điều kiện
"cần thẩm định viên khảo sát thực địa và tham khảo thêm ít nhất 2 nguồn giá thị trường khác trước
khi phê duyệt" vào checklist.
