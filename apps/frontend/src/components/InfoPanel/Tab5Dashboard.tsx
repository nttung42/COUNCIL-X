import { APPRAISAL_STAGE_LABELS } from '../../mocks/chatScripts';
import { useCaseStore } from '../../state/caseStore';
import { Badge, Card, StatTile, Timeline, TimelineItem } from '../common/ui';
import { SEVERITY_LABEL, VERDICT_LABEL, VERDICT_TONE } from '../../utils/severity';
import { getFieldValue } from '../../utils/tab1Field';
import type { StepNumber } from '../../types';

const FALLBACK_STEP_TEXT: Record<1 | 2 | 3 | 4, string> = {
  1: 'Chưa có dữ liệu — hoàn thành màn Nhập thông tin trước.',
  2: 'Chưa có dữ liệu — hoàn thành màn Kết quả tra cứu trước.',
  3: 'Chưa có dữ liệu — hoàn thành màn Định giá trước.',
  4: 'Chưa có dữ liệu — hoàn thành màn Rủi ro trước.',
};

export function Tab5Dashboard() {
  const caseData = useCaseStore((s) => s.caseData);
  const switchTab = useCaseStore((s) => s.switchTab);
  const exportReport = useCaseStore((s) => s.exportReport);
  const dashboardWarnings = useCaseStore((s) => s.dashboardWarnings);

  const { caseId, tab1Fields, valuation, risk, verdict, overallNarrative, agentTrace, dashboardSteps } = caseData;
  const address = getFieldValue(tab1Fields, 'address');
  const landArea = getFieldValue(tab1Fields, 'land_area_sqm');
  const step1Fallback = address ? `${address} · ${landArea} · Sổ hồng chính chủ.` : FALLBACK_STEP_TEXT[1];

  const stepSummaries: Record<1 | 2 | 3 | 4, string> = {
    1: dashboardSteps.find((d) => d.stepNumber === 1)?.summaryText ?? step1Fallback,
    2: dashboardSteps.find((d) => d.stepNumber === 2)?.summaryText ?? FALLBACK_STEP_TEXT[2],
    3: dashboardSteps.find((d) => d.stepNumber === 3)?.summaryText ?? FALLBACK_STEP_TEXT[3],
    4: dashboardSteps.find((d) => d.stepNumber === 4)?.summaryText ?? FALLBACK_STEP_TEXT[4],
  };

  return (
    <>
      {dashboardWarnings.length > 0 && (
        <Card style={{ marginBottom: 12, background: 'var(--warning-tint)', border: '1px solid rgba(250,178,25,0.4)' }}>
          <div style={{ fontSize: 10.5, fontWeight: 700, color: '#8a6100', marginBottom: 4 }}>{dashboardWarnings.length} cảnh báo dashboard</div>
          <ul style={{ margin: 0, paddingLeft: 16, fontSize: 11.5, color: 'var(--ink)', lineHeight: 1.55 }}>
            {dashboardWarnings.map((w, i) => (
              // eslint-disable-next-line react/no-array-index-key
              <li key={i}>{w}</li>
            ))}
          </ul>
        </Card>
      )}
      <Card style={{ marginBottom: 12 }}>
        <div className="section-h">
          Tổng quan hồ sơ — {caseId}
          <button type="button" className="primary-btn" onClick={() => void exportReport()}>
Xuất báo cáo thẩm định
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
        <div className="section-h">Kết luận cho vay</div>
        {verdict ? (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <Badge tone={VERDICT_TONE[verdict.decision]}>{VERDICT_LABEL[verdict.decision]}</Badge>
              <b>{verdict.headline}</b>
              {verdict.downgraded && <span className="meta">(đã hạ 1 bậc do cảnh báo pháp lý đã xác thực)</span>}
            </div>
            <div className="grid c2" style={{ marginTop: 10 }}>
              <StatTile label="Hạn mức cho vay tối đa" value={verdict.maxLoanVndLabel} sub={`= giá trị đề xuất × LTV ${risk.ltvProposedPct}%`} />
              <StatTile label="Kết luận" value={VERDICT_LABEL[verdict.decision]} sub={risk.riskScore + '/100 · ' + SEVERITY_LABEL[risk.riskLabel]} />
            </div>
            {overallNarrative && (
              <div className="ld-inference" style={{ marginTop: 12 }}>
                <div className="ld-label">Nhận định nghiệp vụ</div>
                <p>{overallNarrative}</p>
              </div>
            )}
            {verdict.reasons.length > 0 && (
              <div className="ld-raw" style={{ marginTop: 12 }}>
                <div className="ld-label">Diễn giải</div>
                <ul>
                  {verdict.reasons.map((r, i) => (
                    // eslint-disable-next-line react/no-array-index-key
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : (
          <div className="meta">Chưa đủ dữ liệu định giá/rủi ro để đưa ra kết luận cho vay.</div>
        )}
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
        <div className="section-h">Trace thực thi — {caseId}</div>
        <Timeline>
          {agentTrace.map((event) => (
            <TimelineItem key={event.id} time={event.secondsOffsetLabel} title={event.title} description={event.description} />
          ))}
        </Timeline>
      </Card>
    </>
  );
}
