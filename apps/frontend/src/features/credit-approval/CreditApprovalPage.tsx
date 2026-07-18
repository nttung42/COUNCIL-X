import { WorkflowAgentPage, type WorkflowPageConfig } from '../sharedWorkflow';

const config: WorkflowPageConfig = {
  agentTitle: 'Approval Agent — Tóm tắt trình duyệt',
  agentSubtitle: 'Cty TNHH ABC · REQ-2026-00458',
  agentIcon: '✅',
  welcomeTitle: 'Tôi đã soạn tóm tắt phê duyệt 1 trang',
  welcomeText: 'Hồ sơ đã qua phản biện Underwriter. Có 1 điểm cần lưu ý: LTV vượt ngưỡng 80% chính sách.',
  chips: ['Vì sao LTV vượt ngưỡng 80%?', 'Điểm tín dụng 64/100 nghĩa là gì?', 'Giải thích các điều kiện phê duyệt đề xuất', 'Vì sao đề xuất hạ vay xuống 3.5 tỷ?'],
  banner: 'Tóm tắt phê duyệt — trình Hội đồng tín dụng.',
  loadingText: 'Đang soạn tóm tắt phê duyệt và tính toán ma trận thẩm quyền.',
  progress: ['Tổng hợp hồ sơ trình HĐTD', 'Tính LTV & đối chiếu ngưỡng', 'Chấm điểm tín dụng & rủi ro', 'Sinh đề xuất điều kiện'],
  summaryTitle: 'Đề xuất phê duyệt có điều kiện',
  metrics: [
    { label: 'Khoản vay đề nghị', value: '5 tỷ', sub: '24 tháng · VLĐ' },
    { label: 'Định giá TSBĐ', value: '4.85 tỷ', sub: 'PAA đề xuất' },
    { label: 'LTV', value: '103%', sub: 'Vượt ngưỡng 80%', tone: 'var(--critical)' },
    { label: 'Điểm tín dụng', value: '64/100', sub: 'Rủi ro trung bình', tone: '#8a6100' },
  ],
  cards: [
    { tone: 'critical', title: 'LTV vượt chính sách', description: 'Khoản vay 5 tỷ trên tài sản 4.85 tỷ tạo LTV 103%, vượt ngưỡng chính sách 80%.' },
    { tone: 'warning', title: 'Đề xuất hạ hạn mức', description: 'Hạ hạn mức vay xuống 3.5 tỷ để đưa LTV về khoảng 72%, hoặc yêu cầu bổ sung tài sản bảo đảm.' },
    { tone: 'warning', title: 'Điều kiện trước giải ngân', description: 'Giải trình doanh thu, xử lý điều lệ và hoàn tất kiểm tra thực địa bất động sản.' },
  ],
  footerHint: 'Hội đồng có thể phê duyệt có điều kiện hoặc yêu cầu điều chỉnh hạn mức.',
  secondaryLabel: 'Từ chối',
  primaryLabel: 'Phê duyệt có điều kiện',
  nextRoute: 'loanDisbursement',
};

export function CreditApprovalPage({ params }: { params: Record<string, string> }) {
  return <WorkflowAgentPage config={config} caseId={params.caseId} />;
}
