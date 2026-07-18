import { PlatformPageLayout } from '../../app/layout/PlatformPageLayout';
import { navigate } from '../../app/routes';
import { Badge, Card, SectionHeading } from '../../components/common/ui';
import { allAssetDomainConfigs, collateralCases } from '../../mocks/assetDomainCases';

const capabilityRows = [
  ['Bất động sản', 'Sổ đỏ, ảnh, quy hoạch', 'Comparable + cost', 'Pháp lý, quy hoạch, thanh khoản', 'Tài liệu + nguồn thị trường'],
  ['Động sản', 'Đăng ký, ảnh, serial', 'Market + depreciation', 'Serial, hao mòn, thanh khoản', 'Ảnh + hồ sơ sở hữu'],
  ['Giấy tờ có giá', 'Mã công cụ, lưu ký', 'Market/yield/PV', 'Issuer, market, liquidity', 'Lưu ký + market data'],
  ['Quyền tài sản', 'Hợp đồng, dòng tiền', 'Scenario/recovery', 'Pháp lý, nghĩa vụ, thu hồi', 'Hợp đồng + aging'],
];

export function AssetDomainHubPage() {
  return (
    <PlatformPageLayout>
      <section className="platform-header">
        <div>
          <div className="eyebrow">Asset domains</div>
          <h1>Phân hệ tài sản bảo đảm</h1>
          <p>Chọn nhóm tài sản để thẩm định theo bộ bước, nguồn evidence và calculation riêng.</p>
        </div>
      </section>

      <div className="asset-domain-grid">
        {allAssetDomainConfigs.map((domain) => {
          const count = collateralCases.filter((item) => item.domainId === domain.domainId).length;
          return (
            <button key={domain.domainId} type="button" className="asset-domain-card" onClick={() => navigate(domain.routeId, { caseId: domain.caseId })}>
              <div className="domain-card-head">
                <strong>{domain.label}</strong>
                <Badge tone={domain.domainId === 'real_estate' ? 'good' : 'warning'}>{domain.statusLabel}</Badge>
              </div>
              <p>{domain.subtitle}</p>
              <div className="domain-capabilities">
                {domain.steps.slice(0, 6).map((step) => <span key={step}>✓ {step}</span>)}
              </div>
              <div className="domain-card-foot">
                <span>{count || 1} hồ sơ đang xử lý</span>
                <em>Mở phân hệ →</em>
              </div>
            </button>
          );
        })}
      </div>

      <Card>
        <SectionHeading>Bảng so sánh năng lực</SectionHeading>
        <table>
          <thead>
            <tr>
              <th>Phân hệ</th>
              <th>Đầu vào chính</th>
              <th>Định giá</th>
              <th>Risk chính</th>
              <th>Evidence</th>
            </tr>
          </thead>
          <tbody>
            {capabilityRows.map((row) => (
              <tr key={row[0]}>
                {row.map((cell, index) => <td key={cell} className={index === 0 ? 'strong' : undefined}>{cell}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </PlatformPageLayout>
  );
}
