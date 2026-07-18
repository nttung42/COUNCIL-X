/* Tab 5 — Checklist động + nháp biên bản (mockup screen 5, dòng ~449-471).
   Toggle gọi API PATCH (contracts §6) qua store, không chỉ toggle class cục bộ. */
import { actions, useCaseStore } from '../../state/caseStore'
import type { DraftReport } from '../../types'
import { NoData, QMark } from '../common/ui'

export function Tab5Checklist() {
  const { caseData } = useCaseStore()
  const checklist = caseData?.checklist
  const draft = caseData?.draft_report

  if (!checklist && !draft) return <NoData label="Chưa có checklist / nháp biên bản." />

  return (
    <div className="grid c2">
      <div className="card">
        <div className="section-h">Checklist động</div>
        <div className="checklist">
          {(checklist ?? []).length === 0 && <NoData label="Chưa có mục checklist." />}
          {(checklist ?? []).map((item) => (
            <div
              key={item.item_id}
              className={`check-item${item.is_checked ? ' checked' : ''}`}
              onClick={() => actions.toggleChecklist(item.item_id, !item.is_checked)}
            >
              <div className="checkbox">
                <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={3}>
                  <path d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div className="check-text">{item.text}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="section-h">
          Nháp biên bản thẩm định
          <QMark why="Sinh tự động từ RAG + kết quả định giá/rủi ro — thẩm định viên chỉnh sửa trước khi ký." />
        </div>
        <DraftDoc draft={draft} />
      </div>
    </div>
  )
}

function DraftDoc({ draft }: { draft?: DraftReport }) {
  if (!draft) return <NoData label="Chưa sinh nháp biên bản." />
  const s = draft.sections
  return (
    <div className="report-doc">
      <h4>1. Thông tin tài sản</h4>
      <p>{s?.property_info ?? <NoData />}</p>
      <h4>2. Định giá</h4>
      <p>{s?.valuation ?? <NoData />}</p>
      <h4>3. Rủi ro &amp; LTV</h4>
      <p>{s?.risk_and_ltv ?? <NoData />}</p>
      <div className="sig">{draft.signature_block ?? '☐ Chữ ký thẩm định viên      ☐ Xác nhận chuyên viên tín dụng'}</div>
    </div>
  )
}
