/* ============================================================================
   caseStore — state đồng bộ Chat ↔ Info Panel theo case đang mở (FR-011).
   Store vanilla + useSyncExternalStore (không thêm dependency).

   Luồng chính:
   - SSE step_update: append 1 message vào chatMessages (chat_message) VÀ set
     activeTab (active_tab). Người dùng vẫn bấm tay đổi tab sau đó (không khoá).
   - Chọn case khác từ Sidebar: đóng SSE cũ → GET /api/cases/{id} → mở SSE mới
     nếu status = processing.
   ============================================================================ */
import { useSyncExternalStore } from 'react'
import type {
  AppraisalReport,
  AppraisalRequestBody,
  CaseListItem,
  ChatMessage,
  StepUpdateEvent,
} from '../types'
import * as api from '../services/apiClient'

export type TabIndex = 1 | 2 | 3 | 4 | 5 | 6

export interface CaseState {
  caseId: string | null
  activeTab: TabIndex
  chatMessages: ChatMessage[]
  caseData: AppraisalReport | null
  loading: boolean
  error: string | null
  chatSending: boolean
  streaming: boolean
  caseList: CaseListItem[]
  listLoading: boolean
  mobilePane: 'chat' | 'info'
}

const initialState: CaseState = {
  caseId: null,
  activeTab: 1,
  chatMessages: [],
  caseData: null,
  loading: false,
  error: null,
  chatSending: false,
  streaming: false,
  caseList: [],
  listLoading: false,
  mobilePane: 'chat',
}

let state: CaseState = initialState
const listeners = new Set<() => void>()
let streamCleanup: (() => void) | null = null

function set(patch: Partial<CaseState>) {
  state = { ...state, ...patch }
  listeners.forEach((l) => l())
}

function subscribe(l: () => void) {
  listeners.add(l)
  return () => listeners.delete(l)
}

function getSnapshot() {
  return state
}

export function useCaseStore(): CaseState {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot)
}

function closeStream() {
  if (streamCleanup) {
    streamCleanup()
    streamCleanup = null
  }
}

function startStream(caseId: string) {
  closeStream()
  set({ streaming: true })
  streamCleanup = api.streamCase(caseId, {
    onStep: (e: StepUpdateEvent) => {
      if (e.chat_message) {
        const role = e.status === 'processing' && /đang|⏳/i.test(e.chat_message) ? 'status' : 'agent'
        appendMessage({ role, content: e.chat_message })
      }
      if (e.active_tab && e.active_tab >= 1 && e.active_tab <= 6) {
        set({ activeTab: e.active_tab as TabIndex })
      }
    },
    onError: () => {
      set({ streaming: false })
    },
    onDone: async () => {
      set({ streaming: false })
      // Pipeline xong → nạp state đầy đủ.
      try {
        const full = await api.getCase(caseId)
        if (state.caseId === caseId) set({ caseData: full })
      } catch {
        /* giữ nguyên state hiện có */
      }
      actions.refreshList()
    },
  })
}

function appendMessage(msg: ChatMessage) {
  set({ chatMessages: [...state.chatMessages, msg] })
}

function recapMessage(data: AppraisalReport): ChatMessage | null {
  const v = data.valuation
  const r = data.asset_risk
  if (!v && !r) return null
  const parts: string[] = []
  if (v?.estimated_value) {
    parts.push(
      `Định giá đề xuất ${formatTy(v.estimated_value)}${
        v.confidence_score != null ? `, độ tin cậy ${Math.round(v.confidence_score * 100)}%` : ''
      }.`,
    )
  }
  if (r?.asset_risk_score != null) {
    parts.push(
      `Điểm rủi ro BĐS ${r.asset_risk_score}/100${r.risk_tier ? ` (${tierVi(r.risk_tier)})` : ''}${
        r.recommended_ltv_cap != null ? `, LTV đề xuất ${Math.round(r.recommended_ltv_cap * 100)}%` : ''
      }.`,
    )
  }
  return { role: 'agent', content: parts.join(' ') }
}

function formatTy(vnd: number): string {
  return `${(vnd / 1e9).toFixed(2).replace(/\.?0+$/, '')} tỷ`
}
function tierVi(t: string): string {
  return t === 'LOW' ? 'Thấp' : t === 'HIGH' ? 'Cao' : 'Trung bình'
}

export const actions = {
  setActiveTab(tab: TabIndex) {
    set({ activeTab: tab })
  },

  setMobilePane(pane: 'chat' | 'info') {
    set({ mobilePane: pane })
  },

  async refreshList() {
    set({ listLoading: true })
    try {
      const list = await api.listCases()
      set({ caseList: list, listLoading: false })
    } catch {
      set({ listLoading: false })
    }
  },

  newRequest() {
    closeStream()
    set({
      caseId: null,
      caseData: null,
      chatMessages: [],
      activeTab: 1,
      error: null,
      streaming: false,
    })
  },

  async selectCase(caseId: string) {
    if (caseId === state.caseId) return
    closeStream()
    set({
      caseId,
      loading: true,
      error: null,
      caseData: null,
      chatMessages: [],
      streaming: false,
    })
    try {
      const data = await api.getCase(caseId)
      const msgs: ChatMessage[] = []
      const recap = recapMessage(data)
      if (recap) msgs.push(recap)
      set({
        caseData: data,
        loading: false,
        chatMessages: msgs,
        activeTab: data.status === 'completed' ? 2 : 1,
      })
      if (data.status === 'processing') startStream(caseId)
    } catch (err) {
      set({ loading: false, error: errMsg(err) })
    }
  },

  async createCase(body: AppraisalRequestBody) {
    closeStream()
    set({
      error: null,
      caseData: null,
      chatMessages: [
        {
          role: 'user',
          content: `Thẩm định giúp ${body.subject_property.address}${
            body.subject_property.area_m2 ? `, ${body.subject_property.area_m2}m²` : ''
          }${body.loan_context.requested_amount ? `, vay ${formatTy(body.loan_context.requested_amount)}` : ''}.`,
        },
      ],
      activeTab: 1,
    })
    try {
      const { case_id } = await api.createAppraisalRequest(body)
      set({ caseId: case_id })
      startStream(case_id)
      actions.refreshList()
    } catch (err) {
      set({ error: errMsg(err) })
      appendMessage({ role: 'status', content: `Lỗi tạo yêu cầu: ${errMsg(err)}` })
    }
  },

  async sendChat(content: string) {
    const trimmed = content.trim()
    if (!trimmed || !state.caseId) return
    appendMessage({ role: 'user', content: trimmed })
    set({ chatSending: true })
    try {
      const reply = await api.postMessage(state.caseId, trimmed)
      appendMessage(reply)
    } catch (err) {
      appendMessage({ role: 'status', content: `Không gửi được: ${errMsg(err)}` })
    } finally {
      set({ chatSending: false })
    }
  },

  async toggleChecklist(itemId: string, isChecked: boolean) {
    if (!state.caseId || !state.caseData?.checklist) return
    // optimistic
    const optimistic = state.caseData.checklist.map((c) =>
      c.item_id === itemId ? { ...c, is_checked: isChecked } : c,
    )
    set({ caseData: { ...state.caseData, checklist: optimistic } })
    try {
      const updated = await api.toggleChecklistItem(state.caseId, itemId, isChecked)
      const merged = (state.caseData?.checklist ?? []).map((c) =>
        c.item_id === itemId ? { ...c, ...updated } : c,
      )
      if (state.caseData) set({ caseData: { ...state.caseData, checklist: merged } })
    } catch {
      // rollback
      const rolledBack = (state.caseData?.checklist ?? []).map((c) =>
        c.item_id === itemId ? { ...c, is_checked: !isChecked } : c,
      )
      if (state.caseData) set({ caseData: { ...state.caseData, checklist: rolledBack } })
    }
  },
}

function errMsg(err: unknown): string {
  if (err instanceof api.ApiError) return err.message
  if (err instanceof Error) return err.message
  return 'Đã xảy ra lỗi không xác định.'
}
