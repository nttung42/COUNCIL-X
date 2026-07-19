import type { AppraisalCaseFull, StepNumber } from '../types';

// Kịch bản trò chuyện demo — chuyển thể từ khối <script> trong ai/PAA_Mockup_SHB_8.html.
// Khi nối API thật, thay các phản hồi tĩnh này bằng response của Advisory/Copilot agent,
// nhưng giữ nguyên shape ChatStep để không phải viết lại ChatPane.

export interface ChatStep {
  type: 'user' | 'agent' | 'status';
  text: string;
  delay?: number;
  /** Chạy khi tin nhắn agent/status vừa hiện — dùng để áp dụng 1 thay đổi demo lên caseData. */
  applyKey?: DemoEditKey;
}

export type DemoEditKey = 'area' | 'environment' | 'valuation' | 'reputation';

export const APPRAISAL_STAGE_LABELS: Record<StepNumber, string> = {
  1: 'Dữ liệu tài sản',
  2: 'Pháp lý & thị trường',
  3: 'Định giá',
  4: 'Rủi ro & LTV',
  5: 'Báo cáo & evidence',
};

export const LOADING_TEXT: Record<StepNumber, string> = {
  1: 'Đang tải thông tin đã nhập…',
  2: 'Đang tra cứu dữ liệu khu vực…',
  3: 'Đang tính toán định giá…',
  4: 'Đang chấm điểm rủi ro…',
  5: 'Đang tổng hợp trace xử lý…',
};

export const NEXT_USER_MSG: Partial<Record<StepNumber, string>> = {
  1: 'Thông tin tài sản đã sẵn sàng, chuyển sang tra cứu dữ liệu khu vực.',
  2: 'Kết quả tra cứu đã rà soát, chuyển sang định giá.',
  3: 'Định giá đã rà soát, chuyển sang đánh giá rủi ro.',
  4: 'Rủi ro chấp nhận được, mở tổng hợp trace xử lý.',
};

export const APPRAISAL_STEP_MSG: Partial<Record<StepNumber, string>> = {
  2: 'Hoàn tất tra cứu khu vực — phát hiện 1 điểm cần lưu ý về tin đồn chưa xác thực. Rà soát trước khi xác nhận.',
  3: 'Định giá đề xuất <b>4.85 tỷ</b>, độ tin cậy 78%.',
  4: 'Điểm rủi ro BĐS <b>34/100 (Trung bình)</b>, LTV đề xuất 65%.',
  5: 'Trace xử lý của hồ sơ đã sẵn sàng.',
};

const SEVERITY_TEXT: Record<string, string> = {
  thap: 'Thấp',
  trung_binh: 'Trung bình',
  cao: 'Cao',
  nghiem_trong: 'Nghiêm trọng',
};

/**
 * Bản tin theo bước lấy SỐ LIỆU THẬT từ caseData hiện hành (đã map từ API) thay vì
 * chuỗi tĩnh của mockup — đảm bảo Assistant nói đúng những gì đang hiển thị.
 * Trả về null khi chưa có dữ liệu tương ứng (fallback dùng APPRAISAL_STEP_MSG).
 */
export function buildAppraisalStepMsg(n: StepNumber, c: AppraisalCaseFull): string | null {
  if (n === 2 && c.lookupFindings.length) {
    const attention = c.lookupFindings.filter(
      (f) => f.statusBadge && f.statusBadge !== 'da_xac_thuc',
    ).length;
    return (
      `Hoàn tất tra cứu <b>${c.lookupFindings.length} nguồn</b> khu vực — ` +
      (attention
        ? `phát hiện <b>${attention} điểm cần lưu ý</b>. Rà soát trước khi xác nhận.`
        : 'không có điểm cần lưu ý. Rà soát và xác nhận để tiếp tục.')
    );
  }
  if (n === 3 && c.valuation?.proposedValueLabel) {
    return `Định giá đề xuất <b>${c.valuation.proposedValueLabel}</b>, độ tin cậy ${c.valuation.confidencePct}%.`;
  }
  if (n === 4 && c.risk) {
    const label = SEVERITY_TEXT[c.risk.riskLabel] ?? c.risk.riskLabel;
    return `Điểm rủi ro BĐS <b>${c.risk.riskScore}/100 (${label})</b>, LTV đề xuất ${c.risk.ltvProposedPct}%.`;
  }
  return null;
}

export const DEMO_EDIT_REPLIES: Record<DemoEditKey, string> = {
  area: 'Đã sửa diện tích đất thành <b>200 m²</b> theo phản hồi của bạn — trường này đang <b>chờ xác nhận</b> ở tab <b>Dữ liệu tài sản</b>, bấm Xác nhận khi bạn đồng ý.',
  environment: 'Đã cập nhật lại thông tin môi trường khu vực theo phản hồi của bạn — đang <b>chờ xác nhận</b> ở tab <b>Pháp lý & thị trường</b>.',
  valuation: 'Đã điều chỉnh lại giá trị đề xuất theo phản hồi của bạn — đang <b>chờ xác nhận</b> ở tab <b>Định giá</b>.',
  reputation: 'Đã cập nhật nhóm rủi ro danh tiếng/tâm linh và điểm rủi ro tổng theo phản hồi của bạn — đang <b>chờ xác nhận</b> ở tab <b>Rủi ro & LTV</b>.',
};

const DEMO_EDIT_KEYWORDS: Array<{ key: DemoEditKey; keywords: string[] }> = [
  { key: 'area', keywords: ['diện tích', 'dien tich'] },
  { key: 'environment', keywords: ['ngập', 'môi trường', 'moi truong'] },
  { key: 'valuation', keywords: ['định giá', 'dinh gia', 'giá trị', 'gia tri'] },
  { key: 'reputation', keywords: ['rủi ro', 'rui ro', 'tâm linh', 'tam linh', 'danh tiếng', 'danh tieng'] },
];

export function matchDemoEdit(text: string): DemoEditKey | null {
  const t = text.toLowerCase();
  const hit = DEMO_EDIT_KEYWORDS.find((e) => e.keywords.some((k) => t.includes(k)));
  return hit ? hit.key : null;
}

export type ChipFlow = 'appraise' | 'market' | 'legal' | 'process' | 'edit-demo';

export const CHAT_CHIPS: { flow: ChipFlow; icon: string; label: string }[] = [
  { flow: 'appraise', icon: 'CO', label: 'Thẩm định tài sản vừa nhập' },
  { flow: 'market', icon: 'MK', label: 'Xem giá thị trường khu vực' },
  { flow: 'legal', icon: 'LG', label: 'Kiểm tra pháp lý tài sản' },
  { flow: 'process', icon: 'PR', label: 'Xem quy trình thẩm định TSBĐ' },
  { flow: 'edit-demo', icon: 'ED', label: 'Sửa diện tích đất đã nhập' },
];

export const DEMO_FLOWS: Record<ChipFlow, ChatStep[]> = {
  appraise: [
    { type: 'user', text: 'Thẩm định tài sản vừa nhập.' },
    {
      type: 'agent',
      text: 'Rà soát thông tin ở tab <b>Dữ liệu tài sản</b>. Nếu dữ liệu đúng, bấm <b>Xác nhận &amp; Tiếp theo</b> để chuyển sang tra cứu khu vực.',
      delay: 1000,
    },
  ],
  market: [
    { type: 'user', text: 'Giá thị trường khu vực này hiện nay thế nào?' },
    {
      type: 'agent',
      text: 'Giá trung bình khu vực hiện khoảng <b>123–162 triệu/m²</b>, dựa trên 7 giao dịch so sánh trong bán kính 1.8km — xem chi tiết ở tab <b>Pháp lý & thị trường</b>.',
      delay: 1000,
    },
  ],
  legal: [
    { type: 'user', text: 'Kiểm tra tính pháp lý của tài sản.' },
    {
      type: 'agent',
      text: 'Sổ hồng chính chủ, không ghi nhận tranh chấp hay thế chấp tại tổ chức tín dụng khác. Quy hoạch khu vực không có quy hoạch treo — xem chi tiết ở tab <b>Pháp lý & thị trường</b>.',
      delay: 1000,
    },
  ],
  process: [
    { type: 'user', text: 'Quy trình thẩm định BĐS thế chấp gồm những bước nào?' },
    {
      type: 'agent',
      text: 'Quy trình gồm 3 bước chính: (1) Tra cứu dữ liệu khu vực &amp; pháp lý, (2) Định giá bằng 3 phương pháp, (3) Chấm điểm rủi ro tài sản &amp; đề xuất LTV — sau đó tổng hợp lại toàn bộ trace xử lý ở tab Báo cáo & evidence. Ở mỗi bước bạn đều chủ động rà soát và bấm Xác nhận & Tiếp theo.',
      delay: 1000,
    },
  ],
  'edit-demo': [
    { type: 'user', text: 'Diện tích đất đã nhập chưa đúng, số thực tế là 200m².' },
    { type: 'agent', text: DEMO_EDIT_REPLIES.area, delay: 900, applyKey: 'area' },
  ],
};
