import { useEffect, useState } from 'react';
import { WorkflowNav } from '../../app/layout/WorkflowNav';
import { AppraisalChatPane } from './components/AppraisalChatPane';
import { AppraisalSidebar } from './components/AppraisalSidebar';
import { AppraisalWorkspace } from './components/AppraisalWorkspace';

type MobilePane = 'chat' | 'info';

export function CollateralAppraisalPage({ params: _params }: { params: Record<string, string> }) {
  const [mobilePane, setMobilePane] = useState<MobilePane>('chat');

  useEffect(() => {
    document.body.classList.remove('show-chat', 'show-info');
    document.body.classList.add(`show-${mobilePane}`);
  }, [mobilePane]);

  return (
    <div className="page-shell appraisal-page">
      <WorkflowNav />
      <div className="app-shell">
        <AppraisalSidebar />
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
            <AppraisalChatPane />
            <AppraisalWorkspace />
          </div>
        </div>
      </div>
    </div>
  );
}
