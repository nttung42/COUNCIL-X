import { useEffect, useState } from 'react';
import { Sidebar } from './components/Sidebar/Sidebar';
import { ChatPane } from './components/ChatPane/ChatPane';
import { InfoPanel } from './components/InfoPanel/InfoPanel';

type MobilePane = 'chat' | 'info';

export function App() {
  const [mobilePane, setMobilePane] = useState<MobilePane>('chat');

  // CSS ở src/theme/global.css dùng selector body.show-chat / body.show-info để ẩn/hiện
  // panel trên màn hình hẹp (<900px) — giữ nguyên cơ chế toggle class trên <body> như mockup gốc.
  useEffect(() => {
    document.body.classList.remove('show-chat', 'show-info');
    document.body.classList.add(`show-${mobilePane}`);
  }, [mobilePane]);

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-col">
        <div className="mobile-toggle">
          <button type="button" className={mobilePane === 'chat' ? 'active' : ''} onClick={() => setMobilePane('chat')}>
            💬 Chat
          </button>
          <button type="button" className={mobilePane === 'info' ? 'active' : ''} onClick={() => setMobilePane('info')}>
            📋 Thông tin
          </button>
        </div>
        <div className="main-split">
          <ChatPane />
          <InfoPanel />
        </div>
      </div>
    </div>
  );
}
