import type { ReactNode } from 'react';
import { PlatformNav } from './PlatformNav';

export function PlatformPageLayout({ children }: { children: ReactNode }) {
  return (
    <div className="page-shell platform-shell">
      <PlatformNav />
      <div className="app-shell workflow-app-shell">
        <main className="platform-page">{children}</main>
      </div>
    </div>
  );
}
