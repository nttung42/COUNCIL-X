import { PlatformPageLayout } from '../../app/layout/PlatformPageLayout';
import { navigate } from '../../app/routes';
import { Badge, Card, SectionHeading } from '../../components/common/ui';
import { collateralCases, RISK_LABEL, RISK_TONE, STATUS_LABEL } from '../../mocks/assetDomainCases';

const filters = ['Tất cả', 'Bất động sản', 'Động sản', 'Giấy tờ có giá', 'Quyền tài sản'];

export function AppraisalCaseListPage() {
  return (
    <PlatformPageLayout>
      <section className="platform-header">
        <div>
          <div className="eyebrow">Work queue</div>
          <h1>Hồ sơ thẩm định tài sản bảo đảm</h1>
          <p>Danh sách hồ sơ tài sản cần AI phân tích, gắn evidence và chuyên viên xác nhận.</p>
        </div>
        <button type="button" className="primary-btn">+ Hồ sơ mới</button>
      </section>

      <Card className="filter-card">
        <SectionHeading>Bộ lọc nhanh</SectionHeading>
        <div className="filter-row">
          {filters.map((item, index) => (
            <button key={item} type="button" className={'subtab-btn' + (index === 0 ? ' active' : '')}>
              {item}
            </button>
          ))}
        </div>
      </Card>

      <div className="case-card-grid">
        {collateralCases.map((item) => (
          <button key={item.caseId} type="button" className="appraisal-case-card large" onClick={() => navigate('appraisalDetail', { caseId: item.caseId })}>
            <span className="case-id">{item.caseId}</span>
            <strong>{item.assetName}</strong>
            <span>{item.domainLabel} · {item.assetSubtype}</span>
            <span>Chủ tài sản: {item.owner}</span>
            <span>{item.location}</span>
            <div className="case-metrics-line">
              <b>{item.valueLabel}</b>
              <span>Confidence {item.confidencePct}%</span>
            </div>
            <div className="case-card-meta">
              <Badge tone={RISK_TONE[item.riskLevel]}>{RISK_LABEL[item.riskLevel]}</Badge>
              <em>{STATUS_LABEL[item.status]}</em>
            </div>
            <div className="case-card-foot">
              <span>AI findings: {item.findingsCount} · Blocker: {item.blockerCount}</span>
              <span>Evidence {item.evidenceCoveragePct}%</span>
            </div>
            <span className="case-next">Next: {item.nextAction}</span>
            <span className="primary-btn case-detail-btn">Detail</span>
          </button>
        ))}
      </div>
    </PlatformPageLayout>
  );
}
