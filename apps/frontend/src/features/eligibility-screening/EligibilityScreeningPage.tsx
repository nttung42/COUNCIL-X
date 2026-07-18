import { WorkflowAgentPage, type WorkflowPageConfig } from '../sharedWorkflow';

const config: WorkflowPageConfig = {
  agentTitle: 'Gate Agent — Rà soát nhanh',
  agentSubtitle: 'Cty TNHH ABC · Trần Văn B (GĐ)',
  agentIcon: '🛡️',
  welcomeTitle: 'Gate Agent đã chạy xong 3 kiểm tra',
  welcomeText: 'Tôi đã tự động tra CIC, sàng lọc AML/blacklist và kiểm tra giới hạn nhóm khách hàng liên quan. Có 1 điểm cần xem xét trước khi tiếp tục.',
  chips: ['Vì sao cần xem xét giới hạn nhóm KH?', 'Giải thích chi tiết kết quả CIC', 'Danh sách AML đã đối chiếu gồm những gì?', 'Tra lại CIC mới nhất giúp tôi'],
  banner: 'Kết quả tự động 95% — chỉ cần xem xét cờ vàng và xác nhận GO.',
  loadingText: 'Đang tra CIC, AML/sanction list và giới hạn nhóm khách hàng liên quan.',
  progress: ['CIC — Lịch sử tín dụng', 'AML / Sanction list', 'Giới hạn nhóm khách hàng liên quan'],
  summaryTitle: 'Kết quả sàng lọc điều kiện',
  cards: [
    { tone: 'good', title: 'CIC sạch', description: 'Nhóm nợ hiện tại: Nhóm 1; không ghi nhận nợ xấu trong 24 tháng gần nhất.', meta: 'Nguồn: CIC API · Độ tin cậy 99%' },
    { tone: 'good', title: 'AML / Sanction list đạt', description: 'Không khớp tên với OFAC, UN, EU Sanctions hoặc blacklist nội bộ SHB.', meta: 'Độ tin cậy 97%' },
    { tone: 'warning', title: 'Giới hạn nhóm khách hàng gần ngưỡng', description: 'Tổng dư nợ nhóm nếu cấp thêm 5 tỷ là 13.2 tỷ, bằng 88% giới hạn nội bộ.', meta: 'GO có điều kiện' },
  ],
  footerHint: 'GO có điều kiện; lưu ý giới hạn nhóm khách hàng cho bước phê duyệt.',
  secondaryLabel: 'Từ chối hồ sơ',
  primaryLabel: 'Tiếp tục thẩm định tài chính',
  nextRoute: 'financialReview',
};

export function EligibilityScreeningPage({ params }: { params: Record<string, string> }) {
  return <WorkflowAgentPage config={config} caseId={params.caseId} />;
}
