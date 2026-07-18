import { WorkflowAgentPage, type WorkflowPageConfig } from '../sharedWorkflow';

const config: WorkflowPageConfig = {
  agentTitle: 'Legal Agent — Thẩm định pháp lý',
  agentSubtitle: 'Cty TNHH ABC · Trần Văn B (GĐ)',
  agentIcon: '⚖️',
  welcomeTitle: 'Legal Agent đã kiểm tra 6 mục pháp lý',
  welcomeText: 'Tôi đã tự động tích checklist pháp lý doanh nghiệp. Có 1 điểm cần xử lý: khoản vay 5 tỷ vượt hạn mức được phê duyệt trong điều lệ công ty.',
  chips: ['Vì sao vi phạm điều lệ công ty?', 'Cách xử lý vi phạm điều lệ thế nào?', 'ĐKKD còn hiệu lực đến khi nào?', 'Biên bản họp HĐTV có hợp lệ không?'],
  banner: 'Đã tích tự động 6/6 mục pháp lý — 1 mục cần xử lý trước khi xác nhận.',
  loadingText: 'Đang kiểm tra pháp nhân, điều lệ và thẩm quyền ký kết.',
  progress: ['Pháp nhân', 'Ngành nghề', 'Người ký', 'Biên bản HĐTV', 'Hạn mức điều lệ', 'CCCD'],
  summaryTitle: 'Checklist pháp lý doanh nghiệp',
  cards: [
    { tone: 'good', title: 'Pháp nhân còn hiệu lực', description: 'ĐKKD còn hạn đến 2030, không ghi nhận thay đổi bất thường.' },
    { tone: 'good', title: 'Người ký hợp lệ', description: 'Trần Văn B là Giám đốc, đúng người đại diện theo pháp luật trên ĐKKD.' },
    { tone: 'warning', title: 'Khoản vay vượt hạn mức điều lệ', description: 'Điều lệ công ty quy định hạn mức vay tối đa 4 tỷ, khoản vay đề nghị 5 tỷ.', meta: 'Cần biên bản họp bất thường hoặc sửa đổi điều lệ' },
  ],
  footerHint: 'Cần bổ sung xử lý điều lệ trước giải ngân; có thể chuyển phản biện với điều kiện.',
  secondaryLabel: 'Yêu cầu KH bổ sung',
  primaryLabel: 'Xác nhận & chuyển phản biện',
  nextRoute: 'creditUnderwriting',
};

export function LegalReviewPage({ params }: { params: Record<string, string> }) {
  return <WorkflowAgentPage config={config} caseId={params.caseId} />;
}
