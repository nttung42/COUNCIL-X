import { WorkflowAgentPage, type WorkflowPageConfig } from '../sharedWorkflow';

const config: WorkflowPageConfig = {
  agentTitle: 'Legal — Thẩm định pháp lý',
  agentSubtitle: 'Cty TNHH ABC · Trần Văn B (GĐ)',
  agentIcon: 'LG',
  welcomeTitle: 'Rà soát pháp lý hoàn tất',
  welcomeText: '6 mục pháp lý đã được kiểm tra. Có 1 warning về hạn mức vay trong điều lệ cần xử lý trước giải ngân.',
  chips: ['Giải thích giới hạn điều lệ', 'Cách xử lý vi phạm điều lệ', 'Kiểm tra hiệu lực ĐKKD', 'Xem yêu cầu Biên bản HĐTV'],
  banner: 'Hoàn tất checklist pháp lý — 1 điều kiện cần xử lý trước giải ngân.',
  loadingText: 'Kiểm tra pháp nhân, điều lệ và thẩm quyền ký kết.',
  progress: ['Legal entity checked', 'Business line checked', 'Signer authority checked', 'HĐTV minutes checked', 'Charter limit checked', 'Representative ID checked'],
  summaryTitle: 'Checklist pháp lý doanh nghiệp',
  cards: [
    {
      tone: 'good',
      title: 'Pháp nhân còn hiệu lực',
      description: 'ĐKKD còn hạn đến 2030, không ghi nhận thay đổi bất thường.',
      evidence: 'ĐKKD.pdf; business registry snapshot',
      rule: 'Pass nếu pháp nhân còn hoạt động và ngành nghề phù hợp mục đích vay.',
      action: 'Không cần xử lý thêm.',
      confidence: 'High · registry and document match',
    },
    {
      tone: 'good',
      title: 'Người ký hợp lệ',
      description: 'Trần Văn B là Giám đốc, đúng người đại diện theo pháp luật trên ĐKKD.',
      evidence: 'ĐKKD.pdf / legal representative; CCCD / representative identity',
      rule: 'Signer must be legal representative or have valid authorization.',
      action: 'Tiếp tục phản biện tín dụng.',
      confidence: 'High · exact name match',
    },
    {
      tone: 'warning',
      title: 'Khoản vay vượt hạn mức điều lệ',
      description: 'Điều lệ công ty quy định hạn mức vay tối đa 4 tỷ, khoản vay đề nghị 5 tỷ.',
      evidence: 'Điều lệ công ty / borrowing authority clause; loan proposal 5 tỷ',
      rule: 'Warn nếu khoản vay đề nghị vượt hạn mức trong điều lệ.',
      action: 'Bổ sung biên bản họp bất thường hoặc sửa đổi điều lệ trước giải ngân.',
      confidence: 'Medium · pending latest charter version',
      meta: 'Cần biên bản họp bất thường hoặc sửa đổi điều lệ',
    },
  ],
  footerHint: 'Có thể chuyển phản biện với điều kiện xử lý điều lệ trước giải ngân.',
  secondaryLabel: 'Yêu cầu KH bổ sung',
  primaryLabel: 'Xác nhận & chuyển phản biện',
  nextRoute: 'creditUnderwriting',
};

export function LegalReviewPage({ params }: { params: Record<string, string> }) {
  return <WorkflowAgentPage config={config} caseId={params.caseId} />;
}
