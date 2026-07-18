import type { AttachedDocument, DocPage, Tab1Field } from '../types';
import { mapPropertyIntakeOutput } from '../utils/mapPropertyIntake';
import type {
  ApiFileResponse,
  ApiJobResponse,
  ApiPluginRunAsyncResponse,
  ApiPluginRunResponse,
  ApiPropertyIntakeOutput,
  ApiRegisterResponse,
} from './apiTypes';

// Client cho backend thật ở ai/ (FastAPI, xem ai/src/shb/main.py + ai/src/shb/api/v1/api.py).
// Hiện backend mới có route cho auth/upload-file/chạy-service-bất-đồng-bộ/poll-job — CHƯA có
// route riêng cho case/lookup/valuation/risk/dashboard/chat (những bảng đó mới chỉ là ORM model,
// xem models_paa.py). Vì vậy chỉ màn "Nhập thông tin" (property_intake) gọi API thật; các màn
// 2-5 + chat + xác nhận chỉnh sửa vẫn dùng fixtureCase cho tới khi backend có endpoint tương ứng.

const RAW_BASE_URL = import.meta.env.VITE_API_BASE_URL?.trim();
const API_BASE_URL = RAW_BASE_URL ? RAW_BASE_URL.replace(/\/+$/, '') : '';

export function isApiConfigured(): boolean {
  return Boolean(API_BASE_URL);
}

const API_KEY_STORAGE = 'paa_api_key';
const API_EMAIL_STORAGE = 'paa_api_email';

function randomId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
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

let apiKeyPromise: Promise<string> | null = null;

/** Đăng ký (1 lần, email ngẫu nhiên) hoặc tái sử dụng X-API-Key đã lưu ở localStorage. */
async function ensureApiKey(): Promise<string> {
  const cached = localStorage.getItem(API_KEY_STORAGE);
  if (cached) return cached;

  if (!apiKeyPromise) {
    apiKeyPromise = (async () => {
      let email = localStorage.getItem(API_EMAIL_STORAGE);
      if (!email) {
        email = `paa-frontend+${randomId()}@local.paa`;
        localStorage.setItem(API_EMAIL_STORAGE, email);
      }
      const res = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) throw new Error(`Không đăng ký được tài khoản API: ${await parseErrorDetail(res)}`);
      const data = (await res.json()) as ApiRegisterResponse;
      localStorage.setItem(API_KEY_STORAGE, data.api_key);
      return data.api_key;
    })();
  }
  return apiKeyPromise;
}

async function authedFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const apiKey = await ensureApiKey();
  const headers = new Headers(init.headers);
  headers.set('X-API-Key', apiKey);
  const res = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (!res.ok) throw new Error(await parseErrorDetail(res));
  return res;
}

export async function uploadFile(file: File): Promise<ApiFileResponse> {
  const form = new FormData();
  form.append('file', file);
  const res = await authedFetch('/api/v1/files', { method: 'POST', body: form });
  return (await res.json()) as ApiFileResponse;
}

function toAttachedDocument(file: ApiFileResponse): AttachedDocument {
  const isPdf = file.content_type.includes('pdf');
  const isImage = file.content_type.startsWith('image/');
  return {
    id: file.id,
    fileName: file.original_name,
    icon: isPdf ? '📜' : isImage ? '📷' : '📄',
    docCategory: 'khac',
    uploadedAtLabel: 'vừa xong',
  };
}

const POLL_TIMEOUT_MS = 120_000;

/** Trích xuất bằng LLM thường mất 10–60s — poll nhanh lúc đầu, giãn dần để đỡ dồn request. */
function nextPollDelayMs(elapsedMs: number): number {
  if (elapsedMs < 10_000) return 1500;
  if (elapsedMs < 30_000) return 3000;
  return 5000;
}

async function pollJob(jobId: string): Promise<ApiJobResponse> {
  const startedAt = Date.now();
  for (;;) {
    const res = await authedFetch(`/api/v1/jobs/${jobId}`);
    const job = (await res.json()) as ApiJobResponse;
    if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') return job;
    const elapsed = Date.now() - startedAt;
    if (elapsed > POLL_TIMEOUT_MS) {
      throw new Error('Quá thời gian chờ trích xuất dữ liệu (2 phút) — vui lòng thử lại.');
    }
    // eslint-disable-next-line no-await-in-loop
    await new Promise((resolve) => setTimeout(resolve, nextPollDelayMs(elapsed)));
  }
}

/** Chạy plugin property_intake trên các file đã upload, đợi job xong, trả kết quả trích xuất. */
export async function runPropertyIntake(fileIds: string[], caseId: string): Promise<ApiPropertyIntakeOutput> {
  const res = await authedFetch('/api/v1/services/property_intake/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ input: { file_ids: fileIds, language: 'vi', case_id: caseId } }),
  });
  const body = (await res.json()) as ApiPluginRunAsyncResponse | ApiPluginRunResponse;

  if ('result' in body) return body.result as unknown as ApiPropertyIntakeOutput;

  const job = await pollJob(body.job_id);
  if (job.status !== 'completed') throw new Error(job.error ?? 'Trích xuất dữ liệu thất bại.');
  return job.result as unknown as ApiPropertyIntakeOutput;
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
  const { tab1Fields, docPages } = mapPropertyIntakeOutput(output);
  return { documents, tab1Fields, docPages, warnings: output.warnings ?? [] };
}
