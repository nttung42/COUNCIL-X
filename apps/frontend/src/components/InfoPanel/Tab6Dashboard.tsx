/* Tab 6 — Dashboard / Trace thực thi PAA (mockup screen 6, dòng ~474-485).
   Timeline map từ mảng trace_events. */
import { useCaseStore } from '../../state/caseStore'
import type { TraceEvent } from '../../types'
import { NoData } from '../common/ui'

export function Tab6Dashboard() {
  const { caseData } = useCaseStore()
  const events = caseData?.trace_events ?? []
  const traceId = caseData?.trace_id ?? caseData?.request_id ?? '—'

  return (
    <div className="card">
      <div className="section-h">Trace thực thi PAA — {traceId}</div>
      {events.length === 0 ? (
        <NoData label="Chưa có trace event." />
      ) : (
        <div className="timeline">
          {events.map((e, i) => (
            <div className="tl-item" key={i}>
              <div className="tl-time">{formatOffset(e.t_offset_seconds)}</div>
              <div className="tl-rail">
                <div className="tl-dot" />
                <div className="tl-line" />
              </div>
              <div className="tl-body">
                <b>{e.step_name ?? <NoData />}</b>
                <p>{summaryOf(e)}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function formatOffset(s?: number): string {
  if (s == null) return '—'
  return `t+${s.toFixed(1)}s`
}

function summaryOf(e: TraceEvent): string {
  return e.output_summary || e.input_summary || e.component || ''
}
