import type { AttachedDocument, DocPage, Tab1Field } from '../types';
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
export function mapPropertyIntakeOutput(output: ApiPropertyIntakeOutput, attachedDocuments: AttachedDocument[] = []): {
  tab1Fields: Tab1Field[];
  docPages: DocPage[];
} {
  const attachments = new Map(attachedDocuments.map((doc) => [doc.id, doc]));
  const pageCounts = new Map(output.documents.map((doc) => [doc.file_id, Math.max(1, doc.page_count || 1)]));
  const docPages: DocPage[] = output.documents.flatMap((doc) => {
    const attached = attachments.get(doc.file_id);
    const pageCount = pageCounts.get(doc.file_id) ?? 1;
    // PDF: preview từng trang dưới dạng ảnh PNG render server-side (?format=png&page=N).
    // Ảnh chính là trang giấy (không toolbar/lề của viewer) nên bbox % đè lên khớp
    // tuyệt đối — iframe PDF không bao giờ căn được toạ độ vùng trích xuất.
    const isPdf = (attached?.contentType ?? '').toLowerCase().includes('pdf');
    return Array.from({ length: pageCount }, (_, i) => {
      const pageNumber = i + 1;
      return {
        key: pageCount > 1 ? `${doc.file_id}:p${pageNumber}` : doc.file_id,
        label: `${docTypeLabel(doc.doc_type)}${pageCount > 1 ? ` · tr.${pageNumber}` : ''}`,
        scan: doc.is_scanned,
        fileName: attached?.fileName ?? doc.file_name,
        contentType: isPdf ? 'image/png' : attached?.contentType,
        previewUrl:
          attached?.previewUrl && isPdf
            ? `${attached.previewUrl}?format=png&page=${pageNumber}`
            : attached?.previewUrl,
        pageNumber,
      };
    });
  });

  const docPageKey = (fileId: string | null | undefined, page: number | null | undefined) => {
    if (!fileId) return null;
    const pageCount = pageCounts.get(fileId) ?? 1;
    return pageCount > 1 ? `${fileId}:p${page ?? 1}` : fileId;
  };

  const tab1Fields: Tab1Field[] = output.fields.map((f) => {
    const sourcePage = f.source_page ?? f.bbox?.page ?? null;
    return {
      key: f.key,
      section: f.section,
      label: f.label,
      value: f.value ?? '',
      confidencePct: typeof f.confidence === 'number' ? Math.round(f.confidence * 100) : null,
      status: f.status,
      sourceDocKey: docPageKey(f.source_doc, sourcePage),
      sourceSnippet: f.source_snippet ?? null,
      bbox: f.bbox
        ? {
            top: Math.round(f.bbox.y * 1000) / 10,
            left: Math.round(f.bbox.x * 1000) / 10,
            w: Math.round(f.bbox.w * 1000) / 10,
            h: Math.round(f.bbox.h * 1000) / 10,
          }
        : null,
    };
  });

  return { tab1Fields, docPages };
}
