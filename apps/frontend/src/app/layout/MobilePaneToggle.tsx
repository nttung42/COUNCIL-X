type MobilePane = 'chat' | 'info';

export function MobilePaneToggle({ pane, onChange }: { pane: MobilePane; onChange: (pane: MobilePane) => void }) {
  return (
    <div className="mobile-toggle">
      <button type="button" className={pane === 'chat' ? 'active' : ''} onClick={() => onChange('chat')}>
        Assistant
      </button>
      <button type="button" className={pane === 'info' ? 'active' : ''} onClick={() => onChange('info')}>
        Hồ sơ
      </button>
    </div>
  );
}
