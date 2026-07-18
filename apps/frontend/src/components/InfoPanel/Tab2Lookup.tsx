import type { LookupBadge } from '../../types';
import { getEditStatus, useCaseStore } from '../../state/caseStore';
import { Badge, Card, LookupDetailCard, Qmark } from '../common/ui';

const BADGE_TONE: Record<LookupBadge, { tone: 'good' | 'warning'; label: string }> = {
  da_xac_thuc: { tone: 'good', label: 'Đã xác thực' },
  luu_y: { tone: 'warning', label: 'Lưu ý' },
  chua_xac_thuc: { tone: 'warning', label: 'Chưa xác thực' },
};

export function Tab2Lookup() {
  const marketComparables = useCaseStore((s) => s.caseData.marketComparables);
  const marketInferenceText = useCaseStore((s) => s.caseData.marketInferenceText);
  const lookupFindings = useCaseStore((s) => s.caseData.lookupFindings);
  const pendingEdits = useCaseStore((s) => s.pendingEdits);
  const confirmedKeys = useCaseStore((s) => s.confirmedKeys);

  return (
    <>
      <Card className="" status={undefined}>
        <div className="section-h">
          Giao dịch so sánh khu vực
          <Qmark text="Nguồn: dữ liệu tra cứu giá thị trường (market_price_lookup) trong bán kính 1.1km quanh tài sản, đã quy đổi theo chỉ số giá hiện hành." />
        </div>
        <table>
          <tbody>
            <tr>
              <th>Địa chỉ</th>
              <th>Cách</th>
              <th>DT</th>
              <th>Ngày GD</th>
              <th>Giá/m²</th>
            </tr>
            {marketComparables.map((mc) => (
              <tr key={mc.id}>
                <td>{mc.compAddress}</td>
                <td>{mc.distanceKmLabel}</td>
                <td>{mc.areaSqmLabel}</td>
                <td>{mc.transactionDateLabel}</td>
                <td className="strong">{mc.pricePerSqmLabel}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="ld-inference" style={{ marginTop: 12 }}>
          <div className="ld-label">💡 Nhận định của PAA</div>
          <p>{marketInferenceText}</p>
        </div>
      </Card>

      <div className="grid c2">
        {lookupFindings.map((finding) => {
          const key = `lookup.${finding.id}`;
          const status = getEditStatus(pendingEdits, confirmedKeys, 2, key);
          const badgeInfo = finding.statusBadge ? BADGE_TONE[finding.statusBadge] : null;
          return (
            <LookupDetailCard
              key={finding.id}
              id={finding.id}
              badge={badgeInfo ? <Badge tone={badgeInfo.tone}>{badgeInfo.label}</Badge> : undefined}
              title={finding.title}
              qmark={`Nguồn: ${finding.toolName} · Độ tin cậy ${finding.confidencePct}%`}
              rawFindings={finding.rawFindings}
              inferenceHtml={finding.inferenceText}
              metaText={`Nguồn: ${finding.sourceLabel} · Độ tin cậy ${finding.confidencePct}%`}
              status={status}
            />
          );
        })}
      </div>
    </>
  );
}
