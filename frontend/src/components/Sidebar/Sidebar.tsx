/* Sidebar — nav + "Yêu cầu thẩm định mới" + Lịch sử hồ sơ.
   Cấu trúc theo PAA_Mockup_SHB.html .sidebar (dòng ~250-287).
   dot màu theo status: good=hoàn tất, warning=đang xử lý, text-muted=huỷ. */
import { useEffect } from 'react'
import { actions, useCaseStore } from '../../state/caseStore'
import type { CaseStatus } from '../../types'

function statusDot(status: CaseStatus): string {
  if (status === 'completed') return 'var(--good)'
  if (status === 'processing') return 'var(--warning)'
  return 'var(--text-muted)'
}

function statusLabel(status: CaseStatus): string {
  if (status === 'completed') return 'Hoàn tất'
  if (status === 'processing') return 'Đang xử lý'
  return 'Huỷ'
}

function relTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  const diff = Date.now() - d.getTime()
  const day = Math.floor(diff / 86400000)
  if (day <= 0) return 'hôm nay'
  if (day === 1) return 'hôm qua'
  if (day < 7) return `${day} ngày trước`
  return `${Math.floor(day / 7)} tuần trước`
}

export function Sidebar() {
  const { caseId, caseList, listLoading } = useCaseStore()

  useEffect(() => {
    actions.refreshList()
  }, [])

  return (
    <div className="sidebar">
      <div className="sb-brand">
        <div className="mark">SHB</div>
        <div className="name txt-hide">
          PAA Workspace
          <small>Digital Expert Agent</small>
        </div>
      </div>

      <div className="sb-section" style={{ paddingBottom: 0 }}>
        <div className="nav-item active">
          <span className="ic">🏠</span>
          <span className="txt-hide">Thẩm định BĐS</span>
        </div>
        <div className="nav-item disabled">
          <span className="ic">💳</span>
          <span className="txt-hide">Credit Agent</span>
          <span className="soon txt-hide">sắp có</span>
        </div>
        <div className="nav-item disabled">
          <span className="ic">⚖️</span>
          <span className="txt-hide">Legal/Compliance</span>
          <span className="soon txt-hide">sắp có</span>
        </div>
      </div>

      <div className="sb-divider" />

      <div className="sb-section" style={{ paddingBottom: 0 }}>
        <button className="new-req-btn" onClick={() => actions.newRequest()}>
          ＋ <span className="txt-hide">Yêu cầu thẩm định mới</span>
        </button>
        <div className="sb-label txt-hide">Lịch sử hồ sơ</div>
      </div>

      <div className="history-list">
        {listLoading && caseList.length === 0 && (
          <div className="sb-empty txt-hide">
            <span className="spinner" />
            Đang tải…
          </div>
        )}
        {!listLoading && caseList.length === 0 && (
          <div className="sb-empty txt-hide">Chưa có hồ sơ nào.</div>
        )}
        {caseList.map((c) => (
          <div
            key={c.case_id}
            className={`history-item${c.case_id === caseId ? ' active' : ''}`}
            onClick={() => actions.selectCase(c.case_id)}
          >
            <div className="addr">{c.address}</div>
            <div className="meta">
              <span className="dot" style={{ background: statusDot(c.status) }} />
              <span className="date">
                {statusLabel(c.status)} · {relTime(c.updated_at)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
