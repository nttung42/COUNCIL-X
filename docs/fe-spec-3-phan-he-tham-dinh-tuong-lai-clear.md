# FE SPEC NGẮN GỌN CHO CÁC PHÂN HỆ THẨM ĐỊNH TƯƠNG LAI

## 1. Cách gọi thống nhất

Để tránh nhầm cấp kiến trúc, toàn hệ thống dùng cấu trúc sau:

```text
Nền tảng thẩm định tài sản bảo đảm
└── Phân hệ thẩm định theo nhóm tài sản
    └── Module nghiệp vụ
        └── Agent / Engine
            └── Màn hình / Step UI
```

### Bốn phân hệ của hệ thống

1. **Phân hệ Bất động sản** — MVP hiện tại.
2. **Phân hệ Động sản** — phát triển tương lai.
3. **Phân hệ Giấy tờ có giá** — phát triển tương lai.
4. **Phân hệ Quyền tài sản và tài sản hình thành trong tương lai** — phát triển tương lai.

Tài liệu này chỉ mô tả frontend cho ba phân hệ tương lai. Không mô tả lại MVP bất động sản.

---

# 2. Khung UI dùng chung

## 2.1. Layout

```text
Header
├── Case ID
├── Tên tài sản
├── Loại tài sản
├── Trạng thái
└── Lưu nháp

Left Step Navigation
├── Tổng quan
├── Các bước thẩm định
├── Kết quả định giá
├── Rủi ro
└── Báo cáo

Main Workspace
├── Dữ liệu đầu vào
├── Kết quả phân tích
├── Finding
└── Human review

Right Panel
├── Evidence
├── Nguồn dữ liệu
└── Lịch sử xử lý
```

## 2.2. Component dùng chung

- `CaseHeader`
- `StepNavigation`
- `MetricCard`
- `FindingCard`
- `EvidenceCard`
- `RiskBadge`
- `ConfidenceBadge`
- `SourceTable`
- `CalculationTable`
- `HumanReviewBox`
- `ReportPreview`
- `ConceptLabel`

## 2.3. Trạng thái cần có

- `Not started`
- `Processing`
- `Waiting for data`
- `Waiting for human review`
- `Completed`
- `Blocked`
- `Inconclusive`

Mỗi kết quả quan trọng có:

- Confirm
- Edit
- Reject
- Add note
- Add evidence

Khi Edit hoặc Reject phải nhập lý do.

---

# 3. Phân hệ Động sản

## 3.1. Phạm vi

- Phương tiện vận tải
- Máy móc thiết bị
- Hàng hóa, hàng tồn kho
- Tài sản hữu hình có thể di chuyển

## 3.2. Route

```text
/appraisals/movable-assets/:caseId
```

## 3.3. Các module nghiệp vụ và màn hình

### Module 1 — Nhận diện tài sản

Màn hình hiển thị:

- Loại tài sản
- Nhãn hiệu, model
- Năm sản xuất
- Serial, số khung, số máy
- Thông số kỹ thuật
- Chủ sở hữu
- Vị trí hiện tại
- Hồ sơ đăng ký
- Confidence và nguồn trích xuất

### Module 2 — Quyền sở hữu và hạn chế

Màn hình checklist:

- Có chứng từ sở hữu
- Serial khớp hồ sơ
- Đăng ký còn hiệu lực
- Không có tranh chấp
- Không có hạn chế chuyển nhượng
- Chưa phát hiện cầm cố trước đó

### Module 3 — Tình trạng tài sản

Màn hình hiển thị:

- Tình trạng vật lý
- Khả năng vận hành
- Mức độ sử dụng
- Lịch sử bảo trì
- Hư hỏng
- Tuổi đời còn lại
- Bộ ảnh kiểm tra

### Module 4 — Giá thị trường và chi phí thay thế

Bảng dữ liệu:

| Nguồn | Tài sản tương đồng | Giá | Ngày | Độ tin cậy | Sử dụng |
| ------ | ------------------------ | ---: | ----- | ------------- | --------- |

Metric:

- Giá tài sản mới tương đương
- Giá thị trường tài sản đã qua sử dụng
- Chi phí vận chuyển
- Chi phí lắp đặt
- Chi phí tháo dỡ

### Module 5 — Khấu hao và lỗi thời

Bảng:

| Yếu tố | Tỷ lệ | Lý do | Human edit |
| -------- | ------: | ------ | ---------- |

Bao gồm:

- Hao mòn vật lý
- Lỗi thời kỹ thuật
- Lỗi thời công năng
- Lỗi thời kinh tế

### Module 6 — Thanh khoản và định giá

Hero metrics:

- Giá trị thị trường
- Giá trị thanh lý
- Haircut đề xuất
- Giá trị bảo đảm điều chỉnh
- Confidence
- Thời gian xử lý dự kiến

### Module 7 — Báo cáo

Các phần:

- Hồ sơ tài sản
- Quyền sở hữu
- Tình trạng
- Dữ liệu thị trường
- Khấu hao
- Thanh khoản
- Giá trị
- Rủi ro
- Evidence
- Giới hạn

---

# 4. Phân hệ Giấy tờ có giá

## 4.1. Phạm vi

- Trái phiếu
- Cổ phiếu
- Chứng chỉ tiền gửi
- Kỳ phiếu
- Hối phiếu
- Các giấy tờ có giá đủ điều kiện nhận bảo đảm

## 4.2. Route

```text
/appraisals/valuable-papers/:caseId
```

## 4.3. Các module nghiệp vụ và màn hình

### Module 1 — Hồ sơ công cụ tài chính

Field:

- Loại giấy tờ
- Mã công cụ
- Tổ chức phát hành
- Mệnh giá
- Số lượng
- Lãi suất
- Ngày phát hành
- Ngày đáo hạn
- Đơn vị lưu ký
- Trạng thái niêm yết

### Module 2 — Quyền sở hữu và tính xác thực

Checklist:

- Công cụ tồn tại
- Quyền sở hữu đã xác minh
- Lưu ký đã xác minh
- Không bị phong tỏa
- Không bị cầm cố trước
- Được phép chuyển nhượng

### Module 3 — Rủi ro tổ chức phát hành

Metric:

- Xếp hạng tín nhiệm
- Khả năng thanh toán
- Xác suất vỡ nợ
- Tình trạng tài chính
- Cảnh báo gần nhất

### Module 4 — Khả năng giao dịch

Hiển thị:

- Niêm yết/chưa niêm yết
- Khối lượng giao dịch
- Bid–ask spread
- Biến động giá
- Số ngày dự kiến để bán
- Hạn chế chuyển nhượng

### Module 5 — Định giá

Bảng:

| Phương pháp | Giá trị | Giả định | Confidence |
| -------------- | --------: | ----------- | ---------- |

Có thể gồm:

- Giá thị trường
- Giá trị hiện tại
- Giá theo yield
- Giá trong stress scenario

### Module 6 — Haircut và giá trị bảo đảm

Breakdown:

- Haircut rủi ro tín dụng
- Haircut rủi ro thị trường
- Haircut thanh khoản
- Haircut kỳ hạn
- Haircut tập trung

Output:

- Tổng haircut
- Giá trị bảo đảm điều chỉnh
- Confidence

### Module 7 — Báo cáo

Các phần:

- Hồ sơ giấy tờ
- Quyền sở hữu
- Rủi ro tổ chức phát hành
- Khả năng giao dịch
- Định giá
- Haircut
- Evidence
- Giới hạn

---

# 5. Phân hệ Quyền tài sản và tài sản hình thành trong tương lai

## 5.1. Phạm vi

- Quyền đòi nợ
- Khoản phải thu
- Quyền phát sinh từ hợp đồng
- Quyền khai thác
- Quyền tài sản trí tuệ nếu đủ điều kiện
- Tài sản hoặc dự án đang hình thành trong tương lai

## 5.2. Route

```text
/appraisals/property-rights/:caseId
```

## 5.3. Các module nghiệp vụ và màn hình

### Module 1 — Hồ sơ quyền và hợp đồng

Field:

- Chủ thể quyền
- Bên có nghĩa vụ
- Hợp đồng cơ sở
- Giá trị hợp đồng
- Ngày hiệu lực
- Ngày hết hạn
- Điều kiện phát sinh quyền
- Hạn chế chuyển giao

### Module 2 — Khả năng thực thi pháp lý

Checklist:

- Quyền tồn tại hợp pháp
- Được phép chuyển giao
- Được phép dùng làm tài sản bảo đảm
- Điều kiện phát sinh đã hoàn thành
- Không có tranh chấp
- Có đầy đủ chấp thuận cần thiết

### Module 3 — Đánh giá bên có nghĩa vụ

Metric:

- Năng lực thanh toán
- Lịch sử thanh toán
- Mức độ tập trung
- Phụ thuộc vào một bên
- Tranh chấp
- Cảnh báo tín dụng

### Module 4 — Dòng tiền và khả năng thu hồi

Bảng aging:

| Nhóm tuổi nợ | Giá trị | Xác suất thu hồi | Giá trị điều chỉnh |
| --------------- | --------: | ------------------: | ----------------------: |

Hiển thị:

- Tổng giá trị phải thu
- Phần đang tranh chấp
- Xác suất thu hồi
- Dilution
- Giá trị thu hồi ròng

### Module 5 — Tiến độ tài sản tương lai

Timeline:

```text
Phê duyệt pháp lý
→ Khởi công
→ Hoàn thành
→ Nghiệm thu
→ Đăng ký
→ Xác lập quyền sở hữu
```

Mỗi milestone có:

- Ngày dự kiến
- Ngày thực tế
- Trạng thái
- Evidence
- Rủi ro chậm tiến độ

### Module 6 — Định giá theo kịch bản

Ba scenario card:

- Base
- Downside
- Stress

Mỗi card có:

- Giả định
- Xác suất
- Giá trị

Output:

- Giá trị bình quân theo xác suất
- Haircut
- Giá trị bảo đảm điều chỉnh
- Confidence

### Module 7 — Điều kiện theo dõi

Bảng:

| Trigger | Ngưỡng | Hiện tại | Trạng thái | Hành động |
| ------- | -------- | ---------- | ------------ | ------------ |

Ví dụ:

- Chậm thanh toán
- Chậm milestone
- Hợp đồng bị sửa đổi
- Bên có nghĩa vụ bị hạ xếp hạng
- Phát sinh tranh chấp

### Module 8 — Báo cáo

Các phần:

- Hồ sơ quyền
- Khả năng thực thi
- Đánh giá đối tác
- Dòng tiền
- Tiến độ
- Định giá theo kịch bản
- Điều kiện theo dõi
- Evidence
- Giới hạn

---

# 6. Dữ liệu mock tối thiểu

## Case

```json
{
  "caseId": "CASE-001",
  "appraisalDomain": "movable_assets",
  "assetSubtype": "vehicle",
  "assetName": "Xe tải ABC",
  "owner": "Công ty ABC",
  "status": "waiting_for_review",
  "riskLevel": "medium",
  "confidence": 0.78,
  "currentStep": "valuation"
}
```

## Finding

```json
{
  "id": "F-001",
  "title": "Serial không khớp",
  "severity": "high",
  "description": "Serial trên ảnh khác hồ sơ đăng ký.",
  "status": "open"
}
```

## Human override

```json
{
  "field": "haircut",
  "aiValue": 0.15,
  "humanValue": 0.20,
  "reason": "Thanh khoản thấp tại thị trường địa phương"
}
```

---

# 7. Prompt khung để gen frontend

```text
Create a desktop-first frontend for the [APPRAISAL DOMAIN] appraisal domain
inside an existing bank collateral appraisal platform.

Primary user: collateral appraiser.

Architecture level:
- appraisal domain
- business capability modules
- screens inside each module

Reuse the existing real-estate MVP design system:
- case header
- left step navigation
- main analysis workspace
- right evidence panel
- bottom human-review actions

Required capability modules:
[LIST MODULES]

Use mock JSON data.
Show findings, evidence, confidence, calculation details and human override.
Label the page as FUTURE APPRAISAL DOMAIN.
Do not include loan approval actions.
```

---

# 8. Checklist hoàn thành

Mỗi phân hệ tương lai chỉ cần:

- Một route chính
- Một overview
- Sidebar theo module nghiệp vụ
- Dữ liệu mock
- Finding và evidence
- Kết quả định giá
- Risk và haircut
- Human review
- Report preview
- Không có dead link
- Dùng cùng design system với MVP bất động sản
- Gắn nhãn `FUTURE APPRAISAL DOMAIN`

---

# 9. Kết luận

> **Bất động sản, động sản, giấy tờ có giá và quyền tài sản là bốn phân hệ thẩm định theo nhóm tài sản. Bên trong mỗi phân hệ mới chia thành các module nghiệp vụ; bên trong module mới có agent, engine và màn hình. Cách phân cấp này phải được giữ nhất quán trong cả kiến trúc, codebase và UI.**
