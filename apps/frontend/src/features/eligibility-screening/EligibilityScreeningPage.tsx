import { WorkflowAgentPage, type WorkflowPageConfig } from '../sharedWorkflow';

const config: WorkflowPageConfig = {
  agentTitle: 'Gate — Rà soát nhanh',
  agentSubtitle: 'Cty TNHH ABC · Trần Văn B (GĐ)',
  agentIcon: 'GT',
  welcomeTitle: 'Sàng lọc điều kiện hoàn tất',
  welcomeText: '3/3 kiểm tra đã hoàn tất. Có 1 warning về giới hạn nhóm khách hàng cần lưu ý ở bước phê duyệt.',
  chips: ['Giải thích giới hạn nhóm KH', 'Xem kết quả CIC', 'Xem nguồn AML đã đối chiếu', 'Tra lại CIC mới nhất'],
  banner: 'Hoàn tất sàng lọc điều kiện — GO có điều kiện với 1 warning cần theo dõi.',
  loadingText: 'Tra CIC, AML/sanction list và giới hạn nhóm khách hàng liên quan.',
  progress: ['CIC history checked', 'AML and sanction list screened', 'Related-party exposure limit checked'],
  summaryTitle: 'Kết quả sàng lọc điều kiện',
  cards: [
    {
      tone: 'good',
      title: 'CIC sạch',
      description: 'Nhóm nợ hiện tại: Nhóm 1; không ghi nhận nợ xấu trong 24 tháng gần nhất.',
      evidence: 'CIC API lookup · customer tax ID and representative ID',
      rule: 'Reject nếu có nợ nhóm 3–5 trong 24 tháng gần nhất.',
      action: 'Tiếp tục thẩm định tài chính.',
      confidence: 'High · direct CIC response',
      meta: 'Nguồn: CIC API · Độ tin cậy 99%',
    },
    {
      tone: 'good',
      title: 'AML / Sanction list đạt',
      description: 'Không khớp tên với OFAC, UN, EU Sanctions hoặc blacklist nội bộ SHB.',
      evidence: 'OFAC, UN, EU Sanctions, SHB internal blacklist',
      rule: 'Block nếu match chính xác hoặc fuzzy match vượt ngưỡng.',
      action: 'Không cần xử lý thêm.',
      confidence: 'High · no name/date-of-birth match',
      meta: 'Độ tin cậy 97%',
    },
    {
      tone: 'warning',
      title: 'Giới hạn nhóm khách hàng gần ngưỡng',
      description: 'Tổng dư nợ nhóm nếu cấp thêm 5 tỷ là 13.2 tỷ, bằng 88% giới hạn nội bộ.',
      evidence: 'Core Banking exposure snapshot; related-party mapping',
      rule: 'Warn nếu nhóm khách hàng đạt > 85% giới hạn nội bộ.',
      action: 'Đưa vào điều kiện theo dõi ở bước phê duyệt.',
      confidence: 'Medium · depends on latest exposure refresh',
      meta: 'GO có điều kiện',
    },
  ],
  footerHint: 'GO có điều kiện; lưu ý giới hạn nhóm khách hàng cho bước phê duyệt.',
  secondaryLabel: 'Từ chối hồ sơ',
  primaryLabel: 'Tiếp tục thẩm định tài chính',
  nextRoute: 'financialReview',
};

export function EligibilityScreeningPage({ params }: { params: Record<string, string> }) {
  return <WorkflowAgentPage config={config} caseId={params.caseId} />;
}
