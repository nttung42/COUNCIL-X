import type { ValuationConfidenceFactor, ValuationMethod, ValuationPriceIndexPoint, ValuationResult } from '../types';
import type { ApiPropertyValuationOutput } from '../services/apiTypes';
import { escapeHtml, formatNumber, formatVndShort } from './format';

const METHOD_LABEL = {
  sales_comparison: 'So sánh trực tiếp',
  hedonic_ml: 'Hedonic (ML)',
  cost_approach: 'Chi phí xây dựng',
} as const;

export type MappedPropertyValuation =
  | { ok: false; warnings: string[] }
  | {
      ok: true;
      valuation: ValuationResult;
      priceIndexSeries: ValuationPriceIndexPoint[];
      valuationMethods: ValuationMethod[];
      valuationWeightedInferenceText: string;
      confidenceFactors: ValuationConfidenceFactor[];
      confidenceInferenceText: string;
      warnings: string[];
    };

function methodId(methodKey: string): string {
  return `lc-method-${methodKey.replace(/_/g, '-')}`;
}

function methodConfidence(weightPct: number, fallback: number | null): number {
  return fallback ?? Math.max(50, Math.min(95, Math.round(weightPct + 35)));
}

export function mapPropertyValuationOutput(output: ApiPropertyValuationOutput): MappedPropertyValuation {
  if (!output.valuation) {
    return { ok: false, warnings: output.warnings.length ? output.warnings : ['Backend chưa trả kết quả định giá cho hồ sơ này.'] };
  }

  const v = output.valuation;
  const valuation: ValuationResult = {
    proposedValueLabel: formatVndShort(v.proposed_value_vnd),
    valueRangeLabel: `${formatVndShort(v.value_range_low_vnd)}–${formatVndShort(v.value_range_high_vnd)}`,
    pricePerSqmLabel: formatVndShort(v.price_per_sqm_vnd),
    confidencePct: v.confidence_pct,
    comparableCount: v.comparable_count,
    priceIndexPeriod: v.price_index_period ?? '—',
    priceIndexValue: v.price_index_value ?? 100,
    priceIndexBase: v.price_index_base ?? 100,
  };

  const priceIndexSeries = [...output.price_index_series]
    .sort((a, b) => a.display_order - b.display_order)
    .map((p) => ({ periodLabel: p.period_label, indexValue: p.index_value }));

  const valuationMethods = output.methods.map((m) => ({
    id: methodId(m.method_key),
    methodKey: m.method_key,
    label: METHOD_LABEL[m.method_key] ?? m.method_key,
    estimatedValueLabel: formatVndShort(m.estimated_value_vnd),
    weightPct: m.weight_pct,
    contributionValueLabel: formatVndShort(m.contribution_value_vnd),
    methodConfidencePct: methodConfidence(m.weight_pct, m.method_confidence_pct),
    inputs: m.inputs.length ? m.inputs : ['Backend chưa trả chi tiết dữ liệu đầu vào.'],
    inferenceText: m.inference_text ?? `Phương pháp ${METHOD_LABEL[m.method_key] ?? m.method_key} đóng góp ${m.weight_pct}% vào giá trị đề xuất.`,
    sourceLabel: m.source_label ?? METHOD_LABEL[m.method_key] ?? m.method_key,
  }));

  const confidenceFactors = output.confidence_factors.map((f) => ({
    factorKey: f.factor_key,
    label: f.label,
    weightPct: f.weight_pct,
    score: f.score,
  }));

  const methodSummary = valuationMethods
    .map((m) => `<b>${escapeHtml(m.label)} (${m.weightPct}%)</b>: ${escapeHtml(m.estimatedValueLabel)}`)
    .join(' · ');
  const subjective = output.subjective_adjustment
    ? ` Điều chỉnh cảm tính LLM: <b>${formatNumber(output.subjective_adjustment.value_pct)}%</b> (${escapeHtml(output.subjective_adjustment.reason)}).`
    : '';
  const valuationWeightedInferenceText = methodSummary
    ? `${methodSummary}.${subjective}`
    : 'Backend chưa trả chi tiết 3 phương pháp định giá.';

  const confidenceInferenceText =
    v.confidence_inference_text ??
    `Độ tin cậy tổng <b>${v.confidence_pct}%</b>, tính từ ${confidenceFactors.length} yếu tố: ${confidenceFactors
      .map((f) => `${escapeHtml(f.label)} ${f.score}/100`)
      .join(' · ')}.`;

  return {
    ok: true,
    valuation,
    priceIndexSeries,
    valuationMethods,
    valuationWeightedInferenceText,
    confidenceFactors,
    confidenceInferenceText,
    warnings: output.warnings ?? [],
  };
}
