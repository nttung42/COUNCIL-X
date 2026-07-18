import type {
  AppraisalCaseFull,
  AppraisalCaseSummary,
  AttachedDocument,
  DocPage,
  Tab1Field,
} from '../types';

// Dữ liệu demo tĩnh cho hồ sơ REQ-2026-0001, chuyển thể 1:1 từ ai/PAA_Mockup_SHB_8.html.
// Khi API thật sẵn sàng, thay thế điểm dùng fixtureCase trong src/services/apiClient.ts
// bằng lời gọi API — phần còn lại của UI không cần đổi vì đã theo type AppraisalCaseFull.

export const CASE_ID = 'REQ-2026-2000';

export const caseHistory: AppraisalCaseSummary[] = [
  { caseId: 'REQ-2026-0001', address: 'Hẻm 45 Nguyễn Văn A, Q.C', status: 'dang_xu_ly', updatedAtLabel: 'hôm nay' },
  { caseId: 'REQ-2026-0002', address: '12 Trần Văn B, Q.7', status: 'hoan_tat', updatedAtLabel: 'hôm qua' },
  { caseId: 'REQ-2026-0003', address: 'Chung cư Sunview, Q.Bình Thạnh', status: 'hoan_tat', updatedAtLabel: '3 ngày trước' },
  { caseId: 'REQ-2026-0004', address: 'Đất nền Long Thành, Đồng Nai', status: 'hoan_tat', updatedAtLabel: 'tuần trước' },
  { caseId: 'REQ-2026-0005', address: '34 Lê Văn C, Q.10', status: 'huy', updatedAtLabel: '2 tuần trước' },
];

export const docPages: DocPage[] = [
  { key: 'so-hong', label: 'Sổ hồng' },
  { key: 'to-khai', label: 'Tờ khai LPTB' },
  { key: 'bien-ban', label: 'Biên bản BG' },
  { key: 'tb-thue', label: 'TB thuế đất (scan)', scan: true },
];

/** Danh mục tệp mẫu để mô phỏng thao tác tải lên (dropzone demo, không upload thật). */
export const mockUploadPool: Omit<AttachedDocument, 'id' | 'uploadedAtLabel'>[] = [
  { fileName: 'so-hong-scan.pdf', icon: '📜', docCategory: 'so_do_so_hong' },
  { fileName: 'cccd-chu-so-huu.jpg', icon: '🪪', docCategory: 'cmnd_cccd' },
  { fileName: 'hop-dong-mua-ban.pdf', icon: '📃', docCategory: 'hop_dong' },
  { fileName: 'anh-hien-trang-1.jpg', icon: '📷', docCategory: 'anh_hien_trang' },
  { fileName: 'anh-hien-trang-2.jpg', icon: '📷', docCategory: 'anh_hien_trang' },
  { fileName: 'giay-phep-xay-dung.pdf', icon: '🏗️', docCategory: 'khac' },
];

// Danh sách phẳng — key/section/label khớp NGUYÊN VĂN với FormField mà plugin property_intake
// thật trả về (xác nhận qua 1 job "completed" thực tế gọi từ backend ai/, 2026-07-18) — KHÔNG
// còn tự đặt key kiểu "section.camelCase" nữa vì backend dùng snake_case phẳng không tiền tố.
// Ngoại lệ duy nhất: 'frontage_depth' (Kích thước mặt tiền × chiều sâu) — có trong mockup nhưng
// backend hiện chưa trích xuất trường này, nên luôn ở trạng thái nhập tay cho tới khi có tool hỗ trợ.
// bbox tính theo % kích thước trang (0-100); quy đổi từ BBox (0-1) của API xảy ra ở apiClient.ts.
const tab1Fields: Tab1Field[] = [
  // A. Thông tin bên vay / chủ sở hữu
  {
    key: 'owner_full_name',
    section: 'A',
    label: 'Họ và tên',
    value: 'Nguyễn Văn A',
    confidencePct: 98,
    status: 'da_xac_thuc',
    sourceDocKey: 'so-hong',
    sourceSnippet: 'Sổ hồng · trang 1: “Người sử dụng đất, chủ sở hữu: Ông NGUYỄN VĂN A”',
    bbox: { top: 24, left: 8, w: 68, h: 5 },
  },
  {
    key: 'owner_national_id',
    section: 'A',
    label: 'Số CMND/CCCD',
    value: '079xxxxxxxxx',
    confidencePct: 95,
    status: 'da_xac_thuc',
    sourceDocKey: 'to-khai',
    sourceSnippet: 'Tờ khai lệ phí trước bạ · mục Người nộp: “CCCD số 079xxxxxxxxx”',
    bbox: { top: 21, left: 10, w: 60, h: 5 },
  },
  {
    key: 'owner_phone',
    section: 'A',
    label: 'Số điện thoại',
    value: '09xx xxx xxx',
    confidencePct: null,
    status: 'nhap_tay',
    sourceDocKey: null,
    sourceSnippet: 'Không có trong tài liệu tài sản — nhập tay.',
    bbox: null,
  },
  {
    key: 'relationship_to_asset',
    section: 'A',
    label: 'Mối quan hệ với tài sản',
    value: 'Chủ sở hữu đứng tên trên GCN',
    confidencePct: null,
    status: 'suy_luan',
    sourceDocKey: 'so-hong',
    sourceSnippet: 'Suy ra từ đối chiếu: tên người vay trùng tên chủ sở hữu trên Sổ hồng.',
    bbox: null,
  },

  // B. Thông tin pháp lý tài sản
  {
    key: 'certificate_type',
    section: 'B',
    label: 'Loại giấy chứng nhận',
    value: 'Sổ hồng (QSDĐ & QSH nhà ở)',
    confidencePct: 97,
    status: 'da_xac_thuc',
    sourceDocKey: 'so-hong',
    sourceSnippet: 'Sổ hồng · tiêu đề: “GIẤY CHỨNG NHẬN QUYỀN SỬ DỤNG ĐẤT, QUYỀN SỞ HỮU NHÀ Ở...”',
    bbox: { top: 5, left: 12, w: 76, h: 5 },
  },
  {
    key: 'certificate_number',
    section: 'B',
    label: 'Số giấy chứng nhận',
    value: 'CS 01234567',
    confidencePct: 96,
    status: 'da_xac_thuc',
    sourceDocKey: 'so-hong',
    sourceSnippet: 'Sổ hồng · góc trên bên phải: “Số phát hành: CS 01234567”',
    bbox: { top: 14, left: 58, w: 34, h: 5 },
  },
  {
    key: 'issue_date',
    section: 'B',
    label: 'Ngày cấp',
    value: '14/03/2019',
    confidencePct: 93,
    status: 'da_xac_thuc',
    sourceDocKey: 'so-hong',
    sourceSnippet: 'Sổ hồng · trang 2: “Ngày 14 tháng 3 năm 2019 — Giám đốc Sở TN&MT”',
    bbox: { top: 88, left: 48, w: 44, h: 6 },
  },
  {
    key: 'issuing_authority',
    section: 'B',
    label: 'Cơ quan cấp',
    value: 'Sở TN&MT TP',
    confidencePct: 93,
    status: 'da_xac_thuc',
    sourceDocKey: 'so-hong',
    sourceSnippet: 'Sổ hồng · trang 2: “Ngày 14 tháng 3 năm 2019 — Giám đốc Sở TN&MT”',
    bbox: null,
  },
  {
    key: 'land_plot_number',
    section: 'B',
    label: 'Số thửa',
    value: 'Thửa 45',
    confidencePct: 68,
    status: 'da_xac_thuc',
    sourceDocKey: 'tb-thue',
    sourceSnippet: 'Thông báo nộp thuế đất · bản scan (chất lượng thấp): “Thửa đất số 45, tờ bản đồ 12”',
    bbox: { top: 35, left: 10, w: 60, h: 6 },
  },
  {
    key: 'map_sheet_number',
    section: 'B',
    label: 'Số tờ bản đồ',
    value: 'Tờ BĐ 12',
    confidencePct: 68,
    status: 'da_xac_thuc',
    sourceDocKey: 'tb-thue',
    sourceSnippet: 'Thông báo nộp thuế đất · bản scan (chất lượng thấp): “Thửa đất số 45, tờ bản đồ 12”',
    bbox: null,
  },
  {
    key: 'land_use_purpose',
    section: 'B',
    label: 'Mục đích sử dụng đất',
    value: 'Đất ở tại đô thị (ODT)',
    confidencePct: 90,
    status: 'da_xac_thuc',
    sourceDocKey: 'so-hong',
    sourceSnippet: 'Sổ hồng · mục Mục đích sử dụng: “Đất ở tại đô thị”',
    bbox: { top: 42, left: 50, w: 42, h: 5 },
  },
  {
    key: 'use_term',
    section: 'B',
    label: 'Thời hạn sử dụng',
    value: 'Lâu dài',
    confidencePct: 95,
    status: 'da_xac_thuc',
    sourceDocKey: 'so-hong',
    sourceSnippet: 'Sổ hồng · mục Thời hạn sử dụng: “Lâu dài”',
    bbox: { top: 50, left: 8, w: 34, h: 5 },
  },
  {
    key: 'ownership_form',
    section: 'B',
    label: 'Hình thức sở hữu',
    value: 'Sở hữu riêng',
    confidencePct: 94,
    status: 'da_xac_thuc',
    sourceDocKey: 'so-hong',
    sourceSnippet: 'Sổ hồng · mục Hình thức sử dụng: “Sử dụng riêng”',
    bbox: { top: 50, left: 46, w: 40, h: 5 },
  },
  {
    key: 'current_mortgage_status',
    section: 'B',
    label: 'Tình trạng thế chấp hiện tại',
    value: 'Chưa thế chấp tại TCTD nào',
    confidencePct: 55,
    status: 'can_xac_minh',
    sourceDocKey: 'so-hong',
    sourceSnippet:
      'Trang biến động Sổ hồng để trống — chưa đủ căn cứ khẳng định, cần tra cứu CIC/hệ thống nội bộ trước khi kết luận.',
    bbox: { top: 78, left: 8, w: 60, h: 5 },
  },

  // C. Vị trí & đặc điểm tài sản
  {
    key: 'address',
    section: 'C',
    label: 'Địa chỉ',
    value: 'Hẻm 45 Nguyễn Văn A, Phường B, Quận C',
    confidencePct: 94,
    status: 'da_xac_thuc',
    sourceDocKey: 'so-hong',
    sourceSnippet: 'Sổ hồng · Địa chỉ thửa đất: “Hẻm 45 Nguyễn Văn A, Phường B, Quận C”',
    bbox: { top: 33, left: 8, w: 80, h: 5 },
  },
  {
    key: 'property_type',
    section: 'C',
    label: 'Loại BĐS',
    value: 'Nhà phố (nhà trong hẻm)',
    confidencePct: null,
    status: 'suy_luan',
    sourceDocKey: null,
    sourceSnippet: 'Suy luận từ đặc điểm nhà + vị trí trong hẻm — không nêu trực tiếp trên tài liệu, cần thẩm định viên xác nhận.',
    bbox: null,
  },
  {
    key: 'land_area_sqm',
    section: 'C',
    label: 'Diện tích đất',
    value: '62 m²',
    confidencePct: 91,
    status: 'mau_thuan',
    sourceDocKey: 'so-hong',
    sourceSnippet:
      '2 tài liệu ghi khác nhau: Sổ hồng = 62 m², Tờ khai LPTB = 65 m². Kiểm tra chéo sơ đồ (4.2 × 14.8 = 62.2 m²) ủng hộ 62 m². Cần thẩm định viên chốt.',
    bbox: { top: 42, left: 8, w: 38, h: 5 },
  },
  {
    key: 'floor_area_sqm',
    section: 'C',
    label: 'Diện tích sàn xây dựng',
    value: '98 m² (2 tầng)',
    confidencePct: 66,
    status: 'da_xac_thuc',
    sourceDocKey: 'bien-ban',
    sourceSnippet: 'Biên bản bàn giao · “Tổng diện tích sàn ~98m²” (diễn đạt xấp xỉ).',
    bbox: { top: 30, left: 10, w: 56, h: 5 },
  },
  {
    key: 'frontage_depth',
    section: 'C',
    label: 'Kích thước mặt tiền × chiều sâu',
    value: '4.2m × 14.8m',
    confidencePct: 88,
    status: 'da_xac_thuc',
    sourceDocKey: 'so-hong',
    sourceSnippet: 'Sổ hồng · sơ đồ thửa đất: cạnh 4.2m × 14.8m',
    bbox: { top: 59, left: 55, w: 37, h: 9 },
  },
  {
    key: 'num_floors_desc',
    section: 'C',
    label: 'Số tầng',
    value: '2 tầng + sân thượng',
    confidencePct: 86,
    status: 'da_xac_thuc',
    sourceDocKey: 'so-hong',
    sourceSnippet: 'Sổ hồng · tài sản gắn liền với đất: “Nhà ở 2 tầng”',
    bbox: { top: 60, left: 8, w: 32, h: 5 },
  },
  {
    key: 'construction_year',
    section: 'C',
    label: 'Năm xây dựng',
    value: '2016',
    confidencePct: 90,
    status: 'da_xac_thuc',
    sourceDocKey: 'so-hong',
    sourceSnippet: 'Sổ hồng · năm hoàn thành xây dựng: 2016',
    bbox: { top: 68, left: 8, w: 26, h: 5 },
  },
  {
    key: 'structure_material',
    section: 'C',
    label: 'Kết cấu / vật liệu',
    value: 'Bê tông cốt thép, tường gạch',
    confidencePct: 85,
    status: 'da_xac_thuc',
    sourceDocKey: 'so-hong',
    sourceSnippet: 'Sổ hồng · kết cấu: “BTCT, tường gạch”',
    bbox: { top: 68, left: 38, w: 44, h: 5 },
  },
  {
    key: 'house_direction',
    section: 'C',
    label: 'Hướng nhà',
    value: 'Đông Nam',
    confidencePct: 60,
    status: 'can_xac_minh',
    sourceDocKey: 'bien-ban',
    sourceSnippet: 'Biên bản bàn giao · ghi chú hiện trạng: “hướng Đông Nam” (nguồn thứ cấp, nên xác minh thực địa).',
    bbox: { top: 42, left: 10, w: 40, h: 5 },
  },
  {
    key: 'road_type_desc',
    section: 'C',
    label: 'Loại đường / độ rộng hẻm',
    value: 'Hẻm bê tông, rộng 3.5m, ô tô vào được',
    confidencePct: 85,
    status: 'da_xac_thuc',
    sourceDocKey: 'bien-ban',
    sourceSnippet: 'Biên bản bàn giao · mô tả lối vào/hiện trạng khu vực.',
    bbox: { top: 54, left: 10, w: 66, h: 5 },
  },
  {
    key: 'current_usage_status',
    section: 'C',
    label: 'Tình trạng sử dụng hiện tại',
    value: 'Đang ở, không cho thuê',
    confidencePct: 85,
    status: 'da_xac_thuc',
    sourceDocKey: 'bien-ban',
    sourceSnippet: 'Biên bản bàn giao: “Bàn giao nhà đang sử dụng để ở”',
    bbox: null,
  },

  // D. Thông tin khoản vay — không có nguồn tài liệu, luôn nhập tay
  {
    key: 'loan_amount_vnd',
    section: 'D',
    label: 'Số tiền vay',
    value: '3.200.000.000 ₫',
    confidencePct: null,
    status: 'nhap_tay',
    sourceDocKey: null,
    sourceSnippet: null,
    bbox: null,
  },
  {
    key: 'loan_purpose',
    section: 'D',
    label: 'Mục đích vay',
    value: 'Thế chấp vay vốn',
    confidencePct: null,
    status: 'nhap_tay',
    sourceDocKey: null,
    sourceSnippet: null,
    bbox: null,
  },
  {
    key: 'loan_term_years',
    section: 'D',
    label: 'Thời hạn vay',
    value: '15 năm',
    confidencePct: null,
    status: 'nhap_tay',
    sourceDocKey: null,
    sourceSnippet: null,
    bbox: null,
  },
];

export const fixtureCase: AppraisalCaseFull = {
  caseId: CASE_ID,
  status: 'dang_xu_ly',

  tab1Fields,
  documents: [],
  docPages,

  marketComparables: [
    { id: 'mc-1', compAddress: 'Hẻm 40 Nguyễn Văn A', distanceKmLabel: '0.3 km', areaSqmLabel: '58 m²', transactionDateLabel: '11/2025', pricePerSqmLabel: '76.6 tr' },
    { id: 'mc-2', compAddress: 'Đường Nguyễn Văn A', distanceKmLabel: '0.6 km', areaSqmLabel: '65 m²', transactionDateLabel: '09/2025', pricePerSqmLabel: '79.2 tr' },
    { id: 'mc-3', compAddress: 'Hẻm 12 Trần Văn B', distanceKmLabel: '0.8 km', areaSqmLabel: '60 m²', transactionDateLabel: '06/2025', pricePerSqmLabel: '88.1 tr' },
    { id: 'mc-4', compAddress: 'Hẻm 45 (kế bên)', distanceKmLabel: '0.1 km', areaSqmLabel: '64 m²', transactionDateLabel: '02/2026', pricePerSqmLabel: '98.4 tr' },
    { id: 'mc-5', compAddress: 'Đường Lê Văn C', distanceKmLabel: '1.1 km', areaSqmLabel: '70 m²', transactionDateLabel: '01/2026', pricePerSqmLabel: '95.0 tr' },
  ],
  marketInferenceText:
    'Giá giao dịch so sánh dao động 76.6–98.4 triệu/m², trung vị khoảng 88 triệu/m². Xu hướng tăng nhẹ theo thời gian — giao dịch gần nhất (02/2026) cao hơn ~28% so với giao dịch xa nhất (11/2025), cho thấy khu vực đang trong đà tăng giá. Nên ưu tiên trọng số cao hơn cho các giao dịch gần đây khi đưa vào bước định giá.',

  lookupFindings: [
    {
      id: 'lc-planning',
      category: 'planning_zoning',
      toolName: 'planning_zoning_lookup',
      statusBadge: 'da_xac_thuc',
      title: 'Quy hoạch',
      rawFindings: [
        'Không nằm trong khu vực quy hoạch treo.',
        'Lộ giới hẻm dự kiến mở rộng lên 4m theo đồ án quy hoạch 1/2000 phê duyệt 2024.',
        'Không thuộc diện giải toả, thu hồi đất.',
      ],
      inferenceText:
        'Mở rộng lộ giới thường làm tăng giá trị BĐS trong 2–3 năm tới nhờ cải thiện khả năng tiếp cận. Nên đối chiếu thêm bản vẽ quy hoạch chi tiết 1/500 để loại trừ khả năng một phần diện tích nằm trong lộ giới mới.',
      sourceLabel: 'Cổng thông tin quy hoạch đô thị',
      confidencePct: 85,
    },
    {
      id: 'lc-legal',
      category: 'legal_status',
      toolName: 'legal_status_lookup',
      statusBadge: 'da_xac_thuc',
      title: 'Pháp lý',
      rawFindings: [
        'Sổ hồng đứng tên chính chủ, cấp 14/03/2019.',
        'Không ghi nhận tranh chấp, kê biên hay khiếu nại.',
        'Không đang thế chấp tại tổ chức tín dụng khác.',
      ],
      inferenceText:
        'Tình trạng pháp lý sạch, đủ điều kiện nhận thế chấp. Yếu tố tích cực, giảm đáng kể rủi ro khi xử lý tài sản bảo đảm nếu phát sinh nợ xấu.',
      sourceLabel: 'Hệ thống tra cứu sổ đỏ/sổ hồng liên thông',
      confidencePct: 95,
    },
    {
      id: 'lc-amenity',
      category: 'neighborhood_amenity',
      toolName: 'neighborhood_amenity_lookup',
      title: 'Tiện ích xung quanh',
      rawFindings: ['Trường tiểu học: 300m · Chợ dân sinh: 450m', 'Trạm xe bus: 200m · Bệnh viện quận: 1.2km'],
      inferenceText:
        'Mật độ tiện ích cao hơn trung bình khu vực (đầy đủ trường học/chợ/giao thông công cộng trong bán kính <500m) — yếu tố hỗ trợ tích cực cho nhu cầu ở thực và thanh khoản khi cần bán lại.',
      sourceLabel: 'Dữ liệu điểm tiện ích (POI) khu vực',
      confidencePct: 90,
    },
    {
      id: 'lc-environment',
      category: 'environmental_risk',
      toolName: 'environmental_risk_lookup',
      statusBadge: 'luu_y',
      title: 'Môi trường',
      rawFindings: [
        'Ghi nhận ngập nhẹ cục bộ mùa mưa 2022–2023 (mức nước <15cm, rút trong ngày).',
        'Không nằm trong vùng cảnh báo sạt lở, ô nhiễm công nghiệp.',
      ],
      inferenceText:
        'Rủi ro ngập ở mức thấp, không ảnh hưởng đáng kể đến giá trị định giá, nhưng nên khuyến nghị khách hàng mua bảo hiểm tài sản và có phương án chống ngập khi cải tạo.',
      sourceLabel: 'Dữ liệu khí tượng thuỷ văn & phản ánh cư dân',
      confidencePct: 70,
    },
    {
      id: 'lc-liquidity',
      category: 'liquidity_stat',
      toolName: 'liquidity_stat_lookup',
      title: 'Thanh khoản khu vực',
      rawFindings: ['Thời gian bán trung bình: 45 ngày · Tỷ lệ giao dịch thành công: 82%', 'Số tin rao bán cùng phân khúc trong bán kính 1km: 14 tin'],
      inferenceText:
        'Thanh khoản khá tốt so với mặt bằng chung phân khúc nhà phố hẻm (thường 60–90 ngày) — hỗ trợ tích cực cho khả năng xử lý tài sản bảo đảm khi cần thiết.',
      sourceLabel: 'Thống kê giao dịch sàn & môi giới khu vực',
      confidencePct: 80,
    },
    {
      id: 'lc-reputation',
      category: 'stigma_reputation',
      toolName: 'stigma_reputation_lookup',
      statusBadge: 'chua_xac_thuc',
      title: 'Dư luận / tâm linh',
      rawFindings: [
        'Ghi nhận tin đồn dân cư chưa xác thực liên quan 1 sự việc năm 2019.',
        'Không có bài báo, hồ sơ công an hoặc dữ liệu chính thức xác nhận.',
      ],
      inferenceText:
        'Độ tin cậy nguồn tin thấp (30%), chưa đủ cơ sở kết luận ảnh hưởng đến giá trị hay thanh khoản. Khuyến nghị thẩm định viên xác minh thực địa (hỏi hàng xóm, chính quyền địa phương) trước khi đưa vào báo cáo chính thức.',
      sourceLabel: 'Tra cứu dư luận mạng xã hội & diễn đàn khu vực',
      confidencePct: 30,
    },
  ],

  valuation: {
    proposedValueLabel: '4.85 tỷ',
    valueRangeLabel: '4.55–5.10 tỷ',
    pricePerSqmLabel: '97.0 tr',
    confidencePct: 78,
    comparableCount: 5,
    priceIndexPeriod: '2026-Q2',
    priceIndexValue: 118.3,
    priceIndexBase: 100,
  },
  priceIndexSeries: [
    { periodLabel: '2024-Q1', indexValue: 100.0 },
    { periodLabel: '2024-Q2', indexValue: 103.1 },
    { periodLabel: '2024-Q3', indexValue: 106.2 },
    { periodLabel: '2024-Q4', indexValue: 110.4 },
    { periodLabel: '2025-Q2', indexValue: 114.8 },
    { periodLabel: '2025-Q4', indexValue: 116.9 },
    { periodLabel: '2026-Q2', indexValue: 118.3 },
  ],
  valuationMethods: [
    {
      id: 'lc-method-sales',
      methodKey: 'sales_comparison',
      label: 'So sánh trực tiếp',
      estimatedValueLabel: '4.90 tỷ',
      weightPct: 50,
      contributionValueLabel: '2.45 tỷ',
      methodConfidencePct: 82,
      inputs: [
        '5 giao dịch so sánh trong bán kính 1.1km, gần nhất 02/2026.',
        'Điều chỉnh theo diện tích, hướng nhà, vị trí hẻm/mặt tiền và thời gian giao dịch (quy đổi theo chỉ số giá index 118.3).',
        'Giá/m² sau điều chỉnh: 79–98 triệu, trung vị ~86 triệu.',
      ],
      inferenceText:
        'Bám sát thực tế thị trường nhất vì dùng giao dịch thật, nhưng nhạy với chất lượng & số lượng giao dịch so sánh. Với 5 giao dịch cùng loại hình hẻm, diện tích 58–70m², độ tương đồng khá cao nên độ tin cậy phương pháp này ở mức cao.',
      sourceLabel: 'market_price_lookup (market data)'
    },
    {
      id: 'lc-method-hedonic',
      methodKey: 'hedonic_ml',
      label: 'Hedonic (ML)',
      estimatedValueLabel: '4.80 tỷ',
      weightPct: 30,
      contributionValueLabel: '1.44 tỷ',
      methodConfidencePct: 78,
      inputs: [
        'Huấn luyện trên ~2.400 giao dịch lịch sử toàn quận (2022–2026).',
        'Biến số: diện tích, số tầng, chiều rộng hẻm, hướng nhà, khoảng cách trung tâm, tuổi công trình, mật độ tiện ích.',
        'R² mô hình: 0.87 · Sai số trung bình (MAE): 4.2%.',
      ],
      inferenceText:
        'Cân bằng ảnh hưởng đồng thời của nhiều yếu tố mà so sánh trực tiếp khó xử lý cùng lúc (vd. tổ hợp hướng nhà + chiều rộng hẻm). Sai số trung bình 4.2% trên tập dữ liệu khu vực tương tự cho thấy mô hình khá ổn định.',
      sourceLabel: 'calculate_valuation — nhánh hedonic-ML'
    },
    {
      id: 'lc-method-cost',
      methodKey: 'cost_approach',
      label: 'Chi phí xây dựng',
      estimatedValueLabel: '4.75 tỷ',
      weightPct: 20,
      contributionValueLabel: '0.95 tỷ',
      methodConfidencePct: 70,
      inputs: [
        'Giá đất tham chiếu khu vực: ~68 triệu/m² (đã loại trừ phần công trình).',
        'Đơn giá xây dựng: 7.5 triệu/m² (nhà 3 tầng, kết cấu BTCT), diện tích sàn 124m².',
        'Khấu hao theo tuổi công trình: 12 năm, khấu hao 18%.',
      ],
      inferenceText:
        'Cho giá trị thấp nhất trong 3 phương pháp vì chưa phản ánh đầy đủ yếu tố vị trí/tiềm năng tăng giá — phù hợp dùng làm giá sàn tham chiếu, hạn chế định giá vượt quá xa chi phí thay thế thực tế.',
      sourceLabel: 'calculate_valuation — nhánh chi phí xây dựng'
    },
  ],
  valuationWeightedInferenceText:
    'Trọng số ưu tiên <b>So sánh trực tiếp (50%)</b> vì khu vực có đủ giao dịch gần đây và tương đồng cao với tài sản; <b>Hedonic/ML (30%)</b> giúp hiệu chỉnh đồng thời nhiều biến số; <b>Chi phí xây dựng (20%)</b> chỉ dùng làm giá sàn tham chiếu vì ít phản ánh yếu tố vị trí. Chênh lệch giữa giá trị cao nhất và thấp nhất trong 3 phương pháp chỉ <b>3.1%</b> (4.90 so với 4.75 tỷ) — mức đồng thuận cao giữa các phương pháp, củng cố cho độ tin cậy tổng 78%.',

  confidenceFactors: [
    { factorKey: 'comp_quantity_quality', label: 'Giao dịch so sánh (SL & chất lượng)', weightPct: 30, score: 85 },
    { factorKey: 'method_consensus', label: 'Đồng thuận giữa 3 phương pháp', weightPct: 25, score: 80 },
    { factorKey: 'legal_planning_completeness', label: 'Pháp lý & quy hoạch đầy đủ', weightPct: 20, score: 88 },
    { factorKey: 'market_volatility', label: 'Biến động thị trường gần đây', weightPct: 15, score: 54 },
    { factorKey: 'comp_similarity', label: 'Tương đồng giao dịch so sánh', weightPct: 10, score: 65 },
  ],
  confidenceInferenceText:
    'Hai yếu tố đang kéo độ tin cậy tổng xuống 78% thay vì cao hơn: <b>biến động thị trường gần đây</b> (chỉ số giá tăng ~5%/quý, nhanh hơn trung bình dài hạn của khu vực) và <b>độ tương đồng giao dịch so sánh</b> (một số giao dịch chênh lệch diện tích &gt;15% so với tài sản thẩm định). Ba yếu tố còn lại (số lượng giao dịch, mức đồng thuận giữa các phương pháp, dữ liệu pháp lý/quy hoạch) đều ở mức tốt. Khuyến nghị bổ sung giao dịch so sánh mới nhất nếu cần nâng độ tin cậy trước khi ra quyết định cho vay.',

  risk: { riskScore: 34, riskLabel: 'trung_binh', ltvProposedPct: 65 },
  ltvPolicyBands: [
    { minScore: 0, maxScore: 20, maxLtvPct: 75, label: '0–20 điểm → tối đa 75%' },
    { minScore: 21, maxScore: 40, maxLtvPct: 65, label: '21–40 điểm → tối đa 65%' },
    { minScore: 41, maxScore: 60, maxLtvPct: 55, label: '41–60 điểm → tối đa 55%' },
    { minScore: 61, maxScore: null, maxLtvPct: 45, label: '>60 điểm → tối đa 45% hoặc cần thẩm định lại' },
  ],
  ltvPolicyInferenceText:
    'Điểm rủi ro tài sản 34/100 rơi vào khung 21–40, nên LTV đề xuất 65%.',
  riskGroups: [
    {
      id: 'rc-legal',
      groupKey: 'legal',
      label: 'Pháp lý',
      weightPct: 30,
      score: 15,
      rawFindings: [
        'Sổ hồng chính chủ, cấp 14/03/2019, không tranh chấp/kê biên.',
        'Không đang thế chấp tại tổ chức tín dụng khác.',
        'Không thuộc diện giải toả, thu hồi đất.',
      ],
      inferenceText:
        'Nhóm rủi ro thấp nhất trong 5 nhóm nhờ hồ sơ pháp lý sạch, đã xác thực qua hệ thống liên thông sổ đỏ/sổ hồng — đóng góp tích cực lớn nhất giúp kéo điểm rủi ro tổng xuống mức Trung bình.',
      sourceLabel: 'legal_status_lookup',
      toolName: 'legal_status_lookup',
    },
    {
      id: 'rc-liquidity',
      groupKey: 'liquidity',
      label: 'Thanh khoản',
      weightPct: 25,
      score: 30,
      rawFindings: [
        'Thời gian bán trung bình khu vực: 45 ngày · Tỷ lệ giao dịch thành công: 82%.',
        'Số tin rao bán cùng phân khúc trong bán kính 1km: 14 tin.',
      ],
      inferenceText:
        'Thanh khoản khá tốt so với mặt bằng chung phân khúc nhà phố hẻm (thường 60–90 ngày) nên điểm rủi ro ở mức thấp-trung bình — hỗ trợ khả năng xử lý tài sản bảo đảm khi cần thiết.',
      sourceLabel: 'liquidity_stat_lookup',
      toolName: 'liquidity_stat_lookup',
    },
    {
      id: 'rc-volatility',
      groupKey: 'price_volatility',
      label: 'Biến động giá',
      weightPct: 20,
      score: 55,
      rawFindings: [
        'Chỉ số giá khu vực tăng từ 100.0 (2024-Q1) lên 118.3 (2026-Q2), tương đương ~5%/quý.',
        'Biên độ giá giao dịch so sánh dao động rộng: 76.6–98.4 triệu/m² (chênh lệch 28%).',
      ],
      inferenceText:
        'Tốc độ tăng giá nhanh hơn trung bình dài hạn và biên độ giao dịch rộng cho thấy thị trường khu vực đang biến động khá mạnh — nhóm có điểm cao thứ 2. Nếu thị trường điều chỉnh giảm, giá trị tài sản bảo đảm có thể biến động theo.',
      sourceLabel: 'market_price_lookup',
      toolName: 'market_price_lookup',
    },
    {
      id: 'rc-environment',
      groupKey: 'physical_environment',
      label: 'Vật lý/môi trường',
      weightPct: 15,
      score: 30,
      rawFindings: [
        'Ghi nhận ngập nhẹ cục bộ mùa mưa 2022–2023 (<15cm, rút trong ngày).',
        'Không nằm trong vùng cảnh báo sạt lở, ô nhiễm công nghiệp.',
        'Công trình xây dựng 2016, kết cấu BTCT, chưa ghi nhận xuống cấp.',
      ],
      inferenceText:
        'Rủi ro ở mức thấp-trung bình, chủ yếu do tình trạng ngập nhẹ cục bộ — không ảnh hưởng đáng kể đến kết cấu công trình. Khuyến nghị khách hàng mua bảo hiểm tài sản.',
      sourceLabel: 'environmental_risk_lookup',
      toolName: 'environmental_risk_lookup',
    },
    {
      id: 'rc-reputation',
      groupKey: 'reputation',
      label: 'Danh tiếng/tâm linh',
      weightPct: 10,
      score: 60,
      rawFindings: [
        'Tin đồn dân cư chưa xác thực liên quan 1 sự việc năm 2019.',
        'Không có bài báo, hồ sơ công an hoặc dữ liệu chính thức xác nhận.',
        'Độ tin cậy nguồn tin: chỉ 30% (chưa kiểm chứng).',
      ],
      inferenceText:
        'Điểm rủi ro cao nhất trong 5 nhóm (60/100) nhưng dựa trên nguồn tin có độ tin cậy thấp — chưa đủ cơ sở kết luận. Trọng số nhóm này chỉ 10% nên ảnh hưởng lên điểm tổng bị giới hạn. Cần xác minh thực địa trước khi đưa vào báo cáo chính thức.',
      sourceLabel: 'stigma_reputation_lookup',
      toolName: 'stigma_reputation_lookup',
    },
  ],
  riskWeightedInferenceText:
    '<b>Biến động giá</b> (20%) và <b>danh tiếng/tâm linh</b> (10%) là 2 nhóm có điểm cao nhất (55 và 60), nhưng danh tiếng/tâm linh chỉ chiếm trọng số nhỏ nên ảnh hưởng lên điểm tổng bị giới hạn. Ngược lại, <b>pháp lý</b> (30% — trọng số lớn nhất) có điểm rất thấp (15), là yếu tố kéo điểm rủi ro tổng xuống mức Trung bình thay vì cao hơn.',

  riskFlags: [
    {
      id: 'legal',
      severity: 'thap',
      title: 'Pháp lý',
      description: 'Sổ hồng hợp lệ, không tranh chấp ghi nhận.',
      confidencePct: 95,
      verifiedStatus: 'da_xac_thuc',
    },
    {
      id: 'reputation',
      severity: 'trung_binh',
      title: 'Danh tiếng / tâm linh',
      description: 'Tin đồn dân cư chưa xác thực về sự việc 2019 — <b>cần xác minh thực địa</b>.',
      confidencePct: 35,
      verifiedStatus: 'chua_xac_thuc',
    },
    {
      id: 'environment',
      severity: 'thap',
      title: 'Môi trường',
      description: 'Khu vực từng ngập nhẹ 2022–2023 — khuyến nghị mua bảo hiểm tài sản.',
      confidencePct: 70,
      verifiedStatus: 'da_xac_thuc',
    },
  ],

  dashboardSteps: [
    { stepNumber: 1, title: 'Nhập thông tin', summaryText: 'Hẻm 45 Nguyễn Văn A, Phường B, Quận C · 62 m² · Sổ hồng chính chủ.' },
    { stepNumber: 2, title: 'Kết quả tra cứu', summaryText: '7 nguồn tra cứu hoàn tất · 1 điểm cần lưu ý (dư luận khu vực, chưa xác thực).' },
    { stepNumber: 3, title: 'Định giá', summaryText: '4.85 tỷ (4.55–5.10 tỷ) · độ tin cậy 78%, kết hợp 3 phương pháp.' },
    { stepNumber: 4, title: 'Rủi ro', summaryText: 'Điểm rủi ro tài sản 34/100 (Trung bình) · LTV đề xuất 65%.' },
  ],

  agentTrace: [
    { id: 'te-1', secondsOffsetLabel: 't+0.0s', actor: 'System', title: 'Hệ thống tiếp nhận yêu cầu', description: 'Từ hệ thống điều phối hồ sơ.' },
    { id: 'te-2', secondsOffsetLabel: 't+0.1–1.2s', actor: 'Market data', title: '7 nguồn tra cứu chạy song song', description: 'Giá thị trường, quy hoạch, pháp lý, tiện ích, dư luận, môi trường, thanh khoản...' },
    { id: 'te-3', secondsOffsetLabel: 't+1.4s', actor: 'Valuation', title: 'Định giá hoàn tất', description: 'Giá trị ước tính: 4.85 tỷ' },
    { id: 'te-4', secondsOffsetLabel: 't+1.6s', actor: 'Risk', title: 'Chấm điểm rủi ro hoàn tất', description: 'Điểm rủi ro tài sản: 34/100 · Trung bình' },
    { id: 'te-5', secondsOffsetLabel: 't+2.3s', actor: 'Summary', title: 'Tổng hợp báo cáo', description: 'Sẵn sàng để thẩm định viên xuất báo cáo và ký xác nhận' },
  ],
};
