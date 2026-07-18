/* ChatPane 30% — 3 loại message (.msg.agent / .msg.user / .msg.status).
   Cấu trúc theo PAA_Mockup_SHB.html .chat-pane (dòng ~298-315). */
import { useEffect, useRef, useState } from 'react'
import { actions, useCaseStore } from '../../state/caseStore'
import type { ChatMessage } from '../../types'

function whoLabel(role: ChatMessage['role']): string {
  return role === 'user' ? 'Bạn' : 'PAA'
}

export function ChatPane() {
  const { caseId, caseData, chatMessages, chatSending, streaming } = useCaseStore()
  const [draft, setDraft] = useState('')
  const threadRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight, behavior: 'smooth' })
  }, [chatMessages, streaming])

  const canSend = !!caseId && !chatSending && draft.trim().length > 0
  const subtitle = caseData?.subject_property?.address ?? (caseId ? '' : 'Chưa chọn hồ sơ')

  const submit = () => {
    if (!canSend) return
    const text = draft
    setDraft('')
    void actions.sendChat(text)
  }

  return (
    <div className="chat-pane">
      <div className="pane-head">
        <div className="title">Trò chuyện với PAA</div>
        <div className="sub">{subtitle}</div>
      </div>

      <div className="chat-thread" ref={threadRef}>
        {chatMessages.length === 0 && !streaming && (
          <div className="msg status">
            Nhập thông tin tài sản ở tab 1 rồi bấm “Bắt đầu thẩm định”, hoặc chọn 1 hồ sơ từ lịch sử.
          </div>
        )}
        {chatMessages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.role !== 'status' && <div className="who">{whoLabel(m.role)}</div>}
            {m.content}
            {m.citations?.map((c, j) => (
              <span className="cite" key={j}>
                📎 {c.source_doc ?? 'nguồn'} {c.excerpt ? `— “${c.excerpt}”` : ''}
              </span>
            ))}
          </div>
        ))}
        {streaming && <div className="msg status">⏳ PAA đang xử lý…</div>}
        {chatSending && <div className="msg status">PAA đang soạn câu trả lời…</div>}
      </div>

      <div className="chat-input-bar">
        <input
          className="chat-input"
          placeholder={caseId ? 'Nhập câu hỏi hoặc yêu cầu cho PAA…' : 'Chọn/tạo hồ sơ để bắt đầu chat…'}
          value={draft}
          disabled={!caseId}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') submit()
          }}
        />
        <button className="chat-send" onClick={submit} disabled={!canSend} aria-label="Gửi">
          ➤
        </button>
      </div>
    </div>
  )
}
