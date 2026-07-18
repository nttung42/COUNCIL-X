/* ============================================================================
   Shared UI atoms — pattern .qmark tooltip (Nguyên tắc II/III: mọi số liệu kèm
   nguồn/độ tin cậy), badge, và các formatter tiền tệ/độ tin cậy dùng chung.
   ============================================================================ */
import type { ReactNode } from 'react'
import type { SourceType } from '../../types'

/** Dấu ? tooltip giải thích nguồn/độ tin cậy — bọc mọi số liệu định giá/rủi ro. */
export function QMark({ why }: { why: string }) {
  return (
    <span className="qmark" data-why={why} aria-label={why} role="img">
      ?
    </span>
  )
}

export type BadgeKind = 'good' | 'warning' | 'serious' | 'critical'

export function Badge({ kind, children }: { kind: BadgeKind; children: ReactNode }) {
  return (
    <span className={`badge ${kind}`} style={{ flex: 'none' }}>
      <span className="dot" />
      {children}
    </span>
  )
}

/** "chưa có dữ liệu" khi field thiếu (Error Handling) — không render số trần trụi. */
export function NoData({ label = 'chưa có dữ liệu' }: { label?: string }) {
  return <span className="nodata">{label}</span>
}

/* ---------- formatters ---------- */

/** 4850000000 → "4.85 tỷ" */
export function formatTy(vnd?: number | null): string {
  if (vnd == null || Number.isNaN(vnd)) return '—'
  return `${(vnd / 1e9).toFixed(2).replace(/\.?0+$/, '')} tỷ`
}

/** 97000000 → "97.0 tr" */
export function formatTrieu(vnd?: number | null): string {
  if (vnd == null || Number.isNaN(vnd)) return '—'
  return `${(vnd / 1e6).toFixed(1)} tr`
}

/** 0.78 → "78%" */
export function formatPct(x?: number | null): string {
  if (x == null || Number.isNaN(x)) return '—'
  return `${Math.round(x * 100)}%`
}

/** 3200000000 → "3.200.000.000 ₫" */
export function formatVnd(vnd?: number | null): string {
  if (vnd == null || Number.isNaN(vnd)) return '—'
  return `${vnd.toLocaleString('vi-VN')} ₫`
}

/** "2025-11-01" → "11/2025" */
export function formatMonthYear(iso?: string): string {
  if (!iso) return '—'
  const m = /^(\d{4})-(\d{2})/.exec(iso)
  return m ? `${m[2]}/${m[1]}` : iso
}

export function tierVi(t?: string): string {
  if (t === 'LOW') return 'THẤP'
  if (t === 'HIGH') return 'CAO'
  if (t === 'MEDIUM') return 'TRUNG BÌNH'
  return '—'
}

export function tierBadge(t?: string): BadgeKind {
  if (t === 'LOW') return 'good'
  if (t === 'HIGH') return 'critical'
  return 'warning'
}

export function severityVi(s?: string): string {
  if (s === 'low') return 'Thấp'
  if (s === 'high') return 'Cao'
  if (s === 'medium') return 'Trung bình'
  return '—'
}

export function severityBadge(s?: string): BadgeKind {
  if (s === 'low') return 'good'
  if (s === 'high') return 'critical'
  return 'warning'
}

/** Nhãn nguồn dữ liệu để tooltip/label — phân biệt đã xác thực vs tin đồn. */
export function sourceLabel(source?: SourceType, confidence?: number): string {
  const pct = confidence != null ? ` · Độ tin cậy ${Math.round(confidence * 100)}%` : ''
  if (source === 'verified') return `Nguồn: dữ liệu đã xác thực${pct}`
  if (source === 'unverified_rumor') return `Nguồn: tin đồn CHƯA kiểm chứng${pct} — chỉ tham khảo, không dùng để từ chối hồ sơ`
  return `Nguồn: dữ liệu mô phỏng (mock)${pct}`
}

/** Màu bar theo giá trị điểm rủi ro 0..100 (khớp ngưỡng mockup). */
export function riskColor(score: number): string {
  if (score <= 30) return 'var(--good)'
  if (score <= 55) return 'var(--warning)'
  if (score <= 70) return 'var(--serious)'
  return 'var(--critical)'
}
