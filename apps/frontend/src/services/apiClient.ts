import type { AttachedDocument, DocPage, Tab1Field } from '../types';
import { mapPropertyIntakeOutput } from '../utils/mapPropertyIntake';
import type {
  ApiFileResponse,
  ApiJobResponse,
  ApiPluginRunAsyncResponse,
  ApiPluginRunResponse,
  ApiPropertyIntakeOutput,
  ApiPropertyLookupOutput,
  ApiPropertyValuationOutput,
} from './apiTypes';

// Client cho backend thật ở ai/ (FastAPI, xem ai/src/shb/main.py + ai/src/shb/api/v1/api.py).
// Hiện backend mới có route cho upload-file/chạy-service-bất-đồng-bộ/SSE job — CHƯA có
// route riêng cho case/lookup/valuation/risk/dashboard/chat (những bảng đó mới chỉ là ORM model,
// xem models_paa.py). Vì vậy chỉ màn "Nhập thông tin" (property_intake) gọi API thật; các màn
// 2-5 + chat + xác nhận chỉnh sửa vẫn dùng fixtureCase cho tới khi backend có endpoint tương ứng.

const RAW_BASE_URL = import.meta.env.VITE_API_BASE_URL?.trim();
const API_BASE_URL = RAW_BASE_URL ? RAW_BASE_URL.replace(/\/+$/, '') : '';

export function apiFileUrl(fileId: string): string {
  return `${API_BASE_URL}/api/v1/files/${encodeURIComponent(fileId)}/download`;
}

export function isApiConfigured(): boolean {
  return Boolean(API_BASE_URL);
}

async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown };
    if (typeof body.detail === 'string') return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((d) => (typeof d === 'object' && d && 'msg' in d ? String((d as { msg: unknown }).msg) : String(d))).join('; ');
    }
  } catch {
    // response không phải JSON — bỏ qua, dùng statusText bên dưới
  }
  return res.statusText || `HTTP ${res.status}`;
}

async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const res = await fetch(`${API_BASE_URL}${path}`, init);
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res;
}

export async function uploadFile(file: File): Promise<ApiFileResponse> {
  const form = new FormData();
  form.append('file', file);
  const res = await apiFetch('/api/v1/files', { method: 'POST', body: form });
  return (await res.json()) as ApiFileResponse;
}

function toAttachedDocument(file: ApiFileResponse): AttachedDocument {
  const isPdf = file.content_type.includes('pdf');
  const isImage = file.content_type.startsWith('image/');
  return {
    id: file.id,
    fileName: file.original_name,
    icon: isPdf ? 'PDF' : isImage ? 'IMG' : 'DOC',
    docCategory: 'khac',
    uploadedAtLabel: 'vừa xong',
    contentType: file.content_type,
    previewUrl: apiFileUrl(file.id),
  };
}

const SSE_TIMEOUT_MS = 120_000;

type SsePayload = { status?: ApiJobResponse['status']; progress?: number; result?: unknown; error?: string };

function parseSsePayload(event: MessageEvent<string>): SsePayload {
  try {
    return JSON.parse(event.data) as SsePayload;
  } catch {
    return {};
  }
}

function streamJob<T>(jobId: string, onProgress?: (progress: number) => void): Promise<T> {
  return new Promise((resolve, reject) => {
    const url = `${API_BASE_URL}/api/v1/jobs/${encodeURIComponent(jobId)}/stream`;
    const es = new EventSource(url);
    const timeout = window.setTimeout(() => {
      es.close();
      reject(new Error('Quá thời gian chờ xử lý (2 phút) — vui lòng thử lại.'));
    }, SSE_TIMEOUT_MS);

    function finish(fn: () => void) {
      window.clearTimeout(timeout);
      es.close();
      fn();
    }

    es.addEventListener('snapshot', (event) => {
      const progress = parseSsePayload(event as MessageEvent<string>).progress;
      if (typeof progress === 'number') onProgress?.(progress);
    });
    es.addEventListener('progress', (event) => {
      const progress = parseSsePayload(event as MessageEvent<string>).progress;
      if (typeof progress === 'number') onProgress?.(progress);
    });
    es.addEventListener('done', (event) => {
      const result = parseSsePayload(event as MessageEvent<string>).result as T | undefined;
      finish(() => (result ? resolve(result) : reject(new Error('SSE done không có kết quả.'))));
    });
    es.addEventListener('error', (event) => {
      if (!('data' in event)) return; // Rớt mạng/proxy tạm thời — để EventSource tự nối lại, timeout vẫn chặn treo vô hạn.
      const message = parseSsePayload(event as MessageEvent<string>).error;
      finish(() => reject(new Error(message ?? 'Xử lý dữ liệu thất bại.')));
    });
  });
}

async function runService<T>(serviceId: string, input: Record<string, unknown>, onProgress?: (progress: number) => void): Promise<T> {
  const res = await apiFetch(`/api/v1/services/${serviceId}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ input }),
  });
  const body = (await res.json()) as ApiPluginRunAsyncResponse | ApiPluginRunResponse;

  if ('result' in body) return body.result as unknown as T;

  return streamJob<T>(body.job_id, onProgress);
}

/** Chạy plugin property_intake trên các file đã upload, nhận tiến độ qua SSE, trả kết quả trích xuất. */
export function runPropertyIntake(fileIds: string[], caseId: string, onProgress?: (progress: number) => void): Promise<ApiPropertyIntakeOutput> {
  return runService<ApiPropertyIntakeOutput>('property_intake', { file_ids: fileIds, language: 'vi', case_id: caseId }, onProgress);
}

export function runPropertyLookup(caseId: string, onProgress?: (progress: number) => void): Promise<ApiPropertyLookupOutput> {
  return runService<ApiPropertyLookupOutput>('property_lookup', { case_id: caseId }, onProgress);
}

export function runPropertyValuation(caseId: string, onProgress?: (progress: number) => void): Promise<ApiPropertyValuationOutput> {
  return runService<ApiPropertyValuationOutput>('property_valuation', { case_id: caseId }, onProgress);
}

export interface ExtractionResult {
  tab1Fields: Tab1Field[];
  docPages: DocPage[];
  warnings: string[];
}

/** Tiện ích gộp upload nhiều file + chạy trích xuất + map kết quả sang type UI dùng trực tiếp. */
export async function uploadAndExtract(files: File[], caseId: string): Promise<{ documents: AttachedDocument[] } & ExtractionResult> {
  const uploaded = await Promise.all(files.map((f) => uploadFile(f)));
  const documents = uploaded.map(toAttachedDocument);
  const output = await runPropertyIntake(uploaded.map((f) => f.id), caseId);
  const { tab1Fields, docPages } = mapPropertyIntakeOutput(output, documents);
  return { documents, tab1Fields, docPages, warnings: output.warnings ?? [] };
}
