import { WorkflowAgentPage, type WorkflowPageConfig } from '../sharedWorkflow';

const config: WorkflowPageConfig = {
  agentTitle: 'Approval — Tóm tắt trình duyệt',
  agentSubtitle: 'Cty TNHH ABC · REQ-2026-00458',
  agentIcon: 'AP',
  welcomeTitle: 'Tóm tắt phê duyệt sẵn sàng',
  welcomeText: 'Hồ sơ đã qua phản biện Underwriting. Có 1 critical về LTV và 2 điều kiện cần ghi nhận trước giải ngân.',
  chips: ['Giải thích LTV vượt ngưỡng 80%', 'Điểm tín dụng 64/100 nghĩa là gì?', 'Xem điều kiện phê duyệt đề xuất', 'Vì sao đề xuất hạ vay xuống 3.5 tỷ?'],
  banner: 'Tóm tắt phê duyệt — trình Hội đồng tín dụng với điều kiện kiểm soát rủi ro.',
  loadingText: 'Soạn tóm tắt phê duyệt và tính toán ma trận thẩm quyền.',
  progress: ['Credit memo consolidated', 'LTV threshold checked', 'Credit score calculated', 'Approval conditions drafted'],
  summaryTitle: 'Đề xuất phê duyệt có điều kiện',
  metrics: [
    { label: 'Khoản vay đề nghị', value: '5 tỷ', sub: '24 tháng · VLĐ' },
    { label: 'Định giá TSBĐ', value: '4.85 tỷ', sub: 'PAA đề xuất' },
    { label: 'LTV', value: '103%', sub: 'Vượt ngưỡng 80%', tone: 'var(--danger)' },
    { label: 'Điểm tín dụng', value: '64/100', sub: 'Rủi ro trung bình', tone: 'var(--warning)' },
  ],
  cards: [
    {
      tone: 'critical',
      title: 'LTV vượt chính sách',
      description: 'Khoản vay 5 tỷ trên tài sản 4.85 tỷ tạo LTV 103%, vượt ngưỡng chính sách 80%.',
      evidence: 'Loan proposal 5 tỷ; collateral valuation 4.85 tỷ',
      rule: 'Critical nếu LTV > 80% với sản phẩm này.',
      action: 'Hạ hạn mức hoặc yêu cầu bổ sung tài sản bảo đảm.',
      confidence: 'High · formula inputs complete',
    },
    {
      tone: 'warning',
      title: 'Đề xuất hạ hạn mức',
      description: 'Hạ hạn mức vay xuống 3.5 tỷ để đưa LTV về khoảng 72%, hoặc yêu cầu bổ sung tài sản bảo đảm.',
      evidence: 'LTV recalculation: 3.5 / 4.85 = 72%',
      rule: 'Target LTV must stay within 80% policy cap.',
      action: 'Trình phương án hạn mức 3.5 tỷ trong memo.',
      confidence: 'High · deterministic calculation',
    },
    {
      tone: 'warning',
      title: 'Điều kiện trước giải ngân',
      description: 'Giải trình doanh thu, xử lý điều lệ và hoàn tất kiểm tra thực địa bất động sản.',
      evidence: 'Underwriting conditions; Legal review; Financial review; Collateral review',
      rule: 'All open conditions must be closed before disbursement.',
      action: 'Gắn checklist điều kiện cho Credit Support.',
      confidence: 'High · inherited open conditions',
    },
  ],
  footerHint: 'Hội đồng có thể phê duyệt có điều kiện hoặc yêu cầu điều chỉnh hạn mức.',
  secondaryLabel: 'Từ chối',
  primaryLabel: 'Phê duyệt có điều kiện',
  nextRoute: 'loanDisbursement',
};

export function CreditApprovalPage({ params }: { params: Record<string, string> }) {
  return <WorkflowAgentPage config={config} caseId={params.caseId} />;
}
