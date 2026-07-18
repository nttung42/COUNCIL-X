import { href, matchRoute, navigate } from '../routes';
import { workflowSteps } from '../workflowSteps';

export function WorkflowNav() {
  const active = matchRoute(window.location.pathname).id;

  return (
    <div className="workflow-topnav">
      <button type="button" className="workflow-brand" onClick={() => navigate('casePortal')}>
        <span className="brand-mark">SHB</span>
        <span>
          Credit AI
          <small>Digital appraisal suite</small>
        </span>
      </button>
      <nav className="workflow-nav-scroll" aria-label="Luồng xử lý hồ sơ">
        {workflowSteps.map((step) => {
          const params = step.caseId ? { caseId: step.caseId } : undefined;
          const isActive = active === step.routeId;
          return (
            <a key={step.routeId} className={'workflow-nav-item' + (isActive ? ' active' : '')} href={href(step.routeId, params)}>
              <span className="workflow-nav-icon">{step.icon}</span>
              <span className="workflow-nav-text">
                {step.shortLabel}
                <small>{step.role}</small>
              </span>
            </a>
          );
        })}
      </nav>
    </div>
  );
}
