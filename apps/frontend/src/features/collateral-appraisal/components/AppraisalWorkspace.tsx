import type { StepNumber } from '../../../types';
import { APPRAISAL_STAGE_LABELS } from '../../../mocks/chatScripts';
import { useCaseStore } from '../../../state/caseStore';
import { getFieldValue } from '../../../utils/tab1Field';
import { SEVERITY_LABEL } from '../../../utils/severity';
import { AppraisalIntakePanel } from './AppraisalIntakePanel';
import { MarketAndLegalLookupPanel } from './MarketAndLegalLookupPanel';
import { CollateralValuationPanel } from './CollateralValuationPanel';
import { CollateralRiskPanel } from './CollateralRiskPanel';
import { AppraisalSummaryPanel } from './AppraisalSummaryPanel';

const APPRAISAL_STAGES: StepNumber[] = [1, 2, 3, 4, 5];

export function AppraisalWorkspace() {
  const activeStage = useCaseStore((s) => s.activeTab);
  const unlockedStages = useCaseStore((s) => s.unlockedTabs);
  const isLoadingStage = useCaseStore((s) => s.isLoadingTab);
  const isCaseFinalized = useCaseStore((s) => s.isCaseFinalized);
  const pendingCount = useCaseStore((s) => s.pendingEdits[activeStage].length);
  const switchStage = useCaseStore((s) => s.switchTab);
  const goBack = useCaseStore((s) => s.goBack);
  const confirmAndNext = useCaseStore((s) => s.confirmAndNext);
  const tab1Fields = useCaseStore((s) => s.caseData.tab1Fields);
  const valuation = useCaseStore((s) => s.caseData.valuation);
  const risk = useCaseStore((s) => s.caseData.risk);

  const address = getFieldValue(tab1Fields, 'address') || 'Chưa có địa chỉ';
  const landArea = getFieldValue(tab1Fields, 'land_area_sqm') || 'Chưa có diện tích';
  const propertyType = getFieldValue(tab1Fields, 'property_type') || 'Tài sản bảo đảm';
  const isLastStage = activeStage === 5;
  const nextLabel = isLastStage ? (isCaseFinalized ? 'Đã hoàn tất' : 'Hoàn tất hồ sơ') : 'Xác nhận & tiếp theo →';
  const hint = isLoadingStage
    ? 'Đang tải dữ liệu cho bước này…'
    : isLastStage
      ? isCaseFinalized
        ? 'Hồ sơ đã hoàn tất rà soát.'
        : 'Rà soát tổng quan và trace thực thi, xuất báo cáo nếu cần, rồi hoàn tất hồ sơ.'
      : pendingCount
        ? `Có ${pendingCount} thay đổi đang chờ xác nhận ở tab "${APPRAISAL_STAGE_LABELS[activeStage]}". Xác nhận để áp dụng và chuyển bước.`
        : `Rà soát thông tin ở tab "${APPRAISAL_STAGE_LABELS[activeStage]}". Sửa trên form hoặc assistant nếu cần, rồi xác nhận để chuyển bước.`;

  return (
    <div className="info-pane">
      <div className="subtab-bar">
        {APPRAISAL_STAGES.map((stage) => {
          const locked = !unlockedStages[stage];
          return (
            <button
              key={stage}
              type="button"
              className={'subtab-btn' + (stage === activeStage ? ' active' : '') + (locked ? ' locked' : '')}
              disabled={locked}
              title={locked ? 'Hãy xác nhận các bước trước để mở khoá tab này' : ''}
              onClick={() => switchStage(stage)}
            >
              <span className="n">{locked ? '🔒' : stage}</span>
              {APPRAISAL_STAGE_LABELS[stage]}
            </button>
          );
        })}
      </div>

      <div className="collateral-case-strip card">
        <div>
          <span>Hồ sơ TSBĐ</span>
          <b>{address}</b>
        </div>
        <div>
          <span>Loại tài sản</span>
          <b>{propertyType}</b>
        </div>
        <div>
          <span>Diện tích đất</span>
          <b>{landArea}</b>
        </div>
        <div>
          <span>Định giá đề xuất</span>
          <b>{valuation.proposedValueLabel}</b>
        </div>
        <div>
          <span>Rủi ro / LTV</span>
          <b>{SEVERITY_LABEL[risk.riskLabel]} · {risk.ltvProposedPct}%</b>
        </div>
      </div>

      <div className="info-content">
        {isLoadingStage ? (
          <div className="info-screen loading-screen active">
            <div className="loading-inner">
              <div className="spinner" />
              <div className="loading-text">Đang tải dữ liệu…</div>
            </div>
          </div>
        ) : (
          <>
            {activeStage === 1 && <AppraisalIntakePanel />}
            {activeStage === 2 && <MarketAndLegalLookupPanel />}
            {activeStage === 3 && <CollateralValuationPanel />}
            {activeStage === 4 && <CollateralRiskPanel />}
            {activeStage === 5 && <AppraisalSummaryPanel />}
          </>
        )}
      </div>

      <div className="info-footer">
        <div className="footer-hint">{hint}</div>
        <div className="footer-btns">
          <button type="button" className="footer-back-btn" disabled={activeStage <= 1 || isLoadingStage} onClick={goBack}>
            Quay lại
          </button>
          <button
            type="button"
            className={'primary-btn footer-next-btn' + (isLastStage ? ' done' : '')}
            disabled={isLoadingStage || (isLastStage && isCaseFinalized)}
            onClick={() => void confirmAndNext()}
          >
            {nextLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
