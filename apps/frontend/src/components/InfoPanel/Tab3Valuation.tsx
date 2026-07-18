import { useMemo } from 'react';
import { getEditStatus, useCaseStore } from '../../state/caseStore';
import { Badge, BarRow, Card, LookupDetailCard, Qmark, StatTile } from '../common/ui';
import { parseLeadingNumber } from '../../utils/format';
import { confidenceScoreTone, methodConfidenceTone, TONE_COLOR } from '../../utils/severity';

const SPARK_W = 300;
const SPARK_H = 100;
const PAD_X = 8;
const PAD_TOP = 10;
const PAD_BOTTOM = 12;

function PriceIndexSpark({ series }: { series: { periodLabel: string; indexValue: number }[] }) {
  const { lineStr, areaStr, endX, endY } = useMemo(() => {
    const values = series.map((p) => p.indexValue);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const xStep = (SPARK_W - PAD_X * 2) / Math.max(1, series.length - 1);
    const pts = series.map((p, i) => {
      const x = PAD_X + i * xStep;
      const range = max - min || 1;
      const y = PAD_TOP + (1 - (p.indexValue - min) / range) * (SPARK_H - PAD_TOP - PAD_BOTTOM);
      return [x, y] as const;
    });
    const line = pts.map((p) => p.join(',')).join(' ');
    const area = `${PAD_X},${SPARK_H - PAD_BOTTOM} ${line} ${SPARK_W - PAD_X},${SPARK_H - PAD_BOTTOM}`;
    const last = pts[pts.length - 1] ?? [0, 0];
    return { lineStr: line, areaStr: area, endX: last[0], endY: last[1] };
  }, [series]);

  const first = series[0];
  const last = series[series.length - 1];

  return (
    <>
      <svg viewBox="0 0 300 100" width="100%" height="100" preserveAspectRatio="none">
        <polygon points={areaStr} fill="var(--navy-600)" fillOpacity={0.1} stroke="none" />
        <polyline points={lineStr} fill="none" stroke="var(--navy-600)" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        <circle cx={endX} cy={endY} r={4.5} fill="var(--orange-600)" stroke="var(--white)" strokeWidth={2} />
      </svg>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10.3, color: 'var(--text-muted)', marginTop: 4 }}>
        <span>
          {first?.periodLabel} · {first?.indexValue.toFixed(1)}
        </span>
        <span>
          {last?.periodLabel} · {last?.indexValue.toFixed(1)}
        </span>
      </div>
    </>
  );
}

export function Tab3Valuation() {
  const valuation = useCaseStore((s) => s.caseData.valuation);
  const priceIndexSeries = useCaseStore((s) => s.caseData.priceIndexSeries);
  const valuationMethods = useCaseStore((s) => s.caseData.valuationMethods);
  const valuationWeightedInferenceText = useCaseStore((s) => s.caseData.valuationWeightedInferenceText);
  const confidenceFactors = useCaseStore((s) => s.caseData.confidenceFactors);
  const confidenceInferenceText = useCaseStore((s) => s.caseData.confidenceInferenceText);
  const pendingEdits = useCaseStore((s) => s.pendingEdits);
  const confirmedKeys = useCaseStore((s) => s.confirmedKeys);

  const tileStatus = getEditStatus(pendingEdits, confirmedKeys, 3, 'valuation.tile');
  const maxMethodValue = Math.max(...valuationMethods.map((m) => parseLeadingNumber(m.estimatedValueLabel)));

  return (
    <>
      <div className="grid c4">
        <StatTile label="Giá trị đề xuất" value={valuation.proposedValueLabel} sub={valuation.valueRangeLabel} status={tileStatus} id="tile-valuation" />
        <StatTile label="Giá/m²" value={valuation.pricePerSqmLabel} sub={`quy đổi ${valuation.priceIndexPeriod}`} />
        <StatTile
          label="Độ tin cậy"
          value={`${valuation.confidencePct}%`}
          sub={`${valuation.comparableCount} giao dịch dùng`}
          qmark="Trung bình có trọng số của 5 yếu tố: số lượng/chất lượng giao dịch so sánh (30%), mức đồng thuận giữa 3 phương pháp (25%), độ đầy đủ dữ liệu pháp lý/quy hoạch (20%), biến động thị trường gần đây (15%), độ tương đồng giao dịch so sánh (10%) — xem chi tiết bên dưới."
          id="tile-confidence"
        />
        <StatTile label="Kỳ chỉ số giá" value={valuation.priceIndexPeriod} sub={`index ${valuation.priceIndexValue} (gốc ${valuation.priceIndexBase})`} />
      </div>

      <div className="grid c2">
        <Card>
          <div className="section-h">
            3 phương pháp định giá
            <Qmark text="Kết hợp so sánh trực tiếp, hedonic-ML và chi phí xây dựng để giảm sai lệch." />
          </div>
          <div className="barchart">
            {valuationMethods.map((m) => (
              <BarRow
                key={m.id}
                label={m.label}
                valueLabel={m.estimatedValueLabel}
                percent={(parseLeadingNumber(m.estimatedValueLabel) / (maxMethodValue || 1)) * 100}
              />
            ))}
          </div>
        </Card>
        <Card>
          <div className="section-h">Chỉ số giá theo thời gian</div>
          <PriceIndexSpark series={priceIndexSeries} />
        </Card>
      </div>

      <Card style={{ marginBottom: 12 }}>
        <div className="section-h">
          Quy đổi giá trị đề xuất — trọng số kết hợp 3 phương pháp
          <Qmark text="Trọng số do Valuation Agent gán theo độ tin cậy riêng của từng phương pháp trong bối cảnh dữ liệu hiện có của tài sản này." />
        </div>
        <table>
          <tbody>
            <tr>
              <th>Phương pháp</th>
              <th>Giá trị ước tính</th>
              <th>Trọng số</th>
              <th>Đóng góp</th>
            </tr>
            {valuationMethods.map((m) => (
              <tr key={m.id}>
                <td>{m.label}</td>
                <td className="strong">{m.estimatedValueLabel}</td>
                <td>{m.weightPct}%</td>
                <td>{m.contributionValueLabel}</td>
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
              <td className="strong">{valuation.proposedValueLabel}</td>
            </tr>
          </tbody>
        </table>
        <div className="ld-inference" style={{ marginTop: 12 }}>
          <div className="ld-label">💡 Nhận định của PAA</div>
          {/* eslint-disable-next-line react/no-danger */}
          <p dangerouslySetInnerHTML={{ __html: valuationWeightedInferenceText }} />
        </div>
      </Card>

      <div className="grid c3">
        {valuationMethods.map((m) => (
          <LookupDetailCard
            key={m.id}
            id={m.id}
            badge={<Badge tone={methodConfidenceTone(m.methodConfidencePct)}>Độ tin cậy {m.methodConfidencePct}%</Badge>}
            title={m.label}
            qmark={
              m.methodKey === 'sales_comparison'
                ? 'Phương pháp so sánh trực tiếp (Sales Comparison Approach) — dùng giao dịch thực tế đã điều chỉnh khác biệt.'
                : m.methodKey === 'hedonic_ml'
                  ? 'Mô hình hồi quy đa biến (hedonic pricing) học từ dữ liệu giao dịch lịch sử khu vực.'
                  : 'Phương pháp chi phí (Cost Approach) — giá đất tham chiếu cộng chi phí xây dựng, trừ khấu hao.'
            }
            rawLabel="Dữ liệu đầu vào"
            rawFindings={m.inputs}
            inferenceHtml={m.inferenceText}
            metaText={`Nguồn: ${m.sourceLabel} · Độ tin cậy phương pháp: ${m.methodConfidencePct}%`}
          />
        ))}
      </div>

      <Card>
        <div className="section-h">
          Cấu thành độ tin cậy tổng {valuation.confidencePct}%
          <Qmark text="Trung bình có trọng số của 5 yếu tố ảnh hưởng đến độ tin cậy định giá." />
        </div>
        <div className="barchart">
          {confidenceFactors.map((f) => (
            <BarRow
              key={f.factorKey}
              label={`${f.label} · ${f.weightPct}%`}
              valueLabel={f.score}
              percent={f.score}
              color={TONE_COLOR[confidenceScoreTone(f.score)]}
            />
          ))}
        </div>
        <div className="ld-inference" style={{ marginTop: 12 }}>
          <div className="ld-label">💡 Nhận định của PAA</div>
          {/* eslint-disable-next-line react/no-danger */}
          <p dangerouslySetInnerHTML={{ __html: confidenceInferenceText }} />
        </div>
      </Card>
    </>
  );
}
