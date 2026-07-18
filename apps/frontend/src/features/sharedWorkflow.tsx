import { useEffect, useRef, useState } from 'react';
import { WorkflowPageLayout } from '../app/layout/AppLayout';
import { navigate, type RouteId } from '../app/routes';
import { DEMO_CASE_ID } from '../app/workflowSteps';
import { Badge, Card, Meter, Qmark, SectionHeading, StatTile } from '../components/common/ui';

export interface WorkflowCard {
  tone?: 'good' | 'warning' | 'serious' | 'critical';
  title: string;
  description: string;
  meta?: string;
  evidence?: string;
  rule?: string;
  action?: string;
  confidence?: string;
}

export interface WorkflowMetric {
  label: string;
  value: string;
  sub: string;
  tone?: string;
}

export interface WorkflowTable {
  title: string;
  columns: string[];
  rows: string[][];
}

function tableCellClass(cell: string, index: number): string | undefined {
  const normalized = cell.toLowerCase();
  if (index === 0) return 'strong';
  if (['pass', 'received', 'complete', 'completed'].includes(normalized)) return 'cell-status good';
  if (['missing', 'blocked', 'critical', 'reject'].includes(normalized)) return 'cell-status critical';
  if (['watch', 'explain', 'warning', 'review needed'].includes(normalized)) return 'cell-status warning';
  return undefined;
}

export interface WorkflowPageConfig {
  agentTitle: string;
  agentSubtitle: string;
  agentIcon: string;
  welcomeTitle: string;
  welcomeText: string;
  chips: string[];
  banner: string;
  loadingText: string;
  progress: string[];
  summaryTitle: string;
  metrics?: WorkflowMetric[];
  table?: WorkflowTable;
  cards: WorkflowCard[];
  footerHint: string;
  primaryLabel: string;
  nextRoute?: RouteId;
  secondaryLabel?: string;
  blocker?: string;
}

function SimpleChat({ config }: { config: WorkflowPageConfig }) {
  const [started, setStarted] = useState(false);
  const [messages, setMessages] = useState<string[]>([]);
  const [draft, setDraft] = useState('');

  function send(text: string) {
    const value = text.trim();
    if (!value) return;
    setStarted(true);
    setMessages((items) => [
      ...items,
      `<b>Bạn</b><br>${value}`,
      `<b>${config.agentTitle.split(' — ')[0]}</b><br>Đã ghi nhận. Kết quả chính nằm ở panel bên phải; các điều kiện/cảnh báo được giữ đúng theo mockup nghiệp vụ.`,
    ]);
    setDraft('');
  }

  return (
    <div className="chat-pane">
      <div className="pane-head">
        <div className="title">{config.agentTitle}</div>
        <div className="sub">{config.agentSubtitle}</div>
      </div>
      {!started ? (
        <div className="chat-welcome">
          <div className="agent-summary-card">
            <div className="agent-summary-top">
              <span className="welcome-avatar">{config.agentIcon}</span>
              <div>
                <div className="welcome-title">{config.welcomeTitle}</div>
                <div className="welcome-text">{config.welcomeText}</div>
              </div>
            </div>
          </div>
          <div className="suggest-label">Suggested actions</div>
          <div className="suggest-chips">
            {config.chips.map((chip) => (
              <button key={chip} type="button" className="chip" onClick={() => send(chip)}>
                {chip}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="chat-thread">
          {messages.map((html, index) => (
            <div key={`${html}-${index}`} className={'msg ' + (index % 2 ? 'agent' : 'user')} dangerouslySetInnerHTML={{ __html: html }} />
          ))}
        </div>
      )}
      <div className="chat-input-bar">
        <input
          className="chat-input"
          placeholder={`Hỏi ${config.agentTitle.split(' — ')[0]}…`}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') send(draft);
          }}
        />
        <button type="button" className="chat-send" onClick={() => send(draft)}>
          ➤
        </button>
      </div>
    </div>
  );
}

export function WorkflowAgentPage({ config, caseId = DEMO_CASE_ID }: { config: WorkflowPageConfig; caseId?: string }) {
  const [selectedCard, setSelectedCard] = useState<WorkflowCard | null>(null);
  const drawerCloseRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!selectedCard) return undefined;
    drawerCloseRef.current?.focus();
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setSelectedCard(null);
        return;
      }
      if (event.key !== 'Tab') return;

      const focusable = drawerRef.current?.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      );
      if (!focusable?.length) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [selectedCard]);

  return (
    <WorkflowPageLayout chat={<SimpleChat config={config} />}>
      <div className="info-pane demo-workspace">
        <div className="review-banner"><span className="ic">⚡</span>{config.banner}</div>
        <div className="info-content">
          <div className="case-strip-card card">
            <span><b>Cty TNHH ABC</b> · Vay bổ sung VLĐ 5 tỷ · 24 tháng</span>
            <span>Người đại diện: <b>Trần Văn B</b></span>
            <span>Mã hồ sơ: <b>{caseId}</b></span>
          </div>

          <div className="process-summary">
            <div>
              <b>Processing complete</b>
              <span>{config.progress.length} checks completed · {config.cards.length} findings</span>
            </div>
            <details>
              <summary>View checks</summary>
              <div className="flow-progress">
                {config.progress.map((step) => (
                  <div key={step} className="flow-step done">
                    <span className="flow-ic">✓</span>
                    {step}
                  </div>
                ))}
              </div>
            </details>
          </div>

          <Card>
            <SectionHeading>
              {config.summaryTitle} <Qmark text={config.loadingText} />
            </SectionHeading>
            {config.metrics && (
              <div className="grid c4 workflow-metrics">
                {config.metrics.map((metric) => (
                  <StatTile
                    key={metric.label}
                    label={metric.label}
                    value={<span style={{ color: metric.tone }}>{metric.value}</span>}
                    sub={metric.sub}
                  />
                ))}
              </div>
            )}
            {config.table && (
              <div className="workflow-table-wrap">
                <div className="section-h">{config.table.title}</div>
                <table>
                  <thead>
                    <tr>
                      {config.table.columns.map((column) => <th key={column}>{column}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {config.table.rows.map((row) => (
                      <tr key={row.join('|')}>
                        {row.map((cell, index) => <td key={`${cell}-${index}`} className={tableCellClass(cell, index)}>{cell}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="workflow-card-list">
              {config.cards.map((card) => (
                <div
                  key={card.title}
                  role="button"
                  tabIndex={0}
                  className="flag-row flag-row-button"
                  onClick={() => setSelectedCard(card)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') setSelectedCard(card);
                  }}
                >
                  <div>
                    <div className="workflow-card-title">
                      <b>{card.title}</b>
                      <Badge tone={card.tone ?? 'good'} />
                    </div>
                    <p>{card.description}</p>
                    {(card.evidence || card.rule || card.action || card.confidence) && (
                      <div className="evidence-grid">
                        {card.evidence && <span><b>Evidence</b>{card.evidence}</span>}
                        {card.rule && <span><b>Rule</b>{card.rule}</span>}
                        {card.action && <span><b>Action</b>{card.action}</span>}
                        {card.confidence && <span><b>Confidence</b>{card.confidence}</span>}
                      </div>
                    )}
                    {card.meta && <div className="meta">{card.meta}</div>}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
        {selectedCard && (
          <div className="drawer-backdrop" onClick={() => setSelectedCard(null)}>
            <aside ref={drawerRef} className="evidence-drawer" role="dialog" aria-modal="true" aria-labelledby="evidence-drawer-title" onClick={(event) => event.stopPropagation()}>
              <button ref={drawerCloseRef} type="button" className="drawer-close" aria-label="Đóng evidence drawer" onClick={() => setSelectedCard(null)}>×</button>
              <Badge tone={selectedCard.tone ?? 'good'} />
              <h2 id="evidence-drawer-title">{selectedCard.title}</h2>
              <p>{selectedCard.description}</p>
              <div className="drawer-section">
                <b>Evidence</b>
                <span>{selectedCard.evidence ?? 'Không có nguồn bổ sung.'}</span>
              </div>
              <div className="drawer-section">
                <b>Rule</b>
                <span>{selectedCard.rule ?? 'Không có rule bổ sung.'}</span>
              </div>
              <div className="drawer-section">
                <b>Recommended action</b>
                <span>{selectedCard.action ?? 'Không cần xử lý thêm.'}</span>
              </div>
              <div className="drawer-section">
                <b>Confidence</b>
                <span>{selectedCard.confidence ?? 'Not specified'}</span>
              </div>
              {selectedCard.meta && <div className="drawer-meta">{selectedCard.meta}</div>}
            </aside>
          </div>
        )}
        <div className="info-footer">
          <div className="footer-hint">
            {config.footerHint}
            {config.blocker && <span className="footer-blocker">Blocked: {config.blocker}</span>}
          </div>
          <div className="footer-btns">
            {config.secondaryLabel && <button type="button" className="footer-back-btn">{config.secondaryLabel}</button>}
            <button type="button" className="primary-btn" disabled={Boolean(config.blocker)} onClick={() => config.nextRoute && navigate(config.nextRoute, { caseId })}>
              {config.primaryLabel} →
            </button>
          </div>
        </div>
      </div>
    </WorkflowPageLayout>
  );
}

export function PortfolioMetric({ label, value, sub, color }: { label: string; value: string; sub: string; color?: string }) {
  return <StatTile label={label} value={<span style={{ color }}>{value}</span>} sub={sub} />;
}

export function ScoreMeter({ value, color }: { value: string; color: string }) {
  const percent = Number.parseFloat(value);
  return <Meter percent={Number.isFinite(percent) ? percent : 50} color={color} valueLabel={value} />;
}
