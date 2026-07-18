import type { StepNumber } from '../../../types';
import { APPRAISAL_STAGE_LABELS } from '../../../mocks/chatScripts';
import { useCaseStore } from '../../../state/caseStore';
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

  const isLastStage = activeStage === 5;
  const nextLabel = isLastStage ? (isCaseFinalized ? '✓ Đã hoàn tất' : '✓ Hoàn tất hồ sơ') : '✓ Xác nhận & Tiếp theo →';
  const hint = isLoadingStage
    ? 'Đang tải dữ liệu cho bước này…'
    : isLastStage
      ? isCaseFinalized
        ? 'Hồ sơ đã hoàn tất rà soát.'
        : 'Đây là bước cuối — rà soát tổng quan & trace thực thi, có thể xuất báo cáo, rồi bấm Hoàn tất để đóng hồ sơ.'
      : pendingCount
        ? `Có ${pendingCount} thay đổi đang chờ xác nhận ở tab "${APPRAISAL_STAGE_LABELS[activeStage]}" — bấm Xác nhận để áp dụng (đánh dấu xanh lá) và qua bước tiếp theo.`
        : `Rà soát thông tin ở tab "${APPRAISAL_STAGE_LABELS[activeStage]}". Sửa qua form hoặc chat nếu cần, rồi bấm Xác nhận để qua bước tiếp theo.`;

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

      {!isLastStage && (
        <div className="review-banner">
          <span className="ic">•</span>
          Rà soát dữ liệu trên form hoặc trao đổi với PAA. Thay đổi chỉ áp dụng sau khi bấm Xác nhận.
        </div>
      )}

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
            ← Quay lại
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
