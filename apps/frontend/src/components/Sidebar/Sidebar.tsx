import { caseHistory } from '../../mocks/fixtureCase';
import { useCaseStore } from '../../state/caseStore';
import type { CaseStatus } from '../../types';

const STATUS_LABEL: Record<CaseStatus, string> = {
  dang_xu_ly: 'Đang xử lý',
  hoan_tat: 'Hoàn tất',
  huy: 'Huỷ',
};

const STATUS_COLOR: Record<CaseStatus, string> = {
  dang_xu_ly: 'var(--warning)',
  hoan_tat: 'var(--good)',
  huy: 'var(--text-muted)',
};

export function Sidebar() {
  const activeCaseId = useCaseStore((s) => s.caseData.caseId);
  const activeStatus = useCaseStore((s) => s.caseData.status);

  return (
    <div className="sidebar">
      <div className="sb-brand">
        <div className="mark">SHB</div>
        <div className="name txt-hide">
          PAA Workspace
          <small>Digital Expert Agent</small>
        </div>
      </div>
      <div className="sb-section" style={{ paddingBottom: 0 }}>
        <div className="nav-item active">
          <span className="ic">🏠</span>
          <span className="txt-hide">Thẩm định BĐS</span>
        </div>
      </div>
      <div className="sb-divider" />
      <div className="sb-section" style={{ paddingBottom: 0 }}>
        <button type="button" className="new-req-btn">
          ＋ <span className="txt-hide">Yêu cầu thẩm định mới</span>
        </button>
        <div className="sb-label txt-hide">Lịch sử hồ sơ</div>
      </div>
      <div className="history-list">
        {caseHistory.map((item) => {
          const isActive = item.caseId === activeCaseId;
          const status = isActive ? activeStatus : item.status;
          return (
            <div key={item.caseId} className={'history-item' + (isActive ? ' active' : '')}>
              <div className="addr">{item.address}</div>
              <div className="meta">
                <span className="dot" style={{ background: STATUS_COLOR[status] }} />
                <span className="date">
                  {STATUS_LABEL[status]} · {item.updatedAtLabel}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
