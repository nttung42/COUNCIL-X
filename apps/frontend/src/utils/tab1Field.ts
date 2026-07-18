import type { DocPage, Tab1Field, Tab1FieldStatus } from '../types';

export function getFieldValue(fields: Tab1Field[], key: string): string {
  return fields.find((f) => f.key === key)?.value ?? '';
}

export function docLabel(docPages: DocPage[], docKey: string | null): string {
  if (!docKey) return '';
  return docPages.find((d) => d.key === docKey)?.label ?? docKey;
}

export interface SourceChipInfo {
  label: string;
  warn: boolean;
}

/**
 * Suy ra nhãn chip "📄 nguồn" + màu cảnh báo từ status/sourceDocKey của 1 Tab1Field.
 * Tách riêng khỏi dữ liệu vì API thật (FormField) không tự kèm câu chữ hiển thị — chỉ có
 * status/source_doc/source_snippet — nên phần trình bày phải suy ra ở frontend.
 */
export function getSourceChip(field: Tab1Field, docPages: DocPage[]): SourceChipInfo | null {
  const label = docLabel(docPages, field.sourceDocKey);
  switch (field.status) {
    case 'nhap_tay':
      return { label: '✍️ Nhập tay (không có nguồn)', warn: false };
    case 'suy_luan':
      return field.sourceDocKey
        ? { label: `📄 ${label} ↗`, warn: false }
        : { label: '📄 Suy luận (không có vùng nguồn)', warn: false };
    case 'mau_thuan':
      return { label: '⚠ Mâu thuẫn giữa các nguồn ↗', warn: true };
    case 'can_xac_minh':
      return { label: field.sourceDocKey ? `📄 ${label} · cần xác minh ↗` : '⚠ Cần xác minh thêm', warn: true };
    case 'da_xac_thuc':
    default:
      return field.sourceDocKey ? { label: `📄 ${label} ↗`, warn: false } : null;
  }
}

export const TAB1_STATUS_TOOLTIP: Record<Tab1FieldStatus, string> = {
  da_xac_thuc: 'Đã trích xuất và xác thực từ tài liệu.',
  can_xac_minh: 'Cần thẩm định viên xác minh thêm trước khi chốt.',
  mau_thuan: 'Các tài liệu ghi nhận giá trị khác nhau — cần thẩm định viên chốt.',
  nhap_tay: 'Không có trong tài liệu — thẩm định viên nhập tay.',
  suy_luan: 'PAA suy luận từ ngữ cảnh, không trích trực tiếp từ tài liệu.',
};
