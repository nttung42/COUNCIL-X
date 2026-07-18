/* ============================================================================
   apiClient — gọi PAA backend theo contracts/appraisal-api.md.

   USE_FIXTURE (VITE_USE_FIXTURE=true): trả dữ liệu mock cục bộ thay vì fetch
   thật, để phát triển UI song song khi Orchestrator & API chưa xong. Khi tích
   hợp API thật: đặt VITE_USE_FIXTURE=false — KHÔNG cần sửa signature/URL nào
   trong file này (URL & schema đã đúng contract).
   ============================================================================ */
import type {
  AppraisalReport,
  AppraisalRequestBody,
  CaseListItem,
  CaseStatus,
  ChatMessage,
  ChecklistItem,
  StepUpdateEvent,
} from '../types'
import {
  FIXTURE_CASE_ID,
  fixtureCase,
  fixtureCaseList,
  fixtureStepUpdates,
} from '../mocks/fixtureCase'

export const USE_FIXTURE =
  String(import.meta.env.VITE_USE_FIXTURE ?? '').toLowerCase() === 'true'

const BASE = '/api'

export class ApiError extends Error {
  status: number
  errorCode?: string
  fieldErrors?: unknown[]
  constructor(message: string, status: number, errorCode?: string, fieldErrors?: unknown[]) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.errorCode = errorCode
    this.fieldErrors = fieldErrors
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
  } catch {
    throw new ApiError('Không kết nối được máy chủ PAA. Backend có thể chưa sẵn sàng.', 0)
  }
  if (!res.ok) {
    let body: { error_code?: string; message?: string; field_errors?: unknown[] } = {}
    try {
      body = await res.json()
    } catch {
      /* ignore */
    }
    throw new ApiError(
      body.message || `Yêu cầu thất bại (${res.status})`,
      res.status,
      body.error_code,
      body.field_errors,
    )
  }
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms))

/* ---- contracts §1 ---- */
export async function createAppraisalRequest(
  body: AppraisalRequestBody,
): Promise<{ case_id: string; request_id: string; status: CaseStatus }> {
  if (USE_FIXTURE) {
    await delay(300)
    return { case_id: FIXTURE_CASE_ID, request_id: body.request_id, status: 'processing' }
  }
  return request('/appraisal-requests', { method: 'POST', body: JSON.stringify(body) })
}

/* ---- contracts §3 ---- */
export async function getCase(caseId: string): Promise<AppraisalReport> {
  if (USE_FIXTURE) {
    await delay(250)
    return { ...fixtureCase, case_id: caseId }
  }
  return request(`/cases/${encodeURIComponent(caseId)}`)
}

/* ---- contracts §4 ---- */
export async function listCases(status?: CaseStatus): Promise<CaseListItem[]> {
  if (USE_FIXTURE) {
    await delay(150)
    return status ? fixtureCaseList.filter((c) => c.status === status) : fixtureCaseList
  }
  const q = status ? `?status=${status}` : ''
  return request(`/cases${q}`)
}

/* ---- contracts §5 ---- */
export async function postMessage(caseId: string, content: string): Promise<ChatMessage> {
  if (USE_FIXTURE) {
    await delay(500)
    return {
      role: 'agent',
      content:
        'Theo quy trình thẩm định SHB, tài sản đang thế chấp nơi khác không đủ điều kiện nhận thế chấp mới cho đến khi giải chấp. Cần đối chiếu với tra cứu pháp lý (mục "Pháp lý" ở tab Kết quả tra cứu).',
      citations: [
        { source_doc: 'quy-trinh-tham-dinh.md', excerpt: 'Tài sản phải không bị thế chấp tại tổ chức tín dụng khác…' },
      ],
    }
  }
  return request(`/cases/${encodeURIComponent(caseId)}/messages`, {
    method: 'POST',
    body: JSON.stringify({ role: 'user', content }),
  })
}

/* ---- contracts §6 ---- */
export async function toggleChecklistItem(
  caseId: string,
  itemId: string,
  isChecked: boolean,
): Promise<ChecklistItem> {
  if (USE_FIXTURE) {
    await delay(200)
    const item = fixtureCase.checklist?.find((c) => c.item_id === itemId)
    return {
      item_id: itemId,
      text: item?.text ?? '',
      is_checked: isChecked,
      related_flag_type: item?.related_flag_type ?? null,
    }
  }
  return request(`/cases/${encodeURIComponent(caseId)}/checklist/${encodeURIComponent(itemId)}`, {
    method: 'PATCH',
    body: JSON.stringify({ is_checked: isChecked }),
  })
}

/* ---- contracts §7 ---- */
export async function cancelCase(caseId: string): Promise<{ status: CaseStatus }> {
  if (USE_FIXTURE) {
    await delay(200)
    return { status: 'cancelled' }
  }
  return request(`/cases/${encodeURIComponent(caseId)}/cancel`, { method: 'POST' })
}

/* ---- contracts §2 SSE stream ----
   Trả về hàm cleanup để đóng stream. USE_FIXTURE: phát lại fixtureStepUpdates
   theo thời gian để test đồng bộ chat ↔ info panel mà không cần backend. */
export function streamCase(
  caseId: string,
  handlers: {
    onStep: (e: StepUpdateEvent) => void
    onError?: (err: unknown) => void
    onDone?: () => void
  },
): () => void {
  if (USE_FIXTURE) {
    let cancelled = false
    const timers: ReturnType<typeof setTimeout>[] = []
    fixtureStepUpdates.forEach((evt, i) => {
      timers.push(
        setTimeout(() => {
          if (cancelled) return
          handlers.onStep(evt)
          if (i === fixtureStepUpdates.length - 1) handlers.onDone?.()
        }, 700 * (i + 1)),
      )
    })
    return () => {
      cancelled = true
      timers.forEach(clearTimeout)
    }
  }

  const es = new EventSource(`${BASE}/cases/${encodeURIComponent(caseId)}/stream`)
  es.addEventListener('step_update', (ev) => {
    try {
      const data = JSON.parse((ev as MessageEvent).data) as StepUpdateEvent
      handlers.onStep(data)
      if (data.status === 'completed' || data.status === 'cancelled') {
        es.close()
        handlers.onDone?.()
      }
    } catch (err) {
      handlers.onError?.(err)
    }
  })
  es.onerror = (err) => {
    handlers.onError?.(err)
    es.close()
  }
  return () => es.close()
}
