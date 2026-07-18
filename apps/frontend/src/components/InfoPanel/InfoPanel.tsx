import type { StepNumber } from '../../types';
import { TAB_NAMES } from '../../mocks/chatScripts';
import { useCaseStore } from '../../state/caseStore';
import { Tab1Input } from './Tab1Input';
import { Tab2Lookup } from './Tab2Lookup';
import { Tab3Valuation } from './Tab3Valuation';
import { Tab4Risk } from './Tab4Risk';
import { Tab5Dashboard } from './Tab5Dashboard';

const TAB_NUMBERS: StepNumber[] = [1, 2, 3, 4, 5];

export function InfoPanel() {
  const activeTab = useCaseStore((s) => s.activeTab);
  const unlockedTabs = useCaseStore((s) => s.unlockedTabs);
  const isLoadingTab = useCaseStore((s) => s.isLoadingTab);
  const isCaseFinalized = useCaseStore((s) => s.isCaseFinalized);
  const pendingCount = useCaseStore((s) => s.pendingEdits[activeTab].length);
  const switchTab = useCaseStore((s) => s.switchTab);
  const goBack = useCaseStore((s) => s.goBack);
  const confirmAndNext = useCaseStore((s) => s.confirmAndNext);

  const isLastTab = activeTab === 5;
  const nextLabel = isLastTab ? (isCaseFinalized ? '✓ Đã hoàn tất' : '✓ Hoàn tất hồ sơ') : '✓ Xác nhận & Tiếp theo →';
  const hint = isLoadingTab
    ? 'Đang tải dữ liệu cho bước này…'
    : isLastTab
      ? isCaseFinalized
        ? 'Hồ sơ đã hoàn tất rà soát.'
        : 'Đây là bước cuối — rà soát tổng quan & trace thực thi, có thể xuất báo cáo, rồi bấm Hoàn tất để đóng hồ sơ.'
      : pendingCount
        ? `Có ${pendingCount} thay đổi đang chờ xác nhận ở tab "${TAB_NAMES[activeTab]}" — bấm Xác nhận để áp dụng (đánh dấu xanh lá) và qua bước tiếp theo.`
        : `Rà soát thông tin ở tab "${TAB_NAMES[activeTab]}". Sửa qua form hoặc chat nếu cần, rồi bấm Xác nhận để qua bước tiếp theo.`;

  return (
    <div className="info-pane">
      <div className="subtab-bar">
        {TAB_NUMBERS.map((n) => {
          const locked = !unlockedTabs[n];
          return (
            <button
              key={n}
              type="button"
              className={'subtab-btn' + (n === activeTab ? ' active' : '') + (locked ? ' locked' : '')}
              disabled={locked}
              title={locked ? 'Hãy xác nhận các bước trước để mở khoá tab này' : ''}
              onClick={() => switchTab(n)}
            >
              <span className="n">{locked ? '🔒' : n}</span>
              {TAB_NAMES[n]}
            </button>
          );
        })}
      </div>

      {!isLastTab && (
        <div className="review-banner">
          <span className="ic">💬</span>
          Chưa đúng? Sửa trực tiếp trên form (nếu có) hoặc chat với PAA — thay đổi sẽ hiện màu xanh lá sau khi bạn
          bấm Xác nhận.
        </div>
      )}

      <div className="info-content">
        {isLoadingTab ? (
          <div className="info-screen loading-screen active">
            <div className="loading-inner">
              <div className="spinner" />
              <div className="loading-text">Đang tải dữ liệu…</div>
            </div>
          </div>
        ) : (
          <>
            {activeTab === 1 && <Tab1Input />}
            {activeTab === 2 && <Tab2Lookup />}
            {activeTab === 3 && <Tab3Valuation />}
            {activeTab === 4 && <Tab4Risk />}
            {activeTab === 5 && <Tab5Dashboard />}
          </>
        )}
      </div>

      <div className="info-footer">
        <div className="footer-hint">{hint}</div>
        <div className="footer-btns">
          <button type="button" className="footer-back-btn" disabled={activeTab <= 1 || isLoadingTab} onClick={goBack}>
            ← Quay lại
          </button>
          <button
            type="button"
            className={'primary-btn footer-next-btn' + (isLastTab ? ' done' : '')}
            disabled={isLoadingTab || (isLastTab && isCaseFinalized)}
            onClick={() => void confirmAndNext()}
          >
            {nextLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
