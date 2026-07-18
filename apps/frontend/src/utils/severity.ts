import type { SeverityLevel } from '../types';

export type Tone = 'good' | 'warning' | 'serious' | 'critical';

export const SEVERITY_LABEL: Record<SeverityLevel, string> = {
  thap: 'Thấp',
  trung_binh: 'Trung bình',
  cao: 'Cao',
  nghiem_trong: 'Nghiêm trọng',
};

export const SEVERITY_TONE: Record<SeverityLevel, Tone> = {
  thap: 'good',
  trung_binh: 'warning',
  cao: 'serious',
  nghiem_trong: 'critical',
};

export const TONE_COLOR: Record<Tone, string> = {
  good: 'var(--good)',
  warning: 'var(--warning)',
  serious: 'var(--serious)',
  critical: 'var(--critical)',
};

/** Điểm rủi ro (0-100, càng thấp càng tốt) -> tông màu, dùng cho 5 nhóm rủi ro cấu thành. */
export function riskScoreTone(score: number): Tone {
  if (score <= 20) return 'good';
  if (score <= 40) return 'warning';
  return 'serious';
}

/** Điểm độ tin cậy / % (0-100, càng cao càng tốt) -> tông màu, dùng cho các yếu tố cấu thành độ tin cậy định giá. */
export function confidenceScoreTone(score: number): Tone {
  if (score >= 80) return 'good';
  if (score >= 60) return 'warning';
  return 'serious';
}

/** Độ tin cậy phương pháp định giá (%) -> tông màu badge. */
export function methodConfidenceTone(pct: number): Tone {
  if (pct >= 75) return 'good';
  if (pct >= 60) return 'warning';
  return 'serious';
}
