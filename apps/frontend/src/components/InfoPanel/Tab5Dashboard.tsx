import { APPRAISAL_STAGE_LABELS } from '../../mocks/chatScripts';
import { useCaseStore } from '../../state/caseStore';
import { Card, StatTile, Timeline, TimelineItem } from '../common/ui';
import { SEVERITY_LABEL } from '../../utils/severity';
import { getFieldValue } from '../../utils/tab1Field';
import type { StepNumber } from '../../types';

export function Tab5Dashboard() {
  const caseData = useCaseStore((s) => s.caseData);
  const switchTab = useCaseStore((s) => s.switchTab);
  const exportReport = useCaseStore((s) => s.exportReport);

  const { caseId, tab1Fields, valuation, risk, agentTrace, dashboardSteps } = caseData;
  const address = getFieldValue(tab1Fields, 'address');
  const landArea = getFieldValue(tab1Fields, 'land_area_sqm');

  const stepSummaries: Record<1 | 2 | 3 | 4, string> = {
    1: address ? `${address} · ${landArea} · Sổ hồng chính chủ.` : 'Chưa có dữ liệu — hoàn thành màn Nhập thông tin trước.',
    2: dashboardSteps.find((d) => d.stepNumber === 2)?.summaryText ?? '',
    3: `${valuation.proposedValueLabel} (${valuation.valueRangeLabel}) · độ tin cậy ${valuation.confidencePct}%, kết hợp 3 phương pháp.`,
    4: `Điểm rủi ro tài sản ${risk.riskScore}/100 (${SEVERITY_LABEL[risk.riskLabel]}) · LTV đề xuất ${risk.ltvProposedPct}%.`,
  };

  return (
    <>
      <Card style={{ marginBottom: 12 }}>
        <div className="section-h">
          Tổng quan hồ sơ — {caseId}
          <button type="button" className="primary-btn" onClick={() => void exportReport()}>
            📄 Xuất báo cáo thẩm định
          </button>
        </div>
        <div className="grid c4">
          <StatTile label="Giá trị đề xuất" value={valuation.proposedValueLabel} sub={valuation.valueRangeLabel} />
          <StatTile label="Độ tin cậy định giá" value={`${valuation.confidencePct}%`} sub="Kết hợp 3 phương pháp" />
          <StatTile label="Điểm rủi ro tài sản" value={`${risk.riskScore}/100`} sub={SEVERITY_LABEL[risk.riskLabel]} />
          <StatTile label="LTV đề xuất" value={`${risk.ltvProposedPct}%`} sub="Trên giá trị định giá" />
        </div>
      </Card>

      <Card style={{ marginBottom: 12 }}>
        <div className="section-h">Tổng hợp theo từng bước</div>
        {([1, 2, 3, 4] as const).map((n) => (
          <div key={n} className="flag-row" style={{ cursor: 'pointer' }} onClick={() => switchTab(n as StepNumber)}>
            <span
              className="step-num"
              style={{ flex: 'none', width: 22, height: 22, fontSize: 11, lineHeight: '22px' }}
            >
              {n}
            </span>
            <div>
              <b>{APPRAISAL_STAGE_LABELS[n as StepNumber]}</b>
              <p>{stepSummaries[n]}</p>
              <div className="meta">Xem lại →</div>
            </div>
          </div>
        ))}
      </Card>

      <Card>
        <div className="section-h">Trace thực thi PAA — {caseId}</div>
        <Timeline>
          {agentTrace.map((event) => (
            <TimelineItem key={event.id} time={event.secondsOffsetLabel} title={event.title} description={event.description} />
          ))}
        </Timeline>
      </Card>
    </>
  );
}
