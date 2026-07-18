import { PlatformPageLayout } from '../../app/layout/PlatformPageLayout';
import { navigate } from '../../app/routes';
import { Badge, Card, FlagRow, SectionHeading, StatTile } from '../../components/common/ui';
import { allAssetDomainConfigs, collateralCases, RISK_LABEL, RISK_TONE, STATUS_LABEL } from '../../mocks/assetDomainCases';

const kpis = [
  { label: 'Đang thẩm định', value: '24', sub: '4 phân hệ tài sản' },
  { label: 'Chờ review', value: '8', sub: 'Cần chuyên viên xác nhận', tone: 'var(--warning)' },
  { label: 'Blocked', value: '3', sub: 'Thiếu điều kiện/evidence', tone: 'var(--danger)' },
  { label: 'Thiếu evidence', value: '5', sub: 'Nguồn chưa đủ tin cậy' },
  { label: 'Quá SLA', value: '2', sub: 'Cần ưu tiên hôm nay', tone: 'var(--danger)' },
];

const riskHighlights = [
  {
    title: 'Serial động sản cần xác minh',
    description: 'Ảnh số khung xe tải Hino chưa đủ nét để khớp chắc chắn với hồ sơ đăng ký.',
    meta: 'MV-2026-0002 · Động sản',
    tone: 'critical' as const,
  },
  {
    title: 'Thanh khoản giấy tờ có giá thấp',
    description: 'Bid–ask spread cao, số ngày bán dự kiến vượt ngưỡng haircut thanh khoản.',
    meta: 'SEC-2026-0001 · Giấy tờ có giá',
    tone: 'warning' as const,
  },
  {
    title: 'Quyền đòi nợ có khoản quá hạn',
    description: '20% khoản phải thu quá hạn trên 90 ngày, cần loại khỏi giá trị bảo đảm hoặc tăng haircut.',
    meta: 'PR-2026-0001 · Quyền tài sản',
    tone: 'critical' as const,
  },
];

export function CollateralHomePage() {
  const workQueue = collateralCases.slice(0, 4);

  return (
    <PlatformPageLayout>
      <section className="platform-hero">
        <div>
          <div className="eyebrow">Collateral Appraisal Platform</div>
          <h1>Nền tảng thẩm định tài sản bảo đảm</h1>
          <p>Một chuẩn AI finding, evidence, human review và báo cáo cho 4 nhóm tài sản bảo đảm.</p>
        </div>
        <button type="button" className="primary-btn" onClick={() => navigate('appraisalList')}>
          Xem hồ sơ thẩm định
        </button>
      </section>

      <div className="platform-kpi-row">
        {kpis.map((item) => (
          <StatTile key={item.label} label={item.label} value={<span style={{ color: item.tone }}>{item.value}</span>} sub={item.sub} />
        ))}
      </div>

      <div className="platform-two-col">
        <Card>
          <SectionHeading>Work queue hôm nay</SectionHeading>
          <div className="case-card-list compact">
            {workQueue.map((item) => (
              <button key={item.caseId} type="button" className="appraisal-case-card" onClick={() => navigate('appraisalDetail', { caseId: item.caseId })}>
                <span className="case-id">{item.caseId}</span>
                <strong>{item.assetName}</strong>
                <span>{item.domainLabel} · {item.assetSubtype}</span>
                <span>Next action: {item.nextAction}</span>
                <span className="case-card-meta">
                  <Badge tone={RISK_TONE[item.riskLevel]}>{RISK_LABEL[item.riskLevel]}</Badge>
                  <em>{STATUS_LABEL[item.status]}</em>
                </span>
              </button>
            ))}
          </div>
        </Card>

        <Card>
          <SectionHeading action={<button type="button" className="footer-back-btn" onClick={() => navigate('assetDomainHub')}>Mở tất cả</button>}>
            Phân hệ tài sản bảo đảm
          </SectionHeading>
          <div className="domain-mini-grid">
            {allAssetDomainConfigs.map((domain) => (
              <button key={domain.domainId} type="button" className="domain-mini-card" onClick={() => navigate(domain.routeId, { caseId: domain.caseId })}>
                <strong>{domain.label}</strong>
                <span>{domain.subtitle}</span>
                <em>{domain.statusLabel}</em>
              </button>
            ))}
          </div>
        </Card>
      </div>

      <Card>
        <SectionHeading>AI cảnh báo nổi bật</SectionHeading>
        {riskHighlights.map((item) => (
          <FlagRow
            key={item.title}
            leading={<Badge tone={item.tone} />}
            title={item.title}
            descriptionHtml={item.description}
            meta={item.meta}
          />
        ))}
      </Card>
    </PlatformPageLayout>
  );
}
