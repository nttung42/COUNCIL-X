import { WorkflowAgentPage, type WorkflowPageConfig } from '../sharedWorkflow';

const config: WorkflowPageConfig = {
  agentTitle: 'Financial — Thẩm định tài chính',
  agentSubtitle: 'Cty TNHH ABC · Trần Văn B (GĐ)',
  agentIcon: 'FI',
  welcomeTitle: 'Sẵn sàng thẩm định tài chính',
  welcomeText: 'Đã tính và đối chiếu chỉ số tài chính. Có 2 warning cần theo dõi về doanh thu và đòn bẩy.',
  chips: ['Giải thích chênh lệch doanh thu 12.3 tỷ vs 9.1 tỷ', 'Giải thích chỉ số DSCR 1.42x', 'Vì sao nợ/VCSH tăng lên 2.1x?', 'So sánh với trung bình ngành'],
  banner: 'Hoàn tất phân tích tài chính — điểm rủi ro 62/100.',
  loadingText: 'Đọc BCTC, tính chỉ số tài chính và đối chiếu sao kê.',
  progress: ['BCTC 2023–2024 extracted', 'DSCR and liquidity calculated', 'Bank statement reconciled with BCTC', 'Risk score aggregated'],
  summaryTitle: 'Nhận xét tổng hợp tài chính',
  metrics: [
    { label: 'Doanh thu', value: '12.3 tỷ', sub: '2023: 10.1 tỷ · ↑21%' },
    { label: 'Lợi nhuận ròng', value: '1.1 tỷ', sub: '2023: 0.8 tỷ · ↑37%' },
    { label: 'Nợ / VCSH', value: '2.1x', sub: 'Đòn bẩy tăng', tone: 'var(--warning)' },
    { label: 'DSCR', value: '1.42x', sub: 'Vượt ngưỡng 1.2x', tone: 'var(--success)' },
  ],
  table: {
    title: 'Ratio analysis',
    columns: ['Metric', '2023', '2024', 'Change', 'Threshold', 'Status'],
    rows: [
      ['Revenue', '10.1 tỷ', '12.3 tỷ', '+21%', '-', 'Pass'],
      ['Net profit', '0.8 tỷ', '1.1 tỷ', '+37%', '-', 'Pass'],
      ['DSCR', '1.18x', '1.42x', '+0.24x', '> 1.20x', 'Pass'],
      ['Debt / Equity', '1.8x', '2.1x', '+0.3x', '< 2.5x', 'Watch'],
      ['Revenue variance', '-', '25%', '-', '< 15%', 'Explain'],
    ],
  },
  cards: [
    {
      tone: 'good',
      title: 'Khả năng trả nợ đạt',
      description: 'DSCR 2024 đạt 1.42x, vượt ngưỡng an toàn nội bộ 1.2x.',
      evidence: 'BCTC_2024.xlsx / cash flow; debt schedule / principal and interest',
      rule: 'Pass nếu DSCR ≥ 1.20x.',
      action: 'Tiếp tục bước pháp lý nếu không có blocker khác.',
      confidence: 'High · formula inputs complete',
    },
    {
      tone: 'warning',
      title: 'Chênh lệch doanh thu cần giải trình',
      description: 'Doanh thu BCTC 12.3 tỷ lệch 25% so với doanh thu kê khai thuế ước tính.',
      evidence: 'BCTC_2024.xlsx / P&L; VAT_Q4_2024.pdf / tax return',
      rule: 'Flag nếu chênh lệch doanh thu > 15%.',
      action: 'Yêu cầu giải trình trước khi trình phê duyệt.',
      confidence: 'High · inherited from Intake cross-check',
      meta: 'Kế thừa cờ vàng từ Intake',
    },
    {
      tone: 'warning',
      title: 'Đòn bẩy tăng',
      description: 'Nợ/VCSH tăng từ 1.8x lên 2.1x; vẫn chấp nhận được nhưng cần theo dõi.',
      evidence: 'BCTC_2023.xlsx and BCTC_2024.xlsx / balance sheet',
      rule: 'Watch nếu Nợ/VCSH tăng > 0.2x YoY.',
      action: 'Theo dõi covenant và dòng tiền sau giải ngân.',
      confidence: 'Medium · depends on updated liabilities schedule',
    },
  ],
  footerHint: 'Xác nhận kết quả tài chính, sau đó chuyển sang thẩm định pháp lý.',
  secondaryLabel: 'Chỉnh sửa dữ liệu đầu vào',
  primaryLabel: 'Xác nhận & tiếp tục',
  nextRoute: 'legalReview',
};

export function FinancialReviewPage({ params }: { params: Record<string, string> }) {
  return <WorkflowAgentPage config={config} caseId={params.caseId} />;
}
