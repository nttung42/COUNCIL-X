import { WorkflowAgentPage, type WorkflowPageConfig } from '../sharedWorkflow';

const config: WorkflowPageConfig = {
  agentTitle: 'Intake — Số hoá hồ sơ',
  agentSubtitle: 'Cty TNHH ABC · Trần Văn B (GĐ)',
  agentIcon: 'IN',
  welcomeTitle: 'Tiếp nhận hồ sơ hoàn tất',
  welcomeText: '5/7 tài liệu đã xử lý. Còn 1 blocker và 2 warning cần xử lý trước khi hồ sơ sẵn sàng.',
  chips: ['Soạn email bổ sung', 'Giải thích chênh lệch doanh thu', 'Xem checklist thiếu', 'Cách phân loại tài liệu'],
  banner: 'Hoàn tất tiếp nhận hồ sơ — phát hiện 3 vấn đề cần xử lý trước bước sàng lọc.',
  loadingText: 'OCR, phân loại tài liệu, đối chiếu checklist và dữ liệu chéo.',
  progress: ['ĐKKD.pdf classified', 'BCTC_2024.xlsx extracted', 'Sổ đỏ TSBĐ OCR completed', 'Checklist validated', 'Cross-source validation completed'],
  summaryTitle: 'Mức độ sẵn sàng hồ sơ',
  metrics: [
    { label: 'Tài liệu đã nhận', value: '5/7', sub: 'Còn thiếu 2 tài liệu' },
    { label: 'Blocker', value: '1', sub: 'Cần xử lý trước khi chuyển bước', tone: 'var(--danger)' },
    { label: 'Warning', value: '2', sub: 'Cần RM rà soát', tone: 'var(--warning)' },
    { label: 'Lỗi OCR', value: '0', sub: 'Không phát hiện lỗi OCR', tone: 'var(--success)' },
  ],
  table: {
    title: 'Required documents',
    columns: ['Document', 'Status', 'Source', 'Owner'],
    rows: [
      ['ĐKKD.pdf', 'Received', 'Upload', 'RM'],
      ['BCTC_2024.xlsx', 'Received', 'Upload', 'RM'],
      ['Sổ đỏ TSBĐ', 'Received', 'OCR', 'Appraiser'],
      ['Hợp đồng tín dụng dự thảo', 'Received', 'Upload', 'RM'],
      ['Biên bản họp HĐTV', 'Missing', 'Checklist', 'Customer'],
      ['Báo cáo dòng tiền', 'Missing', 'Checklist', 'Customer'],
    ],
  },
  cards: [
    {
      tone: 'critical',
      title: 'Thiếu Biên bản họp HĐTV',
      description: 'Tài liệu bắt buộc cho khoản vay doanh nghiệp vượt ngưỡng phê duyệt thông thường.',
      evidence: 'Checklist khoản vay doanh nghiệp · nhóm tài liệu pháp lý nội bộ',
      rule: 'Facility vượt ngưỡng phê duyệt thông thường cần Biên bản họp HĐTV.',
      action: 'Yêu cầu khách hàng bổ sung qua RM Nguyễn Văn A.',
      confidence: 'High · matched by product type and facility amount',
      meta: 'Owner: Khách hàng qua RM Nguyễn Văn A',
    },
    {
      tone: 'warning',
      title: 'Chênh lệch doanh thu',
      description: 'Doanh thu BCTC 2024 là 12.3 tỷ, tờ khai thuế Q4 ước tính 9.1 tỷ; chênh lệch 26%.',
      evidence: 'BCTC_2024.xlsx / P&L; VAT_Q4_2024.pdf / tax return',
      rule: 'Flag nếu chênh lệch doanh thu > 15%.',
      action: 'Yêu cầu giải trình trước thẩm định tài chính.',
      confidence: 'High · company name and tax ID matched',
      meta: 'Cần giải trình trước thẩm định tài chính',
    },
    {
      tone: 'good',
      title: 'Tên doanh nghiệp khớp',
      description: 'Tên pháp nhân khớp tuyệt đối giữa ĐKKD, BCTC và hợp đồng hiện có.',
      evidence: 'ĐKKD.pdf; BCTC_2024.xlsx; Hợp đồng tín dụng dự thảo',
      rule: 'Tên pháp nhân phải khớp tuyệt đối trên tài liệu chính.',
      action: 'Không cần xử lý thêm.',
      confidence: 'High · exact text match',
    },
  ],
  footerHint: 'Rà soát blocker/warning, gửi yêu cầu bổ sung nếu cần.',
  secondaryLabel: 'Gửi yêu cầu bổ sung',
  primaryLabel: 'Chuyển sàng lọc',
  blocker: 'Còn 1 blocker — thiếu Biên bản họp HĐTV',
  nextRoute: 'eligibilityScreening',
};

export function CaseIntakePage({ params }: { params: Record<string, string> }) {
  return <WorkflowAgentPage config={config} caseId={params.caseId} />;
}
