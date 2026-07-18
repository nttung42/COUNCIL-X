/* InfoPanel 70% — SubtabBar + tab đang active. Bọc ErrorBoundary để 1 tab lỗi
   không sập app; hiển thị loading/error rõ ràng (Error Handling). */
import { useCaseStore } from '../../state/caseStore'
import { ErrorBoundary } from '../common/ErrorBoundary'
import { SubtabBar } from './SubtabBar'
import { Tab1Input } from './Tab1Input'
import { Tab2Lookup } from './Tab2Lookup'
import { Tab3Valuation } from './Tab3Valuation'
import { Tab4Risk } from './Tab4Risk'
import { Tab5Checklist } from './Tab5Checklist'
import { Tab6Dashboard } from './Tab6Dashboard'

export function InfoPanel() {
  const { activeTab, loading, error } = useCaseStore()

  return (
    <div className="info-pane">
      <SubtabBar />
      <div className="info-content">
        {error && (
          <div className="state-msg error">
            {error}
            <br />
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              Kiểm tra backend hoặc bật VITE_USE_FIXTURE=true để xem dữ liệu mẫu.
            </span>
          </div>
        )}
        {!error && loading && (
          <div className="state-msg">
            <span className="spinner" />
            Đang tải hồ sơ…
          </div>
        )}
        {!error && !loading && (
          <ErrorBoundary label={`tab ${activeTab}`}>
            {activeTab === 1 && <Tab1Input />}
            {activeTab === 2 && <Tab2Lookup />}
            {activeTab === 3 && <Tab3Valuation />}
            {activeTab === 4 && <Tab4Risk />}
            {activeTab === 5 && <Tab5Checklist />}
            {activeTab === 6 && <Tab6Dashboard />}
          </ErrorBoundary>
        )}
      </div>
    </div>
  )
}
