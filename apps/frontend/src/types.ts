// Domain types for the PAA appraiser workspace.
// Field names/shape mirror ai/PAA_Schema_PostgreSQL.sql (schema `paa`) but in camelCase,
// since the frontend talks to the (not-yet-built) API in JSON, not to Postgres directly.
// Whoever wires the real API can map snake_case columns -> these fields in src/services/apiClient.ts.

export type CaseStatus = 'dang_xu_ly' | 'hoan_tat' | 'huy';
export type StepStatus = 'locked' | 'unlocked' | 'confirmed';
export type SeverityLevel = 'thap' | 'trung_binh' | 'cao' | 'nghiem_trong';
export type VerificationStatus = 'da_xac_thuc' | 'chua_xac_thuc';
export type EditSource = 'ui_form' | 'chat';
export type EditStatus = 'pending' | 'confirmed';
export type ChatRole = 'user' | 'agent' | 'status';
export type DocumentCategory = 'so_do_so_hong' | 'cmnd_cccd' | 'hop_dong' | 'anh_hien_trang' | 'khac';
export type LookupCategory =
  | 'market_price'
  | 'planning_zoning'
  | 'legal_status'
  | 'neighborhood_amenity'
  | 'environmental_risk'
  | 'liquidity_stat'
  | 'stigma_reputation';
export type LookupBadge = 'da_xac_thuc' | 'luu_y' | 'chua_xac_thuc';
export type ValuationMethodKey = 'sales_comparison' | 'hedonic_ml' | 'cost_approach';
export type ConfidenceFactorKey =
  | 'comp_quantity_quality'
  | 'method_consensus'
  | 'legal_planning_completeness'
  | 'market_volatility'
  | 'comp_similarity';
export type RiskGroupKey = 'legal' | 'liquidity' | 'price_volatility' | 'physical_environment' | 'reputation';

/** Số thứ tự subtab 1..5 (Nhập thông tin / Kết quả tra cứu / Định giá / Rủi ro / Dashboard). */
export type StepNumber = 1 | 2 | 3 | 4 | 5;

export interface AppraisalCaseSummary {
  caseId: string;
  address: string;
  status: CaseStatus;
  updatedAtLabel: string; // vd. "hôm nay", "hôm qua", "3 ngày trước" — hiển thị ở sidebar
}

/** Tham chiếu tới vùng trích xuất trên tài liệu gốc — hiển thị dạng chip "📄 nguồn" dưới mỗi trường. */
export interface SourceRef {
  /** key của DocPage trong docPages, hoặc 'suy-luan' nếu PAA suy luận / không có nguồn trực tiếp. */
  docKey: string;
  /** id của DocBox trong DocPage tương ứng, nếu có vùng khoanh trên tài liệu. */
  boxId?: string;
  /** Nhãn hiển thị trên chip, vd. "📄 Sổ hồng ↗" hoặc "✍️ Nhập tay (không có nguồn)". */
  label: string;
  /** Nội dung tooltip khi hover — trích dẫn nguyên văn từ tài liệu / lý do suy luận. */
  srcText: string;
  /** true nếu là cảnh báo (mâu thuẫn giữa các nguồn, chưa đủ căn cứ...) — hiển thị màu đỏ. */
  warn?: boolean;
}

export interface CaseField<T = string> {
  value: T;
  source?: SourceRef;
}

export interface CaseBorrower {
  id: string;
  fullName: CaseField;
  nationalId: CaseField;
  phoneNumber: CaseField;
  relationshipToAsset: CaseField;
}

export interface PropertyLegalInfo {
  certificateType: CaseField;
  certificateNumber: CaseField;
  issueDateAuthority: CaseField;
  landPlotMapSheet: CaseField;
  landUsePurpose: CaseField;
  useTerm: CaseField;
  ownershipForm: CaseField;
  currentMortgageStatus: CaseField;
}

export interface PropertyPhysicalInfo {
  address: CaseField;
  propertyType: CaseField;
  landAreaSqm: CaseField;
  floorAreaSqm: CaseField;
  frontageDepth: CaseField;
  numFloorsDesc: CaseField;
  constructionYear: CaseField;
  structureMaterial: CaseField;
  houseDirection: CaseField;
  roadTypeDesc: CaseField;
  currentUsageStatus: CaseField;
}

export interface LoanInfo {
  loanAmountVnd: CaseField;
  loanPurpose: CaseField;
  loanTermYears: CaseField;
}

export interface AttachedDocument {
  id: string;
  fileName: string;
  icon: string;
  docCategory: DocumentCategory;
  uploadedAtLabel: string;
}

/** Một ô khoanh vùng trích xuất trên trang tài liệu, kèm % độ tin cậy OCR/extraction. */
export interface DocBox {
  id: string;
  top: number;
  left: number;
  w: number;
  h: number;
  conf: number;
  field: string;
  value: string;
}

export interface DocPage {
  key: string;
  label: string;
  scan?: boolean;
  boxes: DocBox[];
}

export interface MarketComparable {
  id: string;
  compAddress: string;
  distanceKmLabel: string;
  areaSqmLabel: string;
  transactionDateLabel: string;
  pricePerSqmLabel: string;
}

export interface LookupFinding {
  id: string;
  category: LookupCategory;
  toolName: string;
  /** undefined = không hiển thị badge (vd. Tiện ích, Thanh khoản trong mockup gốc). */
  statusBadge?: LookupBadge;
  title: string;
  rawFindings: string[];
  inferenceText: string;
  sourceLabel: string;
  confidencePct: number;
}

export interface ValuationPriceIndexPoint {
  periodLabel: string;
  indexValue: number;
}

export interface ValuationMethod {
  id: string;
  methodKey: ValuationMethodKey;
  label: string;
  estimatedValueLabel: string;
  weightPct: number;
  contributionValueLabel: string;
  methodConfidencePct: number;
  inputs: string[];
  inferenceText: string;
  sourceLabel: string;
}

export interface ValuationConfidenceFactor {
  factorKey: ConfidenceFactorKey;
  label: string;
  weightPct: number;
  score: number;
}

export interface ValuationResult {
  proposedValueLabel: string;
  valueRangeLabel: string;
  pricePerSqmLabel: string;
  confidencePct: number;
  comparableCount: number;
  priceIndexPeriod: string;
  priceIndexValue: number;
  priceIndexBase: number;
}

export interface RiskLtvPolicyBand {
  minScore: number;
  maxScore: number | null;
  maxLtvPct: number;
  label: string;
}

export interface RiskGroup {
  id: string;
  groupKey: RiskGroupKey;
  label: string;
  weightPct: number;
  score: number;
  rawFindings: string[];
  inferenceText: string;
  sourceLabel: string;
  toolName: string;
}

export interface RiskFlag {
  id: string;
  severity: SeverityLevel;
  title: string;
  description: string;
  confidencePct: number;
  verifiedStatus: VerificationStatus;
}

export interface RiskAssessmentResult {
  riskScore: number;
  riskLabel: SeverityLevel;
  ltvProposedPct: number;
}

export interface DashboardStepSummary {
  stepNumber: 1 | 2 | 3 | 4;
  title: string;
  summaryText: string;
}

export interface AgentTraceEvent {
  id: string;
  secondsOffsetLabel: string;
  actor: string;
  title: string;
  description: string;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  html: string;
}

/** Toàn bộ dữ liệu 1 hồ sơ thẩm định — hình dạng payload mà GET /cases/:id dự kiến trả về. */
export interface AppraisalCaseFull {
  caseId: string;
  status: CaseStatus;
  borrower: CaseBorrower;
  legal: PropertyLegalInfo;
  physical: PropertyPhysicalInfo;
  loan: LoanInfo;
  documents: AttachedDocument[];
  docPages: DocPage[];
  marketComparables: MarketComparable[];
  marketInferenceText: string;
  lookupFindings: LookupFinding[];
  valuation: ValuationResult;
  priceIndexSeries: ValuationPriceIndexPoint[];
  valuationMethods: ValuationMethod[];
  valuationWeightedInferenceText: string;
  confidenceFactors: ValuationConfidenceFactor[];
  confidenceInferenceText: string;
  risk: RiskAssessmentResult;
  ltvPolicyBands: RiskLtvPolicyBand[];
  ltvPolicyInferenceText: string;
  riskGroups: RiskGroup[];
  riskWeightedInferenceText: string;
  riskFlags: RiskFlag[];
  dashboardSteps: DashboardStepSummary[];
  agentTrace: AgentTraceEvent[];
}
