import { WorkflowAgentPage, type WorkflowPageConfig } from '../sharedWorkflow';

const config: WorkflowPageConfig = {
  agentTitle: 'Underwriting — Phản biện độc lập',
  agentSubtitle: 'Cty TNHH ABC · REQ-2026-00458',
  agentIcon: 'UW',
  welcomeTitle: 'Hồ sơ sẵn sàng phản biện',
  welcomeText: 'Tài chính, pháp lý, tài sản bảo đảm và gate đã hoàn tất. Có 3 điểm cần phản biện trước khi chuyển phê duyệt.',
  chips: ['Giải thích giới hạn điều lệ', 'Giải thích chênh lệch doanh thu', 'Vì sao cần thực địa lại TSBĐ?', 'DSCR 1.42x có đủ an toàn không?'],
  banner: 'Phản biện độc lập — tổng hợp từ tài chính, pháp lý, tài sản bảo đảm và gate.',
  loadingText: 'Tổng hợp kết quả thẩm định maker và tạo điểm cần phản biện.',
  progress: ['Legal findings consolidated', 'Financial findings consolidated', 'Collateral appraisal consolidated', 'Gate checks consolidated', 'Underwriting conditions drafted'],
  summaryTitle: 'Tóm tắt rủi ro tổng hợp',
  cards: [
    {
      tone: 'critical',
      title: 'Pháp lý',
      description: 'Điều lệ công ty giới hạn hạn mức vay tối đa 4 tỷ, thấp hơn khoản đề nghị 5 tỷ.',
      evidence: 'Legal review / charter clause; loan proposal 5 tỷ',
      rule: 'Critical nếu hạn mức đề nghị vượt thẩm quyền pháp lý hiện có.',
      action: 'Yêu cầu biên bản HĐTV hoặc sửa đổi điều lệ trước giải ngân.',
      confidence: 'Medium · legal document version pending',
      meta: 'Nguồn: Legal review',
    },
    {
      tone: 'warning',
      title: 'Tài chính',
      description: 'Chênh lệch doanh thu giữa BCTC nội bộ và tờ khai thuế lên tới 25%.',
      evidence: 'Financial review / BCTC_2024.xlsx; VAT_Q4_2024.pdf',
      rule: 'Warn nếu revenue variance > 15%.',
      action: 'Yêu cầu giải trình trước khi trình phê duyệt.',
      confidence: 'High · source match inherited',
      meta: 'Nguồn: Financial review',
    },
    {
      tone: 'warning',
      title: 'Tài sản bảo đảm',
      description: 'Khu vực tài sản có lịch sử ngập cục bộ; cần xác minh thực địa trước khi chốt định giá.',
      evidence: 'PAA appraisal / environment risk; local flood history',
      rule: 'Require field check if environment risk affects collateral liquidity.',
      action: 'Bổ sung biên bản thực địa trước phê duyệt cuối.',
      confidence: 'Medium · field confirmation pending',
      meta: 'Nguồn: Collateral appraisal',
    },
    {
      tone: 'good',
      title: 'CIC / AML',
      description: 'Không phát hiện nợ xấu hay rủi ro chế tài.',
      evidence: 'Gate review / CIC and sanction screening',
      rule: 'Pass if no bad debt and no sanction match.',
      action: 'Không cần xử lý thêm.',
      confidence: 'High · direct lookup',
    },
  ],
  footerHint: 'Thông qua có điều kiện: giải trình doanh thu, xử lý điều lệ, thực địa lại tài sản bảo đảm.',
  secondaryLabel: 'Trả lại Maker',
  primaryLabel: 'Thông qua — chuyển phê duyệt',
  nextRoute: 'creditApproval',
};

export function CreditUnderwritingPage({ params }: { params: Record<string, string> }) {
  return <WorkflowAgentPage config={config} caseId={params.caseId} />;
}
