import { useEffect, useMemo, useState } from 'react';
import { DEMO_CASE_ID } from './workflowSteps';
import { AppraisalCaseDetailPage } from '../features/collateral-platform/AppraisalCaseDetailPage';
import { AppraisalCaseListPage } from '../features/collateral-platform/AppraisalCaseListPage';
import { AssetDomainHubPage } from '../features/collateral-platform/AssetDomainHubPage';
import { CollateralHomePage } from '../features/collateral-platform/CollateralHomePage';
import { EvidenceCenterPage } from '../features/collateral-platform/EvidenceCenterPage';
import { ReportCenterPage } from '../features/collateral-platform/ReportCenterPage';
import { GenericAssetDomainWorkspace } from '../features/asset-domains/GenericAssetDomainWorkspace';
import { CaseIntakePage } from '../features/case-intake/CaseIntakePage';
import { EligibilityScreeningPage } from '../features/eligibility-screening/EligibilityScreeningPage';
import { FinancialReviewPage } from '../features/financial-review/FinancialReviewPage';
import { LegalReviewPage } from '../features/legal-review/LegalReviewPage';
import { CollateralAppraisalPage } from '../features/collateral-appraisal/CollateralAppraisalPage';
import { CreditUnderwritingPage } from '../features/credit-underwriting/CreditUnderwritingPage';
import { CreditApprovalPage } from '../features/credit-approval/CreditApprovalPage';
import { LoanDisbursementPage } from '../features/loan-disbursement/LoanDisbursementPage';
import { PortfolioMonitoringPage } from '../features/portfolio-monitoring/PortfolioMonitoringPage';
import { matchRoute, type RouteId } from './routes';

const PAGES: Record<RouteId, (params: Record<string, string>) => JSX.Element> = {
  casePortal: () => <CollateralHomePage />,
  appraisalList: () => <AppraisalCaseListPage />,
  appraisalDetail: (params) => <AppraisalCaseDetailPage params={params} />,
  assetDomainHub: () => <AssetDomainHubPage />,
  realEstateAppraisal: (params) => <CollateralAppraisalPage params={params} />,
  movableAssetsAppraisal: () => <GenericAssetDomainWorkspace routeId="movableAssetsAppraisal" />,
  valuablePapersAppraisal: () => <GenericAssetDomainWorkspace routeId="valuablePapersAppraisal" />,
  propertyRightsAppraisal: () => <GenericAssetDomainWorkspace routeId="propertyRightsAppraisal" />,
  evidenceCenter: () => <EvidenceCenterPage />,
  reportCenter: () => <ReportCenterPage />,

  caseList: () => <AppraisalCaseListPage />,
  caseIntake: (params) => <CaseIntakePage params={params.caseId ? params : { caseId: DEMO_CASE_ID }} />,
  eligibilityScreening: (params) => <EligibilityScreeningPage params={params} />,
  financialReview: (params) => <FinancialReviewPage params={params} />,
  legalReview: (params) => <LegalReviewPage params={params} />,
  collateralAppraisal: (params) => <CollateralAppraisalPage params={params} />,
  creditUnderwriting: (params) => <CreditUnderwritingPage params={params} />,
  creditApproval: (params) => <CreditApprovalPage params={params} />,
  loanDisbursement: (params) => <LoanDisbursementPage params={params} />,
  portfolioMonitoring: () => <PortfolioMonitoringPage />,
};

export function Router() {
  const [pathname, setPathname] = useState(window.location.pathname);

  useEffect(() => {
    const sync = () => setPathname(window.location.pathname);
    window.addEventListener('popstate', sync);
    return () => window.removeEventListener('popstate', sync);
  }, []);

  const match = useMemo(() => matchRoute(pathname), [pathname]);
  return PAGES[match.id](match.params);
}
