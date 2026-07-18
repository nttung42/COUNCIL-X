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

// Trạng thái 1 trường trích xuất ở màn "Nhập thông tin" — khớp 1:1 với FieldStatus (StrEnum)
// trả về bởi plugin property_intake ở ai/src/shb/ai/plugins/property_intake/schema.py.
export type Tab1FieldStatus = 'da_xac_thuc' | 'can_xac_minh' | 'mau_thuan' | 'nhap_tay' | 'suy_luan';

/** Khớp 4 khối A/B/C/D ở màn "Nhập thông tin" — cũng là giá trị FormField.section từ API thật. */
export type Tab1SectionKey = 'A' | 'B' | 'C' | 'D';

/** Vùng khoanh trên trang tài liệu, đơn vị % kích thước trang (0-100) — quy đổi từ BBox (0-1) của API. */
export interface FieldBBox {
  top: number;
  left: number;
  w: number;
  h: number;
}

/**
 * 1 trường ở màn "Nhập thông tin". Shape này bám theo FormField của plugin property_intake
 * (ai/src/shb/ai/plugins/property_intake/schema.py) thay vì object lồng nhau theo tên trường —
 * vì API thật trả về danh sách phẳng, không có shape cố định borrower/legal/physical/loan.
 */
export interface Tab1Field {
  /** id ổn định dùng làm key React + key theo dõi pending/confirmed — khớp key của FormField từ API thật, vd. 'land_area_sqm'. */
  key: string;
  section: Tab1SectionKey;
  label: string;
  value: string;
  /** 0-100, null nếu trường nhập tay/suy luận không có điểm tin cậy OCR. */
  confidencePct: number | null;
  status: Tab1FieldStatus;
  /** key của DocPage trong docPages, null nếu không có vùng nguồn trực tiếp (nhập tay/suy luận). */
  sourceDocKey: string | null;
  /** trích dẫn nguyên văn từ tài liệu (FormField.source_snippet), hoặc ghi chú lý do suy luận/nhập tay. */
  sourceSnippet: string | null;
  bbox: FieldBBox | null;
}

export interface AttachedDocument {
  id: string;
  fileName: string;
  icon: string;
  docCategory: DocumentCategory;
  uploadedAtLabel: string;
}

/** 1 tài liệu đã xử lý, hiển thị trong khung "Tài liệu & vùng trích xuất" — khớp DocumentInfo của API. */
export interface DocPage {
  key: string;
  label: string;
  scan?: boolean;
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
  tab1Fields: Tab1Field[];
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
