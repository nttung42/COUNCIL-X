import type { StepNumber } from '../types';

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
  1: 'Nhập thông tin',
  2: 'Kết quả tra cứu',
  3: 'Định giá',
  4: 'Rủi ro',
  5: 'Dashboard',
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

export const DEMO_EDIT_REPLIES: Record<DemoEditKey, string> = {
  area: 'Đã sửa diện tích đất thành <b>65 m²</b> theo phản hồi của bạn — trường này đang <b>chờ xác nhận</b> ở tab <b>Nhập thông tin</b>, bấm Xác nhận khi bạn đồng ý.',
  environment: 'Đã cập nhật lại thông tin môi trường khu vực theo phản hồi của bạn — đang <b>chờ xác nhận</b> ở tab <b>Kết quả tra cứu</b>.',
  valuation: 'Đã điều chỉnh lại giá trị đề xuất theo phản hồi của bạn — đang <b>chờ xác nhận</b> ở tab <b>Định giá</b>.',
  reputation: 'Đã cập nhật nhóm rủi ro danh tiếng/tâm linh và điểm rủi ro tổng theo phản hồi của bạn — đang <b>chờ xác nhận</b> ở tab <b>Rủi ro</b>.',
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
      text: 'Rà soát thông tin ở tab <b>Nhập thông tin</b>. Nếu dữ liệu đúng, bấm <b>Xác nhận &amp; Tiếp theo</b> để chuyển sang tra cứu khu vực.',
      delay: 1000,
    },
  ],
  market: [
    { type: 'user', text: 'Giá thị trường khu vực này hiện nay thế nào?' },
    {
      type: 'agent',
      text: 'Giá trung bình khu vực hiện khoảng <b>85–98 triệu/m²</b>, dựa trên 5 giao dịch so sánh trong bán kính 1.1km, cập nhật gần nhất 02/2026 — xem chi tiết ở tab <b>Kết quả tra cứu</b>.',
      delay: 1000,
    },
  ],
  legal: [
    { type: 'user', text: 'Kiểm tra tính pháp lý của tài sản.' },
    {
      type: 'agent',
      text: 'Sổ hồng chính chủ, không ghi nhận tranh chấp hay thế chấp tại tổ chức tín dụng khác. Quy hoạch khu vực không có quy hoạch treo — xem chi tiết ở tab <b>Kết quả tra cứu</b>.',
      delay: 1000,
    },
  ],
  process: [
    { type: 'user', text: 'Quy trình thẩm định BĐS thế chấp gồm những bước nào?' },
    {
      type: 'agent',
      text: 'Quy trình gồm 3 bước chính: (1) Tra cứu dữ liệu khu vực &amp; pháp lý, (2) Định giá bằng 3 phương pháp, (3) Chấm điểm rủi ro tài sản &amp; đề xuất LTV — sau đó tổng hợp lại toàn bộ trace xử lý ở tab Dashboard. Ở mỗi bước bạn đều chủ động rà soát và bấm Xác nhận & Tiếp theo.',
      delay: 1000,
    },
  ],
  'edit-demo': [
    { type: 'user', text: 'Diện tích đất đã nhập chưa đúng, số thực tế là 65m².' },
    { type: 'agent', text: DEMO_EDIT_REPLIES.area, delay: 900, applyKey: 'area' },
  ],
};
