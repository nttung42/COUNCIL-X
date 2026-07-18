import { PlatformPageLayout } from '../../app/layout/PlatformPageLayout';
import { navigate } from '../../app/routes';
import { Badge, Card, SectionHeading } from '../../components/common/ui';
import { collateralCases, RISK_LABEL, RISK_TONE, STATUS_LABEL } from '../../mocks/assetDomainCases';

export function ReportCenterPage() {
  return (
    <PlatformPageLayout>
      <section className="platform-header">
        <div>
          <div className="eyebrow">Report Center</div>
          <h1>Báo cáo thẩm định tài sản bảo đảm</h1>
          <p>Quản lý báo cáo nháp, báo cáo chờ review và báo cáo đã xác nhận.</p>
        </div>
      </section>

      <Card className="filter-card">
        <SectionHeading>Bộ lọc báo cáo</SectionHeading>
        <div className="filter-row">
          {['Tất cả', 'Draft ready', 'Waiting review', 'Finalized'].map((item, index) => (
            <button key={item} type="button" className={'subtab-btn' + (index === 0 ? ' active' : '')}>{item}</button>
          ))}
        </div>
      </Card>

      <div className="report-card-grid">
        {collateralCases.map((item) => (
          <Card key={item.caseId} className="report-card">
            <div className="report-card-head">
              <span className="case-id">{item.caseId}</span>
              <Badge tone={RISK_TONE[item.riskLevel]}>{RISK_LABEL[item.riskLevel]}</Badge>
            </div>
            <h2>Báo cáo thẩm định {item.domainLabel}</h2>
            <p>{item.assetName}</p>
            <div className="evidence-detail-grid">
              <span><b>Trạng thái</b>{STATUS_LABEL[item.status]}</span>
              <span><b>Evidence coverage</b>{item.evidenceCoveragePct}%</span>
              <span><b>Confidence</b>{item.confidencePct}%</span>
              <span><b>Giá trị</b>{item.valueLabel}</span>
            </div>
            <div className="report-actions">
              <button type="button" className="primary-btn" onClick={() => navigate('appraisalDetail', { caseId: item.caseId })}>Preview</button>
              <button type="button" className="footer-back-btn">Export</button>
            </div>
          </Card>
        ))}
      </div>
    </PlatformPageLayout>
  );
}
