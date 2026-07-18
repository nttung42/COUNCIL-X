/* Tab 4 — Rủi ro (mockup screen 4, dòng ~417-446).
   2 meter (risk score, LTV), barchart 5 nhóm rủi ro, flag list. */
import { useCaseStore } from '../../state/caseStore'
import type { AssetRiskAssessment } from '../../types'
import {
  Badge,
  formatPct,
  NoData,
  QMark,
  riskColor,
  severityBadge,
  severityVi,
  tierBadge,
  tierVi,
} from '../common/ui'

const GROUP_META: { key: keyof NonNullable<AssetRiskAssessment['risk_group_scores']>; label: string; weight: string }[] = [
  { key: 'legal', label: 'Pháp lý', weight: '30%' },
  { key: 'liquidity', label: 'Thanh khoản', weight: '25%' },
  { key: 'price_volatility', label: 'Biến động giá', weight: '20%' },
  { key: 'physical_environmental', label: 'Vật lý/môi trường', weight: '15%' },
  { key: 'reputation_stigma', label: 'Danh tiếng/tâm linh', weight: '10%' },
]

export function Tab4Risk() {
  const { caseData } = useCaseStore()
  const r = caseData?.asset_risk
  if (!r) return <NoData label="Chưa có kết quả chấm điểm rủi ro — hãy bắt đầu thẩm định." />

  const score = r.asset_risk_score ?? 0
  const ltvPct = r.recommended_ltv_cap != null ? Math.round(r.recommended_ltv_cap * 100) : null

  return (
    <>
      <div className="grid c2">
        <div className="card">
          <div className="section-h">
            Điểm rủi ro bất động sản
            <QMark why="Tổng hợp có trọng số từ 5 nhóm rủi ro của chính tài sản — không phải rủi ro tín dụng người vay." />
          </div>
          <div className="meter-wrap">
            <div className="meter-track">
              <div className="meter-fill" style={{ width: `${score}%`, background: riskColor(score) }} />
            </div>
            <div className="meter-num">
              {r.asset_risk_score ?? <NoData />}
              <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 500 }}>/100</span>
            </div>
          </div>
          <div style={{ marginTop: 9 }}>
            <Badge kind={tierBadge(r.risk_tier)}>{tierVi(r.risk_tier)}</Badge>
          </div>
        </div>

        <div className="card">
          <div className="section-h">
            LTV đề xuất
            <QMark why="Trần cho vay trên giá trị định giá — dẫn xuất từ điểm rủi ro tài sản, không phải quyết định duyệt/từ chối." />
          </div>
          <div className="meter-wrap">
            <div className="meter-track">
              <div className="meter-fill" style={{ width: `${ltvPct ?? 0}%`, background: 'var(--navy-600)' }} />
            </div>
            <div className="meter-num">{ltvPct != null ? `${ltvPct}%` : <NoData />}</div>
          </div>
          <div className="sub" style={{ fontSize: 10.7, color: 'var(--text-muted)', marginTop: 9 }}>
            Trần cho vay trên giá trị định giá.
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 12 }}>
        <div className="section-h">5 nhóm rủi ro cấu thành</div>
        <div className="barchart">
          {GROUP_META.map((g) => {
            const val = r.risk_group_scores?.[g.key]
            return (
              <div className="barrow" key={g.key}>
                <div className="rowlabel">
                  {g.label} · {g.weight}
                </div>
                <div className="bartrack">
                  <div className="barfill" style={{ width: `${val ?? 0}%`, background: riskColor(val ?? 0) }} />
                </div>
                <div className="rowvalue">{val ?? '—'}</div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="card">
        <div className="section-h">Flags cần lưu ý</div>
        {(r.flags ?? []).length === 0 ? (
          <NoData label="Không có flag." />
        ) : (
          r.flags!.map((f, i) => {
            const isStigma = f.type === 'stigma' || f.verified === false
            return (
              <div className="flag-row" key={i}>
                <Badge kind={severityBadge(f.severity)}>{severityVi(f.severity)}</Badge>
                <div>
                  <b>{flagTitle(f.type)}</b>
                  <p>{f.detail ?? <NoData />}</p>
                  <div className="meta">
                    {f.confidence != null && `Độ tin cậy ${formatPct(f.confidence)} · `}
                    {isStigma ? 'Chưa xác thực' : 'Đã xác thực'}
                    {f.action && ` · ${f.action}`}
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>

      {r.recommended_conditions && r.recommended_conditions.length > 0 && (
        <div className="card">
          <div className="section-h">Điều kiện khuyến nghị</div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            {r.recommended_conditions.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}
    </>
  )
}

function flagTitle(type?: string): string {
  switch (type) {
    case 'legal':
      return 'Pháp lý'
    case 'stigma':
      return 'Danh tiếng / tâm linh'
    case 'environmental':
      return 'Môi trường'
    case 'liquidity':
      return 'Thanh khoản'
    case 'price_volatility':
      return 'Biến động giá'
    default:
      return type ?? 'Khác'
  }
}
