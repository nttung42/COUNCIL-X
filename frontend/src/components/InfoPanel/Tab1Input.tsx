/* Tab 1 — Nhập thông tin tài sản (mockup screen 1, dòng ~331-344).
   Không có case → form nhập; có case → hiển thị read-only snapshot. */
import { useState } from 'react'
import { actions, useCaseStore } from '../../state/caseStore'
import type { AppraisalRequestBody, LegalStatus, PropertyType } from '../../types'
import { formatVnd, NoData } from '../common/ui'

const PROPERTY_TYPES: { v: PropertyType; label: string }[] = [
  { v: 'nha_pho', label: 'Nhà phố (nhà trong hẻm)' },
  { v: 'dat_nen', label: 'Đất nền' },
  { v: 'chung_cu', label: 'Chung cư' },
  { v: 'bds_thuong_mai', label: 'BĐS thương mại' },
]
const LEGAL_STATUSES: { v: LegalStatus; label: string }[] = [
  { v: 'so_hong', label: 'Sổ hồng' },
  { v: 'so_do', label: 'Sổ đỏ' },
  { v: 'giay_tay', label: 'Giấy tay' },
  { v: 'khac', label: 'Khác' },
]

const propertyLabel = (v?: string) => PROPERTY_TYPES.find((p) => p.v === v)?.label ?? v ?? '—'
const legalLabel = (v?: string) => LEGAL_STATUSES.find((p) => p.v === v)?.label ?? v ?? '—'

export function Tab1Input() {
  const { caseData, caseId, streaming } = useCaseStore()

  if (caseData?.subject_property) {
    const sp = caseData.subject_property
    const lc = caseData.loan_context
    return (
      <div className="card">
        <div className="section-h">Thông tin tài sản cần thẩm định</div>
        <div className="grid c2" style={{ marginBottom: 0 }}>
          <ReadField label="Địa chỉ" value={sp.address} />
          <ReadField label="Loại BĐS" value={propertyLabel(sp.property_type)} />
          <ReadField label="Diện tích" value={sp.area_m2 ? `${sp.area_m2} m²` : undefined} />
          <ReadField label="Pháp lý (khai báo)" value={legalLabel(sp.legal_status_claimed)} />
          <ReadField label="Số tiền vay" value={lc?.requested_amount ? formatVnd(lc.requested_amount) : undefined} />
          <ReadField label="Mục đích vay" value={lc?.purpose === 'the_chap_vay_von' ? 'Thế chấp vay vốn' : lc?.purpose} />
        </div>
      </div>
    )
  }

  return <NewRequestForm disabled={!!caseId && streaming} />
}

function ReadField({ label, value }: { label: string; value?: string }) {
  return (
    <div className="field">
      <label>{label}</label>
      <div className="fake-input">{value || <NoData />}</div>
    </div>
  )
}

function NewRequestForm({ disabled }: { disabled: boolean }) {
  const [address, setAddress] = useState('Hẻm 45 Nguyễn Văn A, Phường B, Quận C')
  const [propertyType, setPropertyType] = useState<PropertyType>('nha_pho')
  const [areaM2, setAreaM2] = useState('62')
  const [legal, setLegal] = useState<LegalStatus>('so_hong')
  const [amount, setAmount] = useState('3200000000')
  const [purpose] = useState('the_chap_vay_von')

  const area = Number(areaM2)
  const amt = Number(amount)
  const valid = address.trim().length > 0 && area > 0 && amt > 0

  const submit = () => {
    if (!valid || disabled) return
    const body: AppraisalRequestBody = {
      request_id: `REQ-${Date.now()}`,
      subject_property: {
        address: address.trim(),
        lat: 10.7756,
        long: 106.7019,
        area_m2: area,
        property_type: propertyType,
        legal_status_claimed: legal,
      },
      loan_context: { requested_amount: amt, purpose },
    }
    void actions.createCase(body)
  }

  return (
    <div className="card">
      <div className="section-h">Thông tin tài sản cần thẩm định</div>
      <div className="grid c2" style={{ marginBottom: 0 }}>
        <div className="field">
          <label>Địa chỉ</label>
          <input className="fake-input" value={address} onChange={(e) => setAddress(e.target.value)} />
        </div>
        <div className="field">
          <label>Loại BĐS</label>
          <select className="fake-input" value={propertyType} onChange={(e) => setPropertyType(e.target.value as PropertyType)}>
            {PROPERTY_TYPES.map((p) => (
              <option key={p.v} value={p.v}>
                {p.label}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Diện tích (m²)</label>
          <input className="fake-input" type="number" min={1} value={areaM2} onChange={(e) => setAreaM2(e.target.value)} />
        </div>
        <div className="field">
          <label>Pháp lý (khai báo)</label>
          <select className="fake-input" value={legal} onChange={(e) => setLegal(e.target.value as LegalStatus)}>
            {LEGAL_STATUSES.map((p) => (
              <option key={p.v} value={p.v}>
                {p.label}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Số tiền vay (₫)</label>
          <input className="fake-input" type="number" min={1} value={amount} onChange={(e) => setAmount(e.target.value)} />
        </div>
        <div className="field">
          <label>Mục đích vay</label>
          <div className="fake-input">Thế chấp vay vốn</div>
        </div>
      </div>
      <button className="primary-btn" style={{ marginTop: 12 }} onClick={submit} disabled={!valid || disabled}>
        Bắt đầu thẩm định →
      </button>
      {!valid && (
        <div style={{ marginTop: 8, fontSize: 11, color: 'var(--critical)' }}>
          Cần địa chỉ, diện tích &gt; 0 và số tiền vay &gt; 0.
        </div>
      )}
    </div>
  )
}
