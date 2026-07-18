import { WorkflowAgentPage, type WorkflowPageConfig } from '../sharedWorkflow';

const config: WorkflowPageConfig = {
  agentTitle: 'Credit Support Agent — Hỗ trợ tín dụng',
  agentSubtitle: 'Cty TNHH ABC · REQ-2026-00458',
  agentIcon: '📄',
  welcomeTitle: 'Checklist giải ngân đang chờ 2 điều kiện',
  welcomeText: 'Hợp đồng tín dụng và thế chấp đã hoàn tất công chứng/đăng ký giao dịch bảo đảm. Còn thiếu giải trình doanh thu và biên bản thực địa tài sản bảo đảm.',
  chips: ['Còn thiếu điều kiện gì để giải ngân?', 'Nội dung hợp đồng tín dụng gồm gì?', 'Đăng ký GDBĐ (NPAST) là gì?', 'Đã nhắc khách hàng bao nhiêu lần?'],
  banner: 'Hợp đồng & giải ngân — theo dõi checklist điều kiện theo thời gian thực.',
  loadingText: 'Đang cập nhật checklist điều kiện giải ngân real-time.',
  progress: ['Hợp đồng tín dụng', 'Hợp đồng thế chấp', 'Đăng ký giao dịch bảo đảm', 'Điều kiện khách hàng', 'Điều kiện thực địa'],
  summaryTitle: 'Checklist điều kiện giải ngân',
  cards: [
    { tone: 'good', title: 'Hợp đồng tín dụng đã ký', description: 'Hoàn tất ký kết giữa SHB và Cty TNHH ABC.', meta: '15/07/2026' },
    { tone: 'good', title: 'Hợp đồng thế chấp đã công chứng', description: 'Công chứng tại Văn phòng công chứng Q9.', meta: '16/07/2026' },
    { tone: 'good', title: 'Đăng ký giao dịch bảo đảm', description: 'Đăng ký thành công trên hệ thống NPAST.', meta: '16/07/2026' },
    { tone: 'critical', title: 'Chưa có giải trình doanh thu', description: 'Chờ khách hàng cung cấp giải trình chênh lệch BCTC ↔ thuế 25%.', meta: 'Chờ khách hàng' },
    { tone: 'warning', title: 'Chờ biên bản thực địa TSBĐ', description: 'Chờ cán bộ hoàn tất thực địa tài sản bảo đảm tại Q9.', meta: 'Chờ cán bộ' },
  ],
  footerHint: 'Chưa thể giải ngân khi còn 2 điều kiện mở.',
  secondaryLabel: 'Gửi nhắc KH',
  primaryLabel: 'Sang giám sát danh mục',
  nextRoute: 'portfolioMonitoring',
};

export function LoanDisbursementPage({ params }: { params: Record<string, string> }) {
  return <WorkflowAgentPage config={config} caseId={params.caseId} />;
}
