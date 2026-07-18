import type { RiskAssessmentResult, RiskFlag, RiskGroup, RiskLtvPolicyBand } from '../types';
import type { ApiPropertyRiskOutput } from '../services/apiTypes';
import { escapeHtml } from './format';

const GROUP_TOOL_NAME = {
  legal: 'legal_status_lookup',
  liquidity: 'liquidity_stat_lookup',
  price_volatility: 'market_price_lookup',
  physical_environment: 'environmental_risk_lookup',
  reputation: 'stigma_reputation_lookup',
} as const;

export type MappedPropertyRisk =
  | { ok: false; warnings: string[] }
  | {
      ok: true;
      risk: RiskAssessmentResult;
      ltvPolicyBands: RiskLtvPolicyBand[];
      ltvPolicyInferenceText: string;
      riskGroups: RiskGroup[];
      riskWeightedInferenceText: string;
      riskFlags: RiskFlag[];
      warnings: string[];
    };

function groupId(groupKey: string): string {
  return `rc-${groupKey.replace(/_/g, '-')}`;
}

function currentLtvBand(bands: RiskLtvPolicyBand[], score: number): RiskLtvPolicyBand | undefined {
  return bands.find((b) => score >= b.minScore && (b.maxScore === null || score <= b.maxScore));
}

export function mapPropertyRiskOutput(output: ApiPropertyRiskOutput): MappedPropertyRisk {
  if (!output.assessment) {
    return { ok: false, warnings: output.warnings.length ? output.warnings : ['Backend chưa trả kết quả chấm rủi ro cho hồ sơ này.'] };
  }

  const a = output.assessment;
  const risk: RiskAssessmentResult = {
    riskScore: a.risk_score,
    riskLabel: a.risk_label,
    ltvProposedPct: a.ltv_proposed_pct,
  };

  const ltvPolicyBands: RiskLtvPolicyBand[] = output.ltv_policy_bands.map((b) => ({
    minScore: b.min_score,
    maxScore: b.max_score,
    maxLtvPct: b.max_ltv_pct,
    label: b.label,
  }));

  const riskGroups: RiskGroup[] = output.groups.map((g) => ({
    id: groupId(g.group_key),
    groupKey: g.group_key,
    label: g.label,
    weightPct: g.weight_pct,
    score: g.score,
    rawFindings: g.signals.length ? g.signals : ['Backend chưa trả tín hiệu chi tiết cho nhóm này.'],
    inferenceText: g.signals.length
      ? `Điểm ${g.score}/100, trọng số ${g.weight_pct}% — ${g.signals.join('; ')}.`
      : `Điểm ${g.score}/100, trọng số ${g.weight_pct}% trong điểm rủi ro tổng.`,
    sourceLabel: GROUP_TOOL_NAME[g.group_key] ?? g.group_key,
    toolName: GROUP_TOOL_NAME[g.group_key] ?? g.group_key,
  }));

  const riskFlags: RiskFlag[] = output.flags.map((f, index) => ({
    id: `flag-api-${index}-${f.severity}`,
    severity: f.severity,
    title: f.title,
    description: f.description,
    confidencePct: f.confidence_pct ?? 0,
    verifiedStatus: f.verified ? 'da_xac_thuc' : 'chua_xac_thuc',
  }));

  const groupSummary = riskGroups.map((g) => `<b>${escapeHtml(g.label)}</b> (${g.weightPct}%): ${g.score}/100`).join(' · ');
  const riskWeightedInferenceText = a.risk_inference_text ?? (groupSummary ? `${groupSummary}.` : 'Backend chưa trả chi tiết 5 nhóm rủi ro.');

  const band = currentLtvBand(ltvPolicyBands, risk.riskScore);
  const ltvPolicyInferenceText = `Điểm rủi ro tài sản ${risk.riskScore}/100 rơi vào khung ${band?.label ?? '—'}, nên LTV đề xuất ${risk.ltvProposedPct}%.`;

  return {
    ok: true,
    risk,
    ltvPolicyBands,
    ltvPolicyInferenceText,
    riskGroups,
    riskWeightedInferenceText,
    riskFlags,
    warnings: output.warnings ?? [],
  };
}
