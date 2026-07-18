import type { RouteId } from './routes';

export interface WorkflowStep {
  routeId: RouteId;
  label: string;
  shortLabel: string;
  role: string;
  icon: string;
  caseId?: string;
}

export const DEMO_CASE_ID = 'REQ-2026-00458';
export const APPRAISAL_CASE_ID = 'REQ-2026-2000';

export const workflowSteps: WorkflowStep[] = [
  { routeId: 'caseIntake', label: 'Tiếp nhận hồ sơ', shortLabel: 'Intake', role: 'RM', icon: 'IN', caseId: DEMO_CASE_ID },
  { routeId: 'eligibilityScreening', label: 'Sàng lọc điều kiện', shortLabel: 'Screening', role: 'Gate', icon: 'GT', caseId: DEMO_CASE_ID },
  { routeId: 'financialReview', label: 'Thẩm định tài chính', shortLabel: 'Financial', role: 'Maker tài chính', icon: 'FI', caseId: DEMO_CASE_ID },
  { routeId: 'legalReview', label: 'Thẩm định pháp lý', shortLabel: 'Legal', role: 'Maker pháp lý', icon: 'LG', caseId: DEMO_CASE_ID },
  { routeId: 'collateralAppraisal', label: 'Định giá tài sản bảo đảm', shortLabel: 'Collateral', role: 'Appraiser', icon: 'CO', caseId: APPRAISAL_CASE_ID },
  { routeId: 'creditUnderwriting', label: 'Phản biện tín dụng', shortLabel: 'Underwriting', role: 'Underwriter', icon: 'UW', caseId: DEMO_CASE_ID },
  { routeId: 'creditApproval', label: 'Phê duyệt tín dụng', shortLabel: 'Approval', role: 'Approver', icon: 'AP', caseId: DEMO_CASE_ID },
  { routeId: 'loanDisbursement', label: 'Hợp đồng & giải ngân', shortLabel: 'Disbursement', role: 'Credit support', icon: 'CS', caseId: DEMO_CASE_ID },
  { routeId: 'portfolioMonitoring', label: 'Giám sát danh mục', shortLabel: 'Monitoring', role: 'Portfolio', icon: 'MO' },
];
