---
doc_type: quy_trinh
property_type: all
title: Quy trình thẩm định tài sản bảo đảm là bất động sản (nội bộ SHB — mock)
---

# Quy trình thẩm định tài sản bảo đảm là Bất động sản

> Tài liệu mô phỏng (mock) cho demo hackathon — không phải quy trình chính thức của SHB.

## Bước 1 — Tiếp nhận hồ sơ
- Thu thập thông tin tài sản: địa chỉ, diện tích, loại hình, tình trạng pháp lý khai báo.
- Xác nhận mục đích vay và số tiền đề nghị.

## Bước 2 — Tra cứu dữ liệu khu vực
- Tra cứu giao dịch so sánh trong bán kính 1–2km, ưu tiên giao dịch trong 12 tháng gần nhất.
- Tra cứu quy hoạch, tình trạng pháp lý, tiện ích, môi trường, thanh khoản khu vực.
- Với thông tin dư luận/tin đồn: LUÔN gắn nhãn "chưa xác thực", không dùng làm căn cứ chính.

## Bước 3 — Định giá
- Áp dụng tối thiểu 2 trong 3 phương pháp: so sánh trực tiếp, hedonic, chi phí xây dựng.
- Với BĐS có <3 giao dịch so sánh phù hợp: bắt buộc ghi chú "độ tin cậy thấp, cần thẩm định viên bổ sung khảo sát thực địa".
- Giá trị cuối cùng PHẢI trình bày kèm khoảng tin cậy (range), không chỉ 1 số tuyệt đối.

## Bước 4 — Đánh giá rủi ro tài sản
- Chấm điểm 5 nhóm rủi ro: pháp lý (30%), thanh khoản (25%), biến động giá (20%), vật lý/môi
  trường (15%), danh tiếng/tâm linh (10%).
- Nhóm danh tiếng/tâm linh chỉ tạo flag cảnh báo, KHÔNG được dùng để tự động từ chối hồ sơ.
- Đề xuất LTV (tỷ lệ cho vay trên giá trị định giá) dựa trên risk_tier: LOW ≤30 → LTV tối đa 70%,
  MEDIUM 31–60 → LTV tối đa 65%, HIGH >60 → LTV tối đa 50% hoặc yêu cầu tài sản bảo đảm bổ sung.

## Bước 5 — Soạn biên bản & checklist
- Sinh checklist các mục cần thẩm định viên xác minh thực địa dựa trên flag đã phát hiện.
- Soạn nháp biên bản gồm: thông tin tài sản, định giá, rủi ro & LTV, chữ ký còn trống.
- Biên bản LUÔN kết thúc bằng bước ký duyệt của thẩm định viên và chuyên viên tín dụng — không có
  bước nào trong quy trình này được coi là quyết định cuối cùng nếu chưa có chữ ký con người.

## Nguyên tắc bắt buộc xuyên suốt
1. Không tự suy đoán số liệu — luôn dựa trên dữ liệu tra cứu được.
2. Giải thích được (explainable): mọi kết luận phải nêu rõ phương pháp và nguồn dữ liệu.
3. Tin đồn/tâm linh không phải căn cứ từ chối tín dụng.
4. Khi thiếu dữ liệu/độ tin cậy thấp: luôn flag "cần thẩm định viên xác minh thực địa".
