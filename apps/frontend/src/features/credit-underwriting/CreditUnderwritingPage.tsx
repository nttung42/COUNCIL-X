import { WorkflowAgentPage, type WorkflowPageConfig } from '../sharedWorkflow';

const config: WorkflowPageConfig = {
  agentTitle: 'Underwriter Agent — Phản biện độc lập',
  agentSubtitle: 'Cty TNHH ABC · REQ-2026-00458',
  agentIcon: '🔎',
  welcomeTitle: 'Tôi đã tổng hợp kết quả từ 3 agent thẩm định',
  welcomeText: 'Tài chính, pháp lý và định giá tài sản bảo đảm đã hoàn tất. Tôi phát hiện 3 điểm cần Underwriter phản biện trước khi chuyển phê duyệt.',
  chips: ['Vì sao điều lệ giới hạn vay là vấn đề?', 'Chênh lệch doanh thu BCTC ↔ thuế 25% là sao?', 'Vì sao cần thực địa lại TSBĐ?', 'DSCR 1.42x có đủ an toàn không?'],
  banner: 'Phản biện độc lập — tổng hợp từ tài chính, pháp lý, định giá tài sản bảo đảm và gate.',
  loadingText: 'Đang tổng hợp kết quả thẩm định lớp maker và tạo điểm cần phản biện.',
  progress: ['Legal Agent', 'Financial Agent', 'PAA — Tài sản bảo đảm', 'Gate — CIC/AML', 'Tổng hợp phản biện'],
  summaryTitle: 'Tóm tắt rủi ro AI tổng hợp',
  cards: [
    { tone: 'critical', title: 'Pháp lý', description: 'Điều lệ công ty giới hạn hạn mức vay tối đa 4 tỷ, thấp hơn khoản đề nghị 5 tỷ.', meta: 'Nguồn: Legal Agent' },
    { tone: 'warning', title: 'Tài chính', description: 'Chênh lệch doanh thu giữa BCTC nội bộ và tờ khai thuế lên tới 25%.', meta: 'Nguồn: Financial Agent' },
    { tone: 'warning', title: 'Tài sản bảo đảm', description: 'Khu vực tài sản có lịch sử ngập cục bộ; cần xác minh thực địa trước khi chốt định giá.', meta: 'Nguồn: PAA' },
    { tone: 'good', title: 'CIC / AML', description: 'Không phát hiện nợ xấu hay rủi ro chế tài.' },
  ],
  footerHint: 'Thông qua có điều kiện: giải trình doanh thu, xử lý điều lệ, thực địa lại tài sản bảo đảm.',
  secondaryLabel: 'Trả lại Maker',
  primaryLabel: 'Thông qua — chuyển phê duyệt',
  nextRoute: 'creditApproval',
};

export function CreditUnderwritingPage({ params }: { params: Record<string, string> }) {
  return <WorkflowAgentPage config={config} caseId={params.caseId} />;
}
