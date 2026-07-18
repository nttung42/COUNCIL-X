import { PlatformPageLayout } from '../../app/layout/PlatformPageLayout';
import { navigate } from '../../app/routes';
import { Badge, Card, FlagRow, SectionHeading, StatTile } from '../../components/common/ui';
import { fixtureCase } from '../../mocks/fixtureCase';
import { allAssetDomainConfigs, findCollateralCase, findDomainByCase, RISK_LABEL, RISK_TONE, STATUS_LABEL } from '../../mocks/assetDomainCases';

const docLabels = ['Sổ hồng.pdf', 'Tờ khai LPTB.pdf', 'Biên bản bàn giao.pdf', 'Ảnh hiện trạng.jpg', 'Thông báo thuế đất.pdf'];

function CaseDocuments() {
  return (
    <Card className="case-side-card">
      <SectionHeading>Tài liệu liên quan</SectionHeading>
      <div className="document-list compact-docs">
        {docLabels.map((doc) => (
          <div key={doc} className="upload-row">
            <div className="upload-ic">PDF</div>
            <div className="upload-info">
              <div className="upload-name">{doc}</div>
              <div className="upload-status">✓ Đã xử lý · evidence ready</div>
            </div>
          </div>
        ))}
      </div>
      <div className="side-actions">
        <button type="button" className="primary-btn">Upload</button>
        <button type="button" className="footer-back-btn">Trích xuất dữ liệu</button>
      </div>
    </Card>
  );
}

export function AppraisalCaseDetailPage({ params }: { params: Record<string, string> }) {
  const summary = findCollateralCase(params.caseId ?? fixtureCase.caseId);
  const domain = findDomainByCase(summary.caseId);
  const isRealEstate = summary.domainId === 'real_estate';
  const appliedDomain = isRealEstate ? allAssetDomainConfigs[0] : domain;
  const findings = isRealEstate
    ? fixtureCase.riskFlags.map((flag) => ({
        title: flag.title,
        description: flag.description,
        meta: `Confidence ${flag.confidencePct}% · ${flag.verifiedStatus === 'da_xac_thuc' ? 'Đã xác thực' : 'Chưa xác thực'}`,
        tone: flag.severity === 'thap' ? 'good' as const : 'warning' as const,
      }))
    : domain.findings.map((finding) => ({
        title: finding.title,
        description: finding.description,
        meta: finding.evidence,
        tone: finding.tone,
      }));

  return (
    <PlatformPageLayout>
      <section className="case-detail-header card">
        <div>
          <span className="case-id">{summary.caseId}</span>
          <h1>{summary.assetName}</h1>
          <p>{summary.domainLabel} · {summary.assetSubtype} · Chủ tài sản: {summary.owner}</p>
        </div>
        <div className="case-header-actions">
          <Badge tone={RISK_TONE[summary.riskLevel]}>{RISK_LABEL[summary.riskLevel]}</Badge>
          <span>{STATUS_LABEL[summary.status]}</span>
          <button type="button" className="footer-back-btn">Lưu nháp</button>
        </div>
      </section>

      <div className="case-detail-layout">
        <aside className="case-detail-left">
          <CaseDocuments />
          <Card className="case-side-card">
            <SectionHeading>Evidence sources</SectionHeading>
            {fixtureCase.docPages.slice(0, 4).map((doc) => (
              <div key={doc.key} className="evidence-source-row">
                <b>{doc.label}</b>
                <span>Source document · confidence mapped</span>
              </div>
            ))}
          </Card>
        </aside>

        <main className="case-detail-main">
          <Card>
            <SectionHeading action={<button type="button" className="primary-btn" onClick={() => navigate(appliedDomain.routeId, { caseId: appliedDomain.caseId })}>Mở workspace</button>}>
              Phân hệ đang áp dụng
            </SectionHeading>
            <div className="applied-domain-card">
              <strong>{appliedDomain.label}</strong>
              <span>{appliedDomain.subtitle}</span>
              <em>{appliedDomain.statusLabel}</em>
            </div>
          </Card>

          <div className="grid c4">
            <StatTile label="Giá trị đề xuất" value={summary.valueLabel} sub="Theo phân hệ thẩm định" />
            <StatTile label="Confidence" value={`${summary.confidencePct}%`} sub={`Evidence coverage ${summary.evidenceCoveragePct}%`} />
            <StatTile label="Risk" value={RISK_LABEL[summary.riskLevel]} sub={`${summary.findingsCount} AI findings`} />
            <StatTile label="Human review" value={summary.status === 'waiting_for_review' ? 'Pending' : 'Open'} sub={summary.nextAction} />
          </div>

          <Card>
            <SectionHeading>Module trạng thái</SectionHeading>
            <div className="module-status-list">
              {appliedDomain.steps.map((step, index) => (
                <div key={step} className="module-status-row">
                  <span className="step-num">{index + 1}</span>
                  <b>{step}</b>
                  <em>{index < 2 ? 'Completed' : index < 4 ? 'Waiting review' : 'Draft ready'}</em>
                </div>
              ))}
            </div>
          </Card>
        </main>

        <aside className="case-detail-right">
          <Card className="right-evidence-panel">
            <SectionHeading>AI findings</SectionHeading>
            {findings.map((finding) => (
              <FlagRow
                key={finding.title}
                leading={<Badge tone={finding.tone} />}
                title={finding.title}
                descriptionHtml={finding.description}
                meta={finding.meta}
              />
            ))}
          </Card>
          <Card className="human-review-box">
            <SectionHeading>Human review</SectionHeading>
            <p>AI output chờ chuyên viên xác nhận trước khi đưa vào báo cáo chính thức.</p>
            <div className="review-actions">
              <button type="button" className="primary-btn">Confirm all</button>
              <button type="button" className="footer-back-btn">Request evidence</button>
              <button type="button" className="footer-back-btn">Reject finding</button>
            </div>
          </Card>
        </aside>
      </div>
    </PlatformPageLayout>
  );
}
