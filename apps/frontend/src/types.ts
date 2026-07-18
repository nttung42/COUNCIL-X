/* ============================================================================
   Type definitions — mirror contracts/appraisal-api.md + data-model.md.
   Kept intentionally permissive (optional fields) so a component renders
   "chưa có dữ liệu" instead of crashing when a field is missing (Error Handling).
   ============================================================================ */

export type CaseStatus = 'processing' | 'completed' | 'cancelled'
export type SourceType = 'mock' | 'verified' | 'unverified_rumor'
export type PropertyType = 'nha_pho' | 'dat_nen' | 'chung_cu' | 'bds_thuong_mai'
export type LegalStatus = 'so_hong' | 'so_do' | 'giay_tay' | 'khac'
export type RiskTier = 'LOW' | 'MEDIUM' | 'HIGH'
export type Severity = 'low' | 'medium' | 'high'

export interface SubjectProperty {
  address: string
  lat?: number
  long?: number
  area_m2?: number
  property_type?: PropertyType
  legal_status_claimed?: LegalStatus
}

export interface LoanContext {
  requested_amount?: number
  purpose?: string
}

export interface AppraisalRequestBody {
  request_id: string
  subject_property: SubjectProperty
  loan_context: LoanContext
}

/* ---- data-model.md §2 ComparableTransaction ---- */
export interface ComparableTransaction {
  transaction_id?: string
  address?: string
  area_m2?: number
  distance_from_subject_km?: number
  transaction_date?: string
  price_per_m2?: number
  price_total?: number
  source_type?: SourceType
  confidence?: number
}

/* ---- data-model.md §5 Lookup envelope ---- */
export interface LookupEnvelope<T = Record<string, unknown>> {
  tool_name?: string
  status?: 'ok' | 'partial' | 'error'
  confidence?: number
  source_type?: SourceType
  data?: T
  warning?: string | null
}

export interface AmenityItem { type?: string; name?: string; distance_m?: number }
export interface RumorItem { detail?: string; year?: number; verified?: boolean }

export interface LookupResult {
  comparables?: ComparableTransaction[]
  market_price?: LookupEnvelope<{
    comparables?: ComparableTransaction[]
    price_index_period?: string
    price_index?: { period: string; index: number }[]
  }>
  planning_zoning?: LookupEnvelope<{ zoning_status?: string; is_planned_overlay?: boolean; road_widening_plan?: string }>
  legal_status?: LookupEnvelope<{ legal_status?: string; has_dispute?: boolean; mortgaged_elsewhere?: boolean }>
  neighborhood_amenity?: LookupEnvelope<{ amenities?: AmenityItem[] }>
  stigma_reputation?: LookupEnvelope<{ rumors?: RumorItem[] }>
  environmental_risk?: LookupEnvelope<{ flood_risk?: string; landslide_risk?: string; pollution_risk?: string; notes?: string }>
  liquidity_stat?: LookupEnvelope<{ avg_days_on_market?: number; success_rate_pct?: number }>
}

/* ---- data-model.md §6 ValuationResult ---- */
export interface ValuationResult {
  estimated_value?: number
  value_range?: { low?: number; high?: number }
  value_per_m2?: number
  confidence_score?: number
  methodology_breakdown?: {
    comparable_approach?: number
    hedonic_model?: number
    cost_approach?: number
  }
  comparables_used?: number
  time_adjustment_index_period?: string
  price_index_series?: { period: string; index: number }[]
  adjustment_notes?: string[]
}

/* ---- data-model.md §7 AssetRiskAssessment ---- */
export interface RiskFlag {
  type?: string
  severity?: Severity
  detail?: string
  confidence?: number
  action?: string
  verified?: boolean
}

export interface AssetRiskAssessment {
  asset_risk_score?: number
  risk_tier?: RiskTier
  recommended_ltv_cap?: number
  risk_group_scores?: {
    legal?: number
    liquidity?: number
    price_volatility?: number
    physical_environmental?: number
    reputation_stigma?: number
  }
  flags?: RiskFlag[]
  recommended_conditions?: string[]
}

/* ---- data-model.md §8 ChecklistItem ---- */
export interface ChecklistItem {
  item_id: string
  text: string
  is_checked: boolean
  property_type_scope?: string[]
  related_flag_type?: string | null
}

/* ---- data-model.md §9 AppraisalReportDraft ---- */
export interface DraftReport {
  sections?: {
    property_info?: string
    valuation?: string
    risk_and_ltv?: string
  }
  signature_block?: string
}

/* ---- data-model.md §11 TraceEvent ---- */
export interface TraceEvent {
  step_name?: string
  component?: string
  t_offset_seconds?: number
  input_summary?: string
  output_summary?: string
}

/* ---- contracts §3 full case state ---- */
export interface AppraisalReport {
  case_id?: string
  request_id?: string
  status?: CaseStatus
  subject_property?: SubjectProperty
  loan_context?: LoanContext
  lookup_result?: LookupResult
  valuation?: ValuationResult
  asset_risk?: AssetRiskAssessment
  checklist?: ChecklistItem[]
  draft_report?: DraftReport
  requires_human_verification?: boolean
  trace_id?: string
  trace_events?: TraceEvent[]
}

/* ---- contracts §4 sidebar list item ---- */
export interface CaseListItem {
  case_id: string
  address: string
  status: CaseStatus
  updated_at: string
}

/* ---- chat ---- */
export type ChatRole = 'user' | 'agent' | 'status'
export interface Citation { source_doc?: string; excerpt?: string }
export interface ChatMessage {
  role: ChatRole
  content: string
  citations?: Citation[]
}

/* ---- contracts §2 SSE step_update payload ---- */
export interface StepUpdateEvent {
  step_name?: string
  active_tab?: number
  chat_message?: string
  status?: CaseStatus
}
