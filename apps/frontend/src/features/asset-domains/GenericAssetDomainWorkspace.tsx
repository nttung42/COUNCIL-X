import { useState } from 'react';
import { PlatformPageLayout } from '../../app/layout/PlatformPageLayout';
import { Badge, Card, FlagRow, SectionHeading, StatTile } from '../../components/common/ui';
import { assetDomainConfigs, type AssetDomainId } from '../../mocks/assetDomainCases';

const ROUTE_DOMAIN: Record<string, Exclude<AssetDomainId, 'real_estate'>> = {
  movableAssetsAppraisal: 'movable_assets',
  valuablePapersAppraisal: 'valuable_papers',
  propertyRightsAppraisal: 'property_rights',
};

export function GenericAssetDomainWorkspace({ routeId }: { routeId: keyof typeof ROUTE_DOMAIN }) {
  const config = assetDomainConfigs[ROUTE_DOMAIN[routeId]];
  const [activeStep, setActiveStep] = useState(0);

  return (
    <PlatformPageLayout>
      <section className="case-detail-header card">
        <div>
          <span className="case-id">{config.caseId}</span>
          <h1>{config.assetName}</h1>
          <p>{config.label} · {config.assetSubtype} · Chủ tài sản: {config.owner}</p>
        </div>
        <div className="case-header-actions">
          <Badge tone="warning">{config.statusLabel}</Badge>
          <button type="button" className="footer-back-btn">Lưu nháp</button>
        </div>
      </section>

      <div className="domain-workspace">
        <aside className="domain-step-nav card">
          <SectionHeading>Các bước thẩm định</SectionHeading>
          {config.steps.map((step, index) => (
            <button key={step} type="button" className={index === activeStep ? 'active' : ''} onClick={() => setActiveStep(index)}>
              <span>{index + 1}</span>
              {step}
            </button>
          ))}
        </aside>

        <main className="domain-main-workspace">
          <Card>
            <SectionHeading>{config.steps[activeStep]}</SectionHeading>
            <p className="domain-intro">{config.subtitle}</p>
            <div className="grid c4">
              {config.metrics.map((metric) => (
                <StatTile key={metric.label} label={metric.label} value={<span style={{ color: metric.tone }}>{metric.value}</span>} sub={metric.sub} />
              ))}
            </div>
          </Card>

          <Card>
            <SectionHeading>Finding</SectionHeading>
            {config.findings.map((finding) => (
              <FlagRow
                key={finding.id}
                leading={<Badge tone={finding.tone} />}
                title={finding.title}
                descriptionHtml={finding.description}
                meta={`${finding.confidence} · ${finding.humanStatus === 'pending' ? 'Chờ human review' : finding.humanStatus}`}
              />
            ))}
          </Card>

          <Card>
            <SectionHeading>{config.calculation.title}</SectionHeading>
            <table>
              <thead>
                <tr>{config.calculation.columns.map((column) => <th key={column}>{column}</th>)}</tr>
              </thead>
              <tbody>
                {config.calculation.rows.map((row) => (
                  <tr key={row.join('|')}>
                    {row.map((cell, index) => <td key={`${cell}-${index}`} className={index === 0 ? 'strong' : undefined}>{cell}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          <Card className="human-review-box">
            <SectionHeading>Human review</SectionHeading>
            <p>Kết quả AI chỉ là đề xuất. Chuyên viên phải xác nhận, chỉnh sửa hoặc yêu cầu bổ sung evidence trước khi xuất báo cáo.</p>
            <div className="review-actions">
              <button type="button" className="primary-btn">Confirm</button>
              <button type="button" className="footer-back-btn">Edit + reason</button>
              <button type="button" className="footer-back-btn">Add evidence</button>
            </div>
          </Card>
        </main>

        <aside className="right-evidence-panel card">
          <SectionHeading>Evidence</SectionHeading>
          {config.evidence.map((item) => (
            <div key={item.id} className="evidence-center-row compact">
              <b>{item.title}</b>
              <span>{item.source}</span>
              <em>{item.confidence} · {item.status}</em>
            </div>
          ))}
          <SectionHeading>Báo cáo</SectionHeading>
          <div className="report-section-list">
            {config.reportSections.map((section) => <span key={section}>✓ {section}</span>)}
          </div>
        </aside>
      </div>
    </PlatformPageLayout>
  );
}
