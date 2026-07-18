import type { DocPage, Tab1Field } from '../types';
import type { ApiDocType, ApiPropertyIntakeOutput } from '../services/apiTypes';

const DOC_TYPE_LABEL: Record<ApiDocType, string> = {
  so_do_so_hong: 'Sổ đỏ/Sổ hồng',
  to_khai_lptb: 'Tờ khai LPTB',
  bien_ban_ban_giao: 'Biên bản bàn giao',
  thong_bao_thue_dat: 'Thông báo thuế đất',
  khac: 'Tài liệu khác',
};

export function docTypeLabel(docType: ApiDocType): string {
  return DOC_TYPE_LABEL[docType] ?? docType;
}

/**
 * Map PropertyIntakeOutput (kết quả job property_intake) sang docPages/tab1Fields dùng trong UI.
 * Giả định: FormField.source_doc chứa file_id của DocumentInfo tương ứng (liên kết duy nhất có sẵn
 * giữa 2 danh sách trong schema hiện tại) — nếu backend đổi quy ước này, chỉ cần sửa ở đây.
 */
export function mapPropertyIntakeOutput(output: ApiPropertyIntakeOutput): {
  tab1Fields: Tab1Field[];
  docPages: DocPage[];
} {
  const docPages: DocPage[] = output.documents.map((doc) => ({
    key: doc.file_id,
    label: docTypeLabel(doc.doc_type),
    scan: doc.is_scanned,
  }));

  const tab1Fields: Tab1Field[] = output.fields.map((f) => ({
    key: f.key,
    section: f.section,
    label: f.label,
    value: f.value ?? '',
    confidencePct: typeof f.confidence === 'number' ? Math.round(f.confidence * 100) : null,
    status: f.status,
    sourceDocKey: f.source_doc ?? null,
    sourceSnippet: f.source_snippet ?? null,
    bbox: f.bbox
      ? {
          top: Math.round(f.bbox.y * 1000) / 10,
          left: Math.round(f.bbox.x * 1000) / 10,
          w: Math.round(f.bbox.w * 1000) / 10,
          h: Math.round(f.bbox.h * 1000) / 10,
        }
      : null,
  }));

  return { tab1Fields, docPages };
}
