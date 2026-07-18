// Kiểu dữ liệu "trên dây" (wire types) — khớp nguyên văn các Pydantic schema của backend thật
// tại ai/src/shb/schemas/api.py và ai/src/shb/ai/plugins/property_intake/schema.py.
// Không dùng trực tiếp trong UI — src/services/apiClient.ts map sang các type camelCase ở
// src/types.ts (Tab1Field, DocPage, AttachedDocument...) trước khi đưa vào store.

export type ApiDocType = 'so_do_so_hong' | 'to_khai_lptb' | 'bien_ban_ban_giao' | 'thong_bao_thue_dat' | 'khac';
export type ApiFieldStatus = 'da_xac_thuc' | 'can_xac_minh' | 'mau_thuan' | 'nhap_tay' | 'suy_luan';
export type ApiTab1Section = 'A' | 'B' | 'C' | 'D';

export interface ApiBBox {
  page: number;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface ApiDocumentInfo {
  file_id: string;
  file_name: string;
  doc_type: ApiDocType;
  is_scanned: boolean;
  page_count: number;
}

export interface ApiFormField {
  key: string;
  section: ApiTab1Section;
  label: string;
  value: string | null;
  confidence: number; // 0-1
  status: ApiFieldStatus;
  source_doc?: string | null;
  source_page?: number | null;
  source_snippet?: string | null;
  bbox?: ApiBBox | null;
}

export interface ApiPropertyIntakeOutput {
  case_id?: string | null;
  documents: ApiDocumentInfo[];
  fields: ApiFormField[];
  warnings: string[];
}

export interface ApiFileResponse {
  id: string;
  original_name: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

export type ApiJobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface ApiJobResponse {
  id: string;
  plugin_id: string;
  status: ApiJobStatus;
  input: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error: string | null;
  progress: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface ApiPluginRunAsyncResponse {
  job_id: string;
  status: string;
}

export interface ApiPluginRunResponse {
  result: Record<string, unknown>;
}
