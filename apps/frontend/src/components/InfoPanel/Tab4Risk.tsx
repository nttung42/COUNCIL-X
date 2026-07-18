import { Fragment } from 'react';
import { getEditStatus, useCaseStore } from '../../state/caseStore';
import { Badge, BarRow, Card, FlagRow, LookupDetailCard, Meter, Qmark } from '../common/ui';
import { riskScoreTone, SEVERITY_LABEL, SEVERITY_TONE, TONE_COLOR } from '../../utils/severity';

function isCurrentBand(minScore: number, maxScore: number | null, score: number): boolean {
  return score >= minScore && (maxScore === null || score <= maxScore);
}

export function Tab4Risk() {
  const risk = useCaseStore((s) => s.caseData.risk);
  const ltvPolicyBands = useCaseStore((s) => s.caseData.ltvPolicyBands);
  const ltvPolicyInferenceText = useCaseStore((s) => s.caseData.ltvPolicyInferenceText);
  const riskGroups = useCaseStore((s) => s.caseData.riskGroups);
  const riskWeightedInferenceText = useCaseStore((s) => s.caseData.riskWeightedInferenceText);
  const riskFlags = useCaseStore((s) => s.caseData.riskFlags);
  const valuationProposed = useCaseStore((s) => s.caseData.valuation.proposedValueLabel);
  const pendingEdits = useCaseStore((s) => s.pendingEdits);
  const confirmedKeys = useCaseStore((s) => s.confirmedKeys);

  const riskTone = SEVERITY_TONE[risk.riskLabel];

  return (
    <>
      <div className="grid c2">
        <Card>
          <div className="section-h">
            Điểm rủi ro bất động sản
            <Qmark text="Trung bình có trọng số của 5 nhóm rủi ro của chính tài sản — không phải rủi ro tín dụng người vay. Xem chi tiết cấu thành bên dưới." />
          </div>
          <Meter percent={risk.riskScore} color={TONE_COLOR[riskTone]} valueLabel={<>{risk.riskScore}<span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 500 }}>/100</span></>} />
          <div style={{ marginTop: 9 }}>
            <Badge tone={riskTone}>{SEVERITY_LABEL[risk.riskLabel].toUpperCase()}</Badge>
          </div>
        </Card>
        <Card>
          <div className="section-h">
            LTV đề xuất
            <Qmark text="LTV đề xuất được tính theo khung chính sách LTV gắn với điểm rủi ro tài sản, không phải điểm tín dụng người vay." />
          </div>
          <Meter percent={risk.ltvProposedPct} color="var(--navy-600)" valueLabel={`${risk.ltvProposedPct}%`} />
          <div className="sub" style={{ fontSize: 10.7, color: 'var(--text-muted)', marginTop: 9 }}>
            Trần cho vay trên giá trị định giá {valuationProposed}.
          </div>
          <div className="ld-inference" style={{ marginTop: 10 }}>
            <div className="ld-label">Khung chính sách LTV theo điểm rủi ro</div>
            <p>
              {ltvPolicyBands.map((b, i) => {
                const active = isCurrentBand(b.minScore, b.maxScore, risk.riskScore);
                return (
                  <Fragment key={b.label}>
                    {i > 0 && ' · '}
                    {active ? <b>{b.label}</b> : b.label}
                  </Fragment>
                );
              })}
              {' '}
              {ltvPolicyInferenceText}
            </p>
          </div>
        </Card>
      </div>

      <Card style={{ marginBottom: 12 }}>
        <div className="section-h">5 nhóm rủi ro cấu thành</div>
        <div className="barchart">
          {riskGroups.map((g) => (
            <BarRow
              key={g.id}
              label={`${g.label} · ${g.weightPct}%`}
              valueLabel={g.score}
              percent={g.score}
              color={TONE_COLOR[riskScoreTone(g.score)]}
              status={getEditStatus(pendingEdits, confirmedKeys, 4, `risk.group.${g.groupKey}`)}
            />
          ))}
        </div>
      </Card>

      <Card style={{ marginBottom: 12 }}>
        <div className="section-h">
          Quy đổi điểm rủi ro tổng — trọng số 5 nhóm
          <Qmark text="Điểm rủi ro tổng được tính bằng trung bình có trọng số của 5 nhóm rủi ro cấu thành." />
        </div>
        <table>
          <tbody>
            <tr>
              <th>Nhóm rủi ro</th>
              <th>Điểm</th>
              <th>Trọng số</th>
              <th>Đóng góp</th>
            </tr>
            {riskGroups.map((g) => (
              <tr key={g.id}>
                <td>{g.label}</td>
                <td className="strong">{g.score}</td>
                <td>{g.weightPct}%</td>
                <td>{((g.score * g.weightPct) / 100).toFixed(1)}</td>
              </tr>
            ))}
            <tr>
              <td>
                <b>Tổng (làm tròn)</b>
              </td>
              <td />
              <td>
                <b>100%</b>
              </td>
              <td className="strong">{risk.riskScore}/100</td>
            </tr>
          </tbody>
        </table>
        <div className="ld-inference" style={{ marginTop: 12 }}>
          <div className="ld-label">Nhận định nghiệp vụ</div>
          {/* eslint-disable-next-line react/no-danger */}
          <p dangerouslySetInnerHTML={{ __html: riskWeightedInferenceText }} />
        </div>
      </Card>

      <div className="grid c2">
        {riskGroups.map((g) => (
          <LookupDetailCard
            key={g.id}
            id={g.id}
            badge={<Badge tone={riskScoreTone(g.score)}>Điểm {g.score}/100</Badge>}
            title={g.label}
            qmark={`Nguồn: ${g.toolName} · Trọng số ${g.weightPct}% trong điểm rủi ro tổng.`}
            rawFindings={g.rawFindings}
            inferenceHtml={g.inferenceText}
            metaText={`Nguồn: ${g.sourceLabel} · Trọng số ${g.weightPct}% · Điểm rủi ro ${g.score}/100`}
            status={getEditStatus(pendingEdits, confirmedKeys, 4, `risk.group.${g.groupKey}`)}
          />
        ))}
      </div>

      <Card>
        <div className="section-h">Flags cần lưu ý</div>
        {riskFlags.map((f) => (
          <FlagRow
            key={f.id}
            leading={
              <span className={`badge ${SEVERITY_TONE[f.severity]}`} style={{ flex: 'none' }}>
                {SEVERITY_LABEL[f.severity]}
              </span>
            }
            title={f.title}
            descriptionHtml={f.description}
            meta={`Độ tin cậy ${f.confidencePct}% · ${f.verifiedStatus === 'da_xac_thuc' ? 'Đã xác thực' : 'Chưa xác thực'}`}
            status={getEditStatus(pendingEdits, confirmedKeys, 4, `risk.flag.${f.id}`)}
          />
        ))}
      </Card>
    </>
  );
}
