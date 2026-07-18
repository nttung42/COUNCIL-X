import { useState } from 'react';
import { WorkflowPageLayout } from '../app/layout/AppLayout';
import { navigate, type RouteId } from '../app/routes';
import { DEMO_CASE_ID } from '../app/workflowSteps';
import { Badge, Card, Meter, Qmark, SectionHeading, StatTile } from '../components/common/ui';

export interface WorkflowCard {
  tone?: 'good' | 'warning' | 'serious' | 'critical';
  title: string;
  description: string;
  meta?: string;
}

export interface WorkflowMetric {
  label: string;
  value: string;
  sub: string;
  tone?: string;
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
  cards: WorkflowCard[];
  footerHint: string;
  primaryLabel: string;
  nextRoute?: RouteId;
  secondaryLabel?: string;
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
          <div className="welcome-avatar">{config.agentIcon}</div>
          <div className="welcome-title">{config.welcomeTitle}</div>
          <div className="welcome-text">{config.welcomeText}</div>
          <div className="suggest-label">Câu hỏi gợi ý</div>
          <div className="suggest-chips">
            {config.chips.map((chip) => (
              <button key={chip} type="button" className="chip" onClick={() => send(chip)}>
                <span className="ic">💬</span>
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

          <div className="flow-progress">
            {config.progress.map((step, index) => (
              <div key={step} className="flow-step done">
                <span className="flow-ic">{index + 1}</span>
                {step}
              </div>
            ))}
          </div>

          <Card>
            <SectionHeading>
              {config.summaryTitle} <Qmark text={config.loadingText} />
            </SectionHeading>
            {config.metrics && (
              <div className="grid c4">
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
            <div className="workflow-card-list">
              {config.cards.map((card) => (
                <div key={card.title} className="flag-row">
                  <Badge tone={card.tone ?? 'good'} />
                  <div>
                    <b>{card.title}</b>
                    <p>{card.description}</p>
                    {card.meta && <div className="meta">{card.meta}</div>}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
        <div className="info-footer">
          <div className="footer-hint">{config.footerHint}</div>
          <div className="footer-btns">
            {config.secondaryLabel && <button type="button" className="footer-back-btn">{config.secondaryLabel}</button>}
            <button type="button" className="primary-btn" onClick={() => config.nextRoute && navigate(config.nextRoute, { caseId })}>
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
