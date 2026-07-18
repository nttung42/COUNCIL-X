import { WorkflowAgentPage, type WorkflowPageConfig } from '../sharedWorkflow';

const config: WorkflowPageConfig = {
  agentTitle: 'Financial Agent — Thẩm định tài chính',
  agentSubtitle: 'Cty TNHH ABC · Trần Văn B (GĐ)',
  agentIcon: '📊',
  welcomeTitle: 'Financial Agent đã phân tích BCTC 2023–2024',
  welcomeText: 'Tôi đã tính các chỉ số tài chính, đối chiếu sao kê và đưa ra điểm rủi ro tổng hợp. Có 1 điểm cần lưu ý về đòn bẩy và chênh lệch doanh thu.',
  chips: ['Giải thích chênh lệch doanh thu 12.3 tỷ vs 9.1 tỷ', 'Giải thích chỉ số DSCR 1.42x', 'Vì sao nợ/VCSH tăng lên 2.1x?', 'So sánh với trung bình ngành'],
  banner: 'Đã tính tự động toàn bộ chỉ số tài chính — điểm rủi ro 62/100.',
  loadingText: 'Đang đọc BCTC, tính chỉ số tài chính và đối chiếu sao kê.',
  progress: ['Trích xuất BCTC 2023–2024', 'DSCR & thanh khoản', 'Đối chiếu sao kê ↔ BCTC', 'Tổng hợp điểm rủi ro'],
  summaryTitle: 'Nhận xét tổng hợp tài chính',
  metrics: [
    { label: 'Doanh thu', value: '12.3 tỷ', sub: '2023: 10.1 tỷ · ↑21%' },
    { label: 'Lợi nhuận ròng', value: '1.1 tỷ', sub: '2023: 0.8 tỷ · ↑37%' },
    { label: 'Nợ / VCSH', value: '2.1x', sub: 'Đòn bẩy tăng', tone: '#8a6100' },
    { label: 'DSCR', value: '1.42x', sub: 'Vượt ngưỡng 1.2x', tone: 'var(--good)' },
  ],
  cards: [
    { tone: 'good', title: 'Khả năng trả nợ đạt', description: 'DSCR 2024 đạt 1.42x, vượt ngưỡng an toàn nội bộ 1.2x.' },
    { tone: 'warning', title: 'Chênh lệch doanh thu cần giải trình', description: 'Doanh thu BCTC 12.3 tỷ lệch 25% so với doanh thu kê khai thuế ước tính.', meta: 'Kế thừa cờ vàng từ Intake' },
    { tone: 'warning', title: 'Đòn bẩy tăng', description: 'Nợ/VCSH tăng từ 1.8x lên 2.1x; vẫn chấp nhận được nhưng cần theo dõi.' },
  ],
  footerHint: 'Xác nhận kết quả tài chính, sau đó chuyển sang thẩm định pháp lý.',
  secondaryLabel: 'Chỉnh sửa dữ liệu đầu vào',
  primaryLabel: 'Xác nhận & tiếp tục',
  nextRoute: 'legalReview',
};

export function FinancialReviewPage({ params }: { params: Record<string, string> }) {
  return <WorkflowAgentPage config={config} caseId={params.caseId} />;
}
