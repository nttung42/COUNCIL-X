import { useState } from 'react';
import { PlatformPageLayout } from '../../app/layout/PlatformPageLayout';
import { Badge, Card, SectionHeading, SourceChip } from '../../components/common/ui';
import { assetDomainConfigs } from '../../mocks/assetDomainCases';
import { fixtureCase } from '../../mocks/fixtureCase';

const evidenceItems = [
  ...fixtureCase.tab1Fields.slice(0, 6).map((field) => ({
    id: field.key,
    title: field.label,
    source: field.sourceDocKey ?? 'Nhập tay',
    confidence: field.confidencePct ? `${field.confidencePct}%` : 'N/A',
    usedIn: 'Bất động sản · Dữ liệu tài sản',
    status: field.status === 'da_xac_thuc' ? 'Đã xác nhận' : 'Chờ xác nhận',
  })),
  ...Object.values(assetDomainConfigs).flatMap((domain) => domain.evidence.map((item) => ({
    id: item.id,
    title: item.title,
    source: item.source,
    confidence: item.confidence,
    usedIn: `${domain.label} · ${item.usedIn}`,
    status: item.status,
  }))),
];

export function EvidenceCenterPage() {
  const [selectedId, setSelectedId] = useState(evidenceItems[0]?.id ?? '');
  const selected = evidenceItems.find((item) => item.id === selectedId) ?? evidenceItems[0];

  return (
    <PlatformPageLayout>
      <section className="platform-header">
        <div>
          <div className="eyebrow">Evidence Center</div>
          <h1>Evidence và nguồn dữ liệu</h1>
          <p>Mọi finding quan trọng phải truy ngược được nguồn, confidence và trạng thái human review.</p>
        </div>
      </section>

      <div className="evidence-center-layout">
        <Card>
          <SectionHeading>Danh sách evidence</SectionHeading>
          <div className="evidence-list">
            {evidenceItems.map((item) => (
              <button key={item.id} type="button" className={'evidence-center-row' + (item.id === selectedId ? ' active' : '')} onClick={() => setSelectedId(item.id)}>
                <b>{item.title}</b>
                <span>{item.usedIn}</span>
                <em>{item.confidence} · {item.status}</em>
              </button>
            ))}
          </div>
        </Card>

        <Card className="evidence-preview-card">
          <SectionHeading>Chi tiết evidence</SectionHeading>
          {selected && (
            <>
              <h2>{selected.title}</h2>
              <div className="evidence-detail-grid">
                <span><b>Source</b>{selected.source}</span>
                <span><b>Confidence</b>{selected.confidence}</span>
                <span><b>Used in</b>{selected.usedIn}</span>
                <span><b>Status</b>{selected.status}</span>
              </div>
              <p>Evidence này được dùng để chứng minh finding hoặc metric trong phân hệ thẩm định tương ứng.</p>
              <SourceChip label="Open source" tooltip={selected.source} />
              <div style={{ marginTop: 14 }}>
                <Badge tone={selected.status === 'Đã xác nhận' ? 'good' : selected.status === 'Cần bổ sung' ? 'critical' : 'warning'}>{selected.status}</Badge>
              </div>
            </>
          )}
        </Card>
      </div>
    </PlatformPageLayout>
  );
}
