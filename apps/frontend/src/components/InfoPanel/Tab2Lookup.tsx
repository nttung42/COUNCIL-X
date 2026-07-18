/* Tab 2 — Kết quả tra cứu (mockup screen 2, dòng ~347-385).
   NGUYÊN TẮC III: dữ liệu đã xác thực (badge xanh "Đã xác thực") và tin đồn/tâm
   linh CHƯA xác thực (badge vàng "Chưa xác thực") PHẢI ở khối UI tách biệt rõ ràng
   — không trộn lẫn. stigma render trong 1 card RIÊNG với cảnh báo. */
import { useCaseStore } from '../../state/caseStore'
import type { LookupResult } from '../../types'
import { Badge, formatMonthYear, formatTrieu, NoData, QMark, sourceLabel } from '../common/ui'

export function Tab2Lookup() {
  const { caseData } = useCaseStore()
  const lr = caseData?.lookup_result
  if (!lr) return <NoData label="Chưa có kết quả tra cứu — hãy bắt đầu thẩm định." />
  return (
    <>
      <ComparablesCard lr={lr} />
      <div className="grid c3">
        <ZoningCard lr={lr} />
        <LegalCard lr={lr} />
        <AmenityCard lr={lr} />
        <EnvironmentCard lr={lr} />
        <LiquidityCard lr={lr} />
        {/* stigma — card RIÊNG BIỆT, badge warning "Chưa xác thực" */}
        <StigmaCard lr={lr} />
      </div>
    </>
  )
}

function ComparablesCard({ lr }: { lr: LookupResult }) {
  const mp = lr.market_price
  const rows = mp?.data?.comparables ?? lr.comparables ?? []
  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <div className="section-h">
        Giao dịch so sánh khu vực
        <QMark why={sourceLabel(mp?.source_type, mp?.confidence) + ' — trong bán kính ~1.1km, đã quy đổi theo chỉ số giá hiện hành.'} />
      </div>
      {rows.length === 0 ? (
        <NoData label="Không có giao dịch so sánh trong khu vực." />
      ) : (
        <table>
          <tbody>
            <tr>
              <th>Địa chỉ</th>
              <th>Cách</th>
              <th>DT</th>
              <th>Ngày GD</th>
              <th>Giá/m²</th>
            </tr>
            {rows.map((r, i) => (
              <tr key={r.transaction_id ?? i}>
                <td>{r.address ?? <NoData />}</td>
                <td>{r.distance_from_subject_km != null ? `${r.distance_from_subject_km} km` : <NoData />}</td>
                <td>{r.area_m2 != null ? `${r.area_m2} m²` : <NoData />}</td>
                <td>{formatMonthYear(r.transaction_date)}</td>
                <td className="strong">{formatTrieu(r.price_per_m2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

function ZoningCard({ lr }: { lr: LookupResult }) {
  const z = lr.planning_zoning
  return (
    <div className="card lookup-card">
      <div className="headline">
        <Badge kind="good">Đã xác thực</Badge> Quy hoạch
        <QMark why={sourceLabel(z?.source_type, z?.confidence)} />
      </div>
      <p>{z?.data?.zoning_status ?? <NoData />}</p>
    </div>
  )
}

function LegalCard({ lr }: { lr: LookupResult }) {
  const l = lr.legal_status
  return (
    <div className="card lookup-card">
      <div className="headline">
        <Badge kind="good">Đã xác thực</Badge> Pháp lý
        <QMark why={sourceLabel(l?.source_type, l?.confidence)} />
      </div>
      <p>{l?.data?.legal_status ?? <NoData />}</p>
    </div>
  )
}

function AmenityCard({ lr }: { lr: LookupResult }) {
  const a = lr.neighborhood_amenity?.data?.amenities ?? []
  return (
    <div className="card lookup-card">
      <div className="headline">Tiện ích xung quanh</div>
      <p>
        {a.length === 0 ? (
          <NoData />
        ) : (
          a.map((am, i) => (
            <span key={i}>
              {i > 0 && ' · '}
              {am.name}
              {am.distance_m != null && ` ${am.distance_m >= 1000 ? `${(am.distance_m / 1000).toFixed(1)}km` : `${am.distance_m}m`}`}
            </span>
          ))
        )}
      </p>
    </div>
  )
}

function EnvironmentCard({ lr }: { lr: LookupResult }) {
  const e = lr.environmental_risk
  return (
    <div className="card lookup-card">
      <div className="headline">
        <Badge kind="warning">lưu ý</Badge> Môi trường
        <QMark why={sourceLabel(e?.source_type, e?.confidence)} />
      </div>
      <p>{e?.data?.notes ?? <NoData />}</p>
    </div>
  )
}

function LiquidityCard({ lr }: { lr: LookupResult }) {
  const li = lr.liquidity_stat?.data
  return (
    <div className="card lookup-card">
      <div className="headline">Thanh khoản khu vực</div>
      <p>
        {li ? (
          <>
            Bán TB <b style={{ color: 'var(--ink)' }}>{li.avg_days_on_market ?? '—'} ngày</b> · Tỷ lệ thành công{' '}
            <b style={{ color: 'var(--ink)' }}>{li.success_rate_pct ?? '—'}%</b>
          </>
        ) : (
          <NoData />
        )}
      </p>
    </div>
  )
}

/* Card RIÊNG BIỆT cho tin đồn/tâm linh — badge warning "Chưa xác thực".
   Tuyệt đối không gộp chung UI với card pháp lý/quy hoạch (Nguyên tắc III). */
function StigmaCard({ lr }: { lr: LookupResult }) {
  const s = lr.stigma_reputation
  const rumors = s?.data?.rumors ?? []
  return (
    <div className="card lookup-card" style={{ borderColor: 'rgba(250,178,25,0.5)', background: 'var(--warning-tint)' }}>
      <div className="headline">
        <Badge kind="warning">Chưa xác thực</Badge> Dư luận/tâm linh
        <QMark
          why={
            sourceLabel(s?.source_type ?? 'unverified_rumor', s?.confidence) +
            '. KHÔNG dùng để từ chối hồ sơ, chỉ mang tính cảnh báo tham khảo.'
          }
        />
      </div>
      {rumors.length === 0 ? (
        <p>
          <NoData label="Không ghi nhận tin đồn." />
        </p>
      ) : (
        rumors.map((r, i) => (
          <p key={i}>
            {r.detail ?? <NoData />}
            {r.year ? ` (${r.year})` : ''}
          </p>
        ))
      )}
      {s?.warning && <div className="src" style={{ color: '#8a6100' }}>⚠ {s.warning}</div>}
    </div>
  )
}
