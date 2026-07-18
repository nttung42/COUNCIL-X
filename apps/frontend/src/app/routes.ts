import type { ComponentType } from 'react';

export type RouteId =
  | 'casePortal'
  | 'appraisalList'
  | 'appraisalDetail'
  | 'assetDomainHub'
  | 'realEstateAppraisal'
  | 'movableAssetsAppraisal'
  | 'valuablePapersAppraisal'
  | 'propertyRightsAppraisal'
  | 'evidenceCenter'
  | 'reportCenter'
  | 'caseList'
  | 'caseIntake'
  | 'eligibilityScreening'
  | 'financialReview'
  | 'legalReview'
  | 'collateralAppraisal'
  | 'creditUnderwriting'
  | 'creditApproval'
  | 'loanDisbursement'
  | 'portfolioMonitoring';

export interface RouteMatch {
  id: RouteId;
  params: Record<string, string>;
}

export interface AppRoute {
  id: RouteId;
  path: string;
  title: string;
  pattern: RegExp;
  buildPath: (params?: Record<string, string>) => string;
}

const CASE_ID = 'REQ-2026-0001';
const DEMO_CASE_ID = 'REQ-2026-00458';

export const appRoutes: AppRoute[] = [
  route('casePortal', '/', 'Tổng quan thẩm định TSBĐ', /^\/$/, () => '/'),
  route('appraisalList', '/appraisals', 'Hồ sơ thẩm định TSBĐ', /^\/appraisals\/?$/, () => '/appraisals'),
  route('appraisalDetail', '/appraisals/:caseId', 'Chi tiết hồ sơ thẩm định', /^\/appraisals\/([^/]+)\/?$/, (params) => `/appraisals/${params?.caseId ?? CASE_ID}`),
  route('assetDomainHub', '/asset-domains', 'Phân hệ tài sản bảo đảm', /^\/asset-domains\/?$/, () => '/asset-domains'),
  domainRoute('realEstateAppraisal', 'real-estate', 'Bất động sản'),
  domainRoute('movableAssetsAppraisal', 'movable-assets', 'Động sản'),
  domainRoute('valuablePapersAppraisal', 'valuable-papers', 'Giấy tờ có giá'),
  domainRoute('propertyRightsAppraisal', 'property-rights', 'Quyền tài sản'),
  route('evidenceCenter', '/evidence', 'Evidence Center', /^\/evidence\/?$/, () => '/evidence'),
  route('reportCenter', '/reports', 'Report Center', /^\/reports\/?$/, () => '/reports'),

  route('caseList', '/cases', 'Legacy cases alias', /^\/cases\/?$/, () => '/cases'),
  caseRoute('caseIntake', 'intake', 'Tiếp nhận & số hoá'),
  caseRoute('eligibilityScreening', 'screening', 'Sàng lọc điều kiện'),
  caseRoute('financialReview', 'financial-review', 'Thẩm định tài chính'),
  caseRoute('legalReview', 'legal-review', 'Thẩm định pháp lý'),
  caseRoute('collateralAppraisal', 'collateral-appraisal', 'Định giá tài sản bảo đảm'),
  caseRoute('creditUnderwriting', 'underwriting', 'Phản biện tín dụng'),
  caseRoute('creditApproval', 'approval', 'Phê duyệt tín dụng'),
  caseRoute('loanDisbursement', 'disbursement', 'Hợp đồng & giải ngân'),
  route('portfolioMonitoring', '/portfolio-monitoring', 'Giám sát danh mục', /^\/portfolio-monitoring\/?$/, () => '/portfolio-monitoring'),
];

export const routeComponents: Partial<Record<RouteId, ComponentType<{ params: Record<string, string> }>>> = {};

function route(id: RouteId, path: string, title: string, pattern: RegExp, buildPath: AppRoute['buildPath']): AppRoute {
  return { id, path, title, pattern, buildPath };
}

function caseRoute(id: RouteId, slug: string, title: string): AppRoute {
  return route(
    id,
    `/cases/:caseId/${slug}`,
    title,
    new RegExp(`^/cases/([^/]+)/${slug}/?$`),
    (params) => `/cases/${params?.caseId ?? DEMO_CASE_ID}/${slug}`,
  );
}

function domainRoute(id: RouteId, slug: string, title: string): AppRoute {
  return route(
    id,
    `/asset-domains/${slug}/:caseId`,
    title,
    new RegExp(`^/asset-domains/${slug}/([^/]+)/?$`),
    (params) => `/asset-domains/${slug}/${params?.caseId ?? CASE_ID}`,
  );
}

export function matchRoute(pathname: string): RouteMatch {
  for (const item of appRoutes) {
    const match = item.pattern.exec(pathname);
    if (!match) continue;
    return { id: item.id, params: match[1] ? { caseId: decodeURIComponent(match[1]) } : {} };
  }
  return { id: 'casePortal', params: {} };
}

export function getRoute(id: RouteId): AppRoute {
  const found = appRoutes.find((item) => item.id === id);
  if (!found) throw new Error(`Unknown route: ${id}`);
  return found;
}

export function href(routeId: RouteId, params?: Record<string, string>): string {
  return getRoute(routeId).buildPath(params);
}

export function navigate(routeId: RouteId, params?: Record<string, string>) {
  const next = href(routeId, params);
  if (window.location.pathname === next) return;
  window.history.pushState({}, '', next);
  window.dispatchEvent(new PopStateEvent('popstate'));
}
