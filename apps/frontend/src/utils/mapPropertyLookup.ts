import type { LookupFinding, MarketComparable } from '../types';
import type { ApiPropertyLookupOutput } from '../services/apiTypes';
import { formatNumber, formatVndShort } from './format';

function formatDateLabel(value: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('vi-VN', { month: '2-digit', year: 'numeric' });
}

export function mapPropertyLookupOutput(output: ApiPropertyLookupOutput): {
  marketComparables: MarketComparable[];
  marketInferenceText: string;
  lookupFindings: LookupFinding[];
  warnings: string[];
} {
  const marketComparables = output.market_comparables.map((mc, index) => ({
    id: `mc-api-${index}`,
    compAddress: mc.address || '—',
    distanceKmLabel: mc.distance_km === null ? '—' : `${formatNumber(mc.distance_km)} km`,
    areaSqmLabel: mc.area_sqm === null ? '—' : `${formatNumber(mc.area_sqm)} m²`,
    transactionDateLabel: formatDateLabel(mc.transaction_date),
    pricePerSqmLabel: formatVndShort(mc.price_per_sqm_vnd),
  }));

  const lookupFindings = output.findings.map((f) => ({
    id: `lc-${f.category}`,
    category: f.category,
    toolName: f.tool_name,
    statusBadge: f.status_badge,
    title: f.title,
    rawFindings: f.raw_findings.length ? f.raw_findings : ['Chưa có dữ liệu tra cứu cho nguồn này.'],
    inferenceText: f.inference_text ?? 'Chưa có nhận định nghiệp vụ từ backend.',
    sourceLabel: f.source_label ?? f.tool_name,
    confidencePct: f.confidence_pct ?? 0,
  }));

  const marketFinding = lookupFindings.find((f) => f.category === 'market_price');
  const marketInferenceText = marketFinding?.inferenceText ?? 'Chưa có nhận định giá thị trường từ backend.';

  return { marketComparables, marketInferenceText, lookupFindings, warnings: output.warnings ?? [] };
}
