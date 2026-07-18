import { WorkflowAgentPage, type WorkflowPageConfig } from '../sharedWorkflow';

const config: WorkflowPageConfig = {
  agentTitle: 'Intake Agent — Số hoá hồ sơ',
  agentSubtitle: 'Cty TNHH ABC · Trần Văn B (GĐ)',
  agentIcon: '📥',
  welcomeTitle: 'Intake Agent đã xử lý 5 tài liệu',
  welcomeText: 'Tôi đã OCR, phân loại theo 4 trụ cột và trích xuất dữ liệu có cấu trúc. Còn 1 blocker và 2 warning cần xử lý trước khi hồ sơ sẵn sàng.',
  chips: ['Còn thiếu những tài liệu gì?', 'Vì sao doanh thu BCTC khác tờ khai thuế?', 'AI phân loại tài liệu theo tiêu chí nào?', 'Soạn giúp email yêu cầu bổ sung'],
  banner: 'Intake & số hoá hồ sơ — AI tự trích xuất dữ liệu và phát hiện vấn đề cần xử lý.',
  loadingText: 'Đang OCR, phân loại tài liệu, đối chiếu checklist và dữ liệu chéo.',
  progress: ['OCR & phân loại ĐKKD.pdf', 'OCR & trích xuất BCTC_2024.xlsx', 'OCR ảnh Sổ đỏ TSBĐ', 'Đối chiếu checklist hồ sơ', 'Đối chiếu chéo dữ liệu'],
  summaryTitle: 'Mức độ sẵn sàng hồ sơ',
  metrics: [
    { label: 'Tài liệu đã nhận', value: '5/7', sub: 'Còn thiếu 2 tài liệu' },
    { label: 'Blocker', value: '1', sub: 'Cần xử lý trước khi chuyển bước', tone: 'var(--critical)' },
    { label: 'Warning', value: '2', sub: 'Cần RM rà soát', tone: '#8a6100' },
    { label: 'Lỗi OCR', value: '0', sub: 'Không phát hiện lỗi OCR', tone: 'var(--good)' },
  ],
  cards: [
    { tone: 'critical', title: 'Thiếu Biên bản họp HĐTV', description: 'Tài liệu bắt buộc cho khoản vay doanh nghiệp vượt ngưỡng phê duyệt thông thường.', meta: 'Chủ xử lý: Khách hàng qua RM Nguyễn Văn A' },
    { tone: 'warning', title: 'Chênh lệch doanh thu', description: 'Doanh thu BCTC 2024 là 12.3 tỷ, tờ khai thuế Q4 ước tính 9.1 tỷ; chênh lệch 26%.', meta: 'Cần giải trình trước thẩm định tài chính' },
    { tone: 'good', title: 'Tên doanh nghiệp khớp', description: 'Tên pháp nhân khớp tuyệt đối giữa ĐKKD, BCTC và hợp đồng hiện có.' },
  ],
  footerHint: 'Rà soát blocker/warning, gửi yêu cầu bổ sung nếu cần, rồi chuyển sang sàng lọc điều kiện.',
  secondaryLabel: 'Gửi yêu cầu bổ sung',
  primaryLabel: 'Chuyển sàng lọc',
  nextRoute: 'eligibilityScreening',
};

export function CaseIntakePage({ params }: { params: Record<string, string> }) {
  return <WorkflowAgentPage config={config} caseId={params.caseId} />;
}
