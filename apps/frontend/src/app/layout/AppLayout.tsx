import { useEffect, useState, type ReactNode } from 'react';
import { MobilePaneToggle } from './MobilePaneToggle';
import { WorkflowNav } from './WorkflowNav';

type MobilePane = 'chat' | 'info';

export function WorkflowPageLayout({
  chat,
  children,
  defaultPane = 'chat',
}: {
  chat?: ReactNode;
  children: ReactNode;
  defaultPane?: MobilePane;
}) {
  const [mobilePane, setMobilePane] = useState<MobilePane>(defaultPane);

  useEffect(() => {
    document.body.classList.remove('show-chat', 'show-info');
    document.body.classList.add(`show-${mobilePane}`);
  }, [mobilePane]);

  return (
    <div className="page-shell">
      <WorkflowNav />
      <div className="app-shell workflow-app-shell">
        <div className="main-col">
          {chat && <MobilePaneToggle pane={mobilePane} onChange={setMobilePane} />}
          <div className="main-split">
            {chat}
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
