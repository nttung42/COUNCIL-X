/* Tab 3 — Định giá (mockup screen 3, dòng ~388-414).
   4 stat-tile, barchart 3 phương pháp, sparkline SVG (logic drawSpark). */
import { useMemo } from 'react'
import { useCaseStore } from '../../state/caseStore'
import type { ValuationResult } from '../../types'
import { formatTrieu, formatTy, formatPct, NoData, QMark } from '../common/ui'

export function Tab3Valuation() {
  const { caseData } = useCaseStore()
  const v = caseData?.valuation
  if (!v) return <NoData label="Chưa có kết quả định giá — hãy bắt đầu thẩm định." />

  const series = v.price_index_series ?? caseData?.lookup_result?.market_price?.data?.price_index ?? []
  const lowData = v.comparables_used != null && v.comparables_used === 0

  return (
    <>
      <div className="grid c4">
        <StatTile label="Giá trị đề xuất" value={formatTy(v.estimated_value)} sub={rangeSub(v)} />
        <StatTile label="Giá/m²" value={formatTrieu(v.value_per_m2)} sub={v.time_adjustment_index_period ? `quy đổi ${v.time_adjustment_index_period}` : undefined} />
        <StatTile
          label="Độ tin cậy"
          why="Dựa trên số lượng và mức tương đồng của các giao dịch so sánh đã dùng."
          value={formatPct(v.confidence_score)}
          sub={v.comparables_used != null ? `${v.comparables_used} giao dịch dùng` : undefined}
          warn={lowData}
        />
        <StatTile
          label="Kỳ chỉ số giá"
          value={v.time_adjustment_index_period ?? '—'}
          sub={series.length ? `index ${series[series.length - 1].index} (gốc 100)` : undefined}
        />
      </div>

      {lowData && (
        <div className="card" style={{ marginBottom: 12, borderColor: 'rgba(208,59,59,0.4)' }}>
          <span className="badge critical">
            <span className="dot" />
            Không đủ dữ liệu so sánh
          </span>{' '}
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            Định giá độ tin cậy thấp — cần thẩm định viên xác minh thủ công.
          </span>
        </div>
      )}

      <div className="grid c2">
        <div className="card">
          <div className="section-h">
            3 phương pháp định giá
            <QMark why="Kết hợp so sánh trực tiếp, hedonic-ML và chi phí xây dựng để giảm sai lệch." />
          </div>
          <MethodBars v={v} />
        </div>
        <div className="card">
          <div className="section-h">Chỉ số giá theo thời gian</div>
          <Sparkline series={series} />
        </div>
      </div>

      {v.adjustment_notes && v.adjustment_notes.length > 0 && (
        <div className="card">
          <div className="section-h">Ghi chú điều chỉnh (explainability)</div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            {v.adjustment_notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </div>
      )}
    </>
  )
}

function rangeSub(v: ValuationResult): string | undefined {
  const lo = v.value_range?.low
  const hi = v.value_range?.high
  if (lo == null || hi == null) return undefined
  return `${formatTy(lo)}–${formatTy(hi)}`
}

function StatTile({
  label,
  value,
  sub,
  why,
  warn,
}: {
  label: string
  value: string
  sub?: string
  why?: string
  warn?: boolean
}) {
  return (
    <div className="card stat-tile">
      <div className="label">
        {label}
        {why && <QMark why={why} />}
      </div>
      <div className="value" style={warn ? { color: 'var(--critical)' } : undefined}>
        {value}
      </div>
      {sub && <div className="sub">{sub}</div>}
    </div>
  )
}

function MethodBars({ v }: { v: ValuationResult }) {
  const mb = v.methodology_breakdown
  const rows = [
    { label: 'So sánh trực tiếp', val: mb?.comparable_approach },
    { label: 'Hedonic (ML)', val: mb?.hedonic_model },
    { label: 'Chi phí xây dựng', val: mb?.cost_approach },
  ]
  const max = Math.max(...rows.map((r) => r.val ?? 0), 1)
  return (
    <div className="barchart">
      {rows.map((r) => (
        <div className="barrow" key={r.label}>
          <div className="rowlabel">{r.label}</div>
          <div className="bartrack">
            <div className="barfill" style={{ width: `${r.val ? (r.val / max) * 100 : 0}%` }} />
          </div>
          <div className="rowvalue">{r.val != null ? formatTy(r.val) : '—'}</div>
        </div>
      ))}
    </div>
  )
}

/* Sparkline — port của drawSpark() (mockup dòng ~519-536) sang React/useMemo. */
function Sparkline({ series }: { series: { period: string; index: number }[] }) {
  const geom = useMemo(() => {
    if (series.length < 2) return null
    const data = series.map((s) => s.index)
    const w = 300, h = 100, padX = 8, padTop = 10, padBottom = 12
    const min = Math.min(...data)
    const max = Math.max(...data)
    const span = max - min || 1
    const xStep = (w - padX * 2) / (data.length - 1)
    const pts = data.map((val, i) => {
      const x = padX + i * xStep
      const y = padTop + (1 - (val - min) / span) * (h - padTop - padBottom)
      return [x, y] as [number, number]
    })
    const lineStr = pts.map((p) => p.join(',')).join(' ')
    const areaStr = `${padX},${h - padBottom} ${lineStr} ${w - padX},${h - padBottom}`
    return { lineStr, areaStr, last: pts[pts.length - 1] }
  }, [series])

  if (!geom) return <NoData label="Không có chuỗi chỉ số giá." />

  return (
    <>
      <svg viewBox="0 0 300 100" width="100%" height={100} preserveAspectRatio="none">
        <polygon points={geom.areaStr} fill="var(--navy-600)" fillOpacity={0.1} stroke="none" />
        <polyline points={geom.lineStr} fill="none" stroke="var(--navy-600)" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        <circle cx={geom.last[0]} cy={geom.last[1]} r={4.5} fill="var(--orange-600)" stroke="var(--white)" strokeWidth={2} />
      </svg>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10.3, color: 'var(--text-muted)', marginTop: 4 }}>
        <span>
          {series[0].period} · {series[0].index.toFixed(1)}
        </span>
        <span>
          {series[series.length - 1].period} · {series[series.length - 1].index.toFixed(1)}
        </span>
      </div>
    </>
  )
}
