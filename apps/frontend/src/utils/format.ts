/** Trích số thập phân đầu tiên trong 1 label hiển thị kiểu "4.90 tỷ" / "97.0 tr" -> 4.9 / 97.0. */
export function parseLeadingNumber(label: string): number {
  const match = label.replace(/,/g, '.').match(/-?\d+(\.\d+)?/);
  return match ? parseFloat(match[0]) : 0;
}

export function formatVndShort(value: number | null | undefined): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
  if (Math.abs(value) >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)} tỷ`;
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)} tr`;
  return value.toLocaleString('vi-VN');
}

export function formatNumber(value: number | null | undefined, digits = 1): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
  return value.toLocaleString('vi-VN', { maximumFractionDigits: digits });
}

export function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
