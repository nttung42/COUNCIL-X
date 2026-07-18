import type { ConfidenceFactorKey, LookupBadge, LookupCategory, RiskGroupKey, SeverityLevel, ValuationMethodKey, VerdictDecision } from '../types';

// Kiểu dữ liệu "trên dây" (wire types) — khớp nguyên văn các Pydantic schema của backend thật
// tại ai/src/shb/schemas/api.py và ai/src/shb/ai/plugins/*/schema.py.
// Không dùng trực tiếp trong UI — src/services/apiClient.ts map sang các type camelCase ở
// src/types.ts (Tab1Field, DocPage, AttachedDocument...) trước khi đưa vào store.

export type ApiDocType = 'so_do_so_hong' | 'to_khai_lptb' | 'bien_ban_ban_giao' | 'thong_bao_thue_dat' | 'khac';
export type ApiFieldStatus = 'da_xac_thuc' | 'can_xac_minh' | 'mau_thuan' | 'nhap_tay' | 'suy_luan';
export type ApiTab1Section = 'A' | 'B' | 'C' | 'D';

export interface ApiBBox {
  page: number;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface ApiDocumentInfo {
  file_id: string;
  file_name: string;
  doc_type: ApiDocType;
  is_scanned: boolean;
  page_count: number;
}

export interface ApiFormField {
  key: string;
  section: ApiTab1Section;
  label: string;
  value: string | null;
  confidence: number; // 0-1
  status: ApiFieldStatus;
  source_doc?: string | null;
  source_page?: number | null;
  source_snippet?: string | null;
  bbox?: ApiBBox | null;
}

export interface ApiPropertyIntakeOutput {
  case_id?: string | null;
  documents: ApiDocumentInfo[];
  fields: ApiFormField[];
  warnings: string[];
}

export interface ApiMarketComparable {
  address: string;
  distance_km: number | null;
  area_sqm: number | null;
  transaction_date: string | null;
  price_per_sqm_vnd: number;
}

export interface ApiLookupFinding {
  category: LookupCategory;
  tool_name: string;
  title: string;
  status_badge: LookupBadge;
  raw_findings: string[];
  inference_text: string | null;
  source_label: string | null;
  confidence_pct: number | null;
}

export interface ApiPropertyLookupOutput {
  case_id: string;
  findings: ApiLookupFinding[];
  market_comparables: ApiMarketComparable[];
  warnings: string[];
}

export interface ApiValuationSummary {
  proposed_value_vnd: number;
  value_range_low_vnd: number;
  value_range_high_vnd: number;
  price_per_sqm_vnd: number;
  confidence_pct: number;
  comparable_count: number;
  price_index_period: string | null;
  price_index_value: number | null;
  price_index_base: number | null;
  confidence_inference_text: string | null;
}

export interface ApiValuationMethod {
  method_key: ValuationMethodKey;
  estimated_value_vnd: number;
  weight_pct: number;
  contribution_value_vnd: number;
  method_confidence_pct: number | null;
  inputs: string[];
  inference_text: string | null;
  source_label: string | null;
}

export interface ApiValuationConfidenceFactor {
  factor_key: ConfidenceFactorKey;
  label: string;
  weight_pct: number;
  score: number;
}

export interface ApiPriceIndexPoint {
  period_label: string;
  index_value: number;
  display_order: number;
}

export interface ApiSubjectiveAdjustment {
  value_pct: number;
  reason: string;
  source: string;
  bound_pct: number;
}

export interface ApiPropertyValuationOutput {
  case_id: string;
  valuation: ApiValuationSummary | null;
  methods: ApiValuationMethod[];
  confidence_factors: ApiValuationConfidenceFactor[];
  price_index_series: ApiPriceIndexPoint[];
  subjective_adjustment: ApiSubjectiveAdjustment | null;
  warnings: string[];
}

export interface ApiRiskGroup {
  group_key: RiskGroupKey;
  label: string;
  weight_pct: number;
  score: number;
  signals: string[];
  source_confidence: number | null;
  verified: boolean;
}

export interface ApiRiskFlag {
  severity: SeverityLevel;
  title: string;
  description: string;
  confidence_pct: number | null;
  verified: boolean;
}

export interface ApiLtvBand {
  min_score: number;
  max_score: number | null;
  max_ltv_pct: number;
  label: string;
}

export interface ApiRiskAssessmentSummary {
  risk_score: number;
  risk_label: SeverityLevel;
  ltv_proposed_pct: number;
  risk_inference_text: string | null;
}

export interface ApiPropertyRiskOutput {
  case_id: string;
  assessment: ApiRiskAssessmentSummary | null;
  groups: ApiRiskGroup[];
  flags: ApiRiskFlag[];
  ltv_policy_bands: ApiLtvBand[];
  warnings: string[];
}

export interface ApiDashboardKpi {
  proposed_value_vnd: number;
  value_range_low_vnd: number | null;
  value_range_high_vnd: number | null;
  valuation_confidence_pct: number | null;
  risk_score: number;
  risk_label: SeverityLevel;
  ltv_proposed_pct: number;
}

export interface ApiVerdict {
  decision: VerdictDecision;
  headline: string;
  max_loan_vnd: number | null;
  downgraded: boolean;
  reasons: string[];
}

export interface ApiStepSummary {
  step_number: number;
  title: string;
  summary_text: string;
  generated_by: string;
}

export interface ApiTraceEvent {
  seconds_offset: number;
  actor: string;
  title: string;
  description: string | null;
}

export interface ApiCaseHistory {
  case_id: string;
  address: string | null;
  status: string;
  updated_at: string;
}

export interface ApiPropertyDashboardOutput {
  case_id: string;
  kpi: ApiDashboardKpi | null;
  verdict: ApiVerdict | null;
  step_summaries: ApiStepSummary[];
  overall_narrative: string | null;
  trace: ApiTraceEvent[];
  case_history: ApiCaseHistory[];
  warnings: string[];
}

export interface ApiFileResponse {
  id: string;
  original_name: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

export type ApiJobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface ApiJobResponse {
  id: string;
  plugin_id: string;
  status: ApiJobStatus;
  input: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error: string | null;
  progress: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface ApiPluginRunAsyncResponse {
  job_id: string;
  status: string;
}

export interface ApiPluginRunResponse {
  result: Record<string, unknown>;
}
