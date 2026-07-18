import { useEffect, useMemo, useState } from 'react';
import { DEMO_CASE_ID } from './workflowSteps';
import { LandingPage } from '../features/landing/LandingPage';
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
  casePortal: () => <LandingPage />,
  caseList: () => <CaseIntakePage params={{ caseId: DEMO_CASE_ID }} />,
  caseIntake: (params) => <CaseIntakePage params={params} />,
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
