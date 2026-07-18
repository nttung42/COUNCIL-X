/** Trích số thập phân đầu tiên trong 1 label hiển thị kiểu "4.90 tỷ" / "97.0 tr" -> 4.9 / 97.0. */
export function parseLeadingNumber(label: string): number {
  const match = label.replace(/,/g, '.').match(/-?\d+(\.\d+)?/);
  return match ? parseFloat(match[0]) : 0;
}
