import { href, matchRoute, navigate, type RouteId } from '../routes';

const NAV_ITEMS: Array<{ routeId: RouteId; label: string; sub: string }> = [
  { routeId: 'casePortal', label: 'Tổng quan', sub: 'Dashboard' },
  { routeId: 'appraisalList', label: 'Hồ sơ thẩm định', sub: 'Work queue' },
  { routeId: 'assetDomainHub', label: 'Phân hệ tài sản', sub: '4 nhóm TSBĐ' },
  { routeId: 'evidenceCenter', label: 'Evidence', sub: 'Nguồn & trace' },
  { routeId: 'reportCenter', label: 'Báo cáo', sub: 'Draft & export' },
];

function isActive(active: RouteId, item: RouteId) {
  if (active === item) return true;
  if (item === 'appraisalList' && (active === 'appraisalDetail' || active === 'realEstateAppraisal')) return true;
  if (
    item === 'assetDomainHub' &&
    (active === 'movableAssetsAppraisal' || active === 'valuablePapersAppraisal' || active === 'propertyRightsAppraisal')
  ) {
    return true;
  }
  return false;
}

export function PlatformNav() {
  const active = matchRoute(window.location.pathname).id;

  return (
    <div className="workflow-topnav platform-topnav">
      <button type="button" className="workflow-brand" onClick={() => navigate('casePortal')}>
        <img className="brand-logo" src="/logo.png" alt="SHB" />
        <span>
          Collateral AI
          <small>Nền tảng thẩm định TSBĐ</small>
        </span>
      </button>
      <nav className="workflow-nav-scroll" aria-label="Điều hướng nền tảng thẩm định tài sản bảo đảm">
        {NAV_ITEMS.map((item, index) => (
          <a key={item.routeId} className={'workflow-nav-item' + (isActive(active, item.routeId) ? ' active' : '')} href={href(item.routeId)}>
            <span className="workflow-nav-icon">{String(index + 1).padStart(2, '0')}</span>
            <span className="workflow-nav-text">
              {item.label}
              <small>{item.sub}</small>
            </span>
          </a>
        ))}
      </nav>
    </div>
  );
}
