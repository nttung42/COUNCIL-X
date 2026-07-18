/* App — layout tổng: Sidebar + main (disclaimer banner + mobile toggle + split
   chat 30% / info 70%). Banner disclaimer cố định, KHÔNG có nút đóng (Nguyên tắc VI). */
import './theme/global.css'
import { actions, useCaseStore } from './state/caseStore'
import { USE_FIXTURE } from './services/apiClient'
import { Sidebar } from './components/Sidebar/Sidebar'
import { ChatPane } from './components/ChatPane/ChatPane'
import { InfoPanel } from './components/InfoPanel/InfoPanel'
import { ErrorBoundary } from './components/common/ErrorBoundary'

export default function App() {
  const { mobilePane } = useCaseStore()

  return (
    <div className="app-shell">
      <ErrorBoundary label="thanh bên">
        <Sidebar />
      </ErrorBoundary>

      <div className="main-col">
        {/* Banner disclaimer — cố định, không đóng được (Nguyên tắc VI) */}
        <div className="disclaimer-banner" role="note">
          <span className="ic">⚠️</span>
          <span className="txt">
            DỮ LIỆU MÔ PHỎNG (MOCK) phục vụ demo — KHÔNG phải số liệu ngân hàng/thị trường thật.
            Kết quả định giá/rủi ro chỉ mang tính tham khảo, cần thẩm định viên xác minh.
            {USE_FIXTURE && ' · Đang chạy chế độ fixture (chưa kết nối backend).'}
          </span>
        </div>

        {/* Mobile toggle chat/info */}
        <div className="mobile-toggle">
          <button
            className={mobilePane === 'chat' ? 'active' : ''}
            onClick={() => actions.setMobilePane('chat')}
          >
            💬 Chat
          </button>
          <button
            className={mobilePane === 'info' ? 'active' : ''}
            onClick={() => actions.setMobilePane('info')}
          >
            📋 Thông tin
          </button>
        </div>

        <div className={`main-split show-${mobilePane}`}>
          <ErrorBoundary label="khung chat">
            <ChatPane />
          </ErrorBoundary>
          <ErrorBoundary label="bảng thông tin">
            <InfoPanel />
          </ErrorBoundary>
        </div>
      </div>
    </div>
  )
}
