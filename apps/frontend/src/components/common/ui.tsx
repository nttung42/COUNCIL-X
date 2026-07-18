import type { CSSProperties, ReactNode } from 'react';
import type { EditStatusFlag } from '../../state/caseStore';

function statusClass(status?: EditStatusFlag): string {
  if (status === 'pending') return ' pending-edit';
  if (status === 'confirmed') return ' edited';
  return '';
}

export function EditedBadge({ status }: { status: EditStatusFlag }) {
  if (status === 'none') return null;
  return (
    <span className={'edited-badge' + (status === 'confirmed' ? ' confirmed' : '')}>
      {status === 'confirmed' ? '✓ Đã xác nhận' : 'Đang chờ xác nhận'}
    </span>
  );
}

export function Card({
  children,
  className = '',
  status,
  id,
  style,
}: {
  children: ReactNode;
  className?: string;
  status?: EditStatusFlag;
  id?: string;
  style?: CSSProperties;
}) {
  return (
    <div id={id} className={`card ${className}${statusClass(status)}`.trim()} style={style}>
      {children}
    </div>
  );
}

export function Qmark({ text }: { text: string }) {
  return (
    <span className="qmark" data-why={text}>
      ?
    </span>
  );
}

export function SectionHeading({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="section-h">
      {children}
      {action}
    </div>
  );
}

const BADGE_LABEL: Record<string, string> = {
  good: 'Đã xác thực',
  warning: 'Lưu ý',
  serious: 'Cần lưu ý',
  critical: 'Nghiêm trọng',
};

export function Badge({
  tone,
  children,
}: {
  tone: 'good' | 'warning' | 'serious' | 'critical';
  children?: ReactNode;
}) {
  return (
    <span className={`badge ${tone}`}>
      <span className="dot" />
      {children ?? BADGE_LABEL[tone]}
    </span>
  );
}

export function StatTile({
  label,
  value,
  sub,
  qmark,
  id,
  status,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  qmark?: string;
  id?: string;
  status?: EditStatusFlag;
}) {
  return (
    <Card className="stat-tile" id={id} status={status}>
      <div className="label">
        {label}
        {qmark && <Qmark text={qmark} />}
      </div>
      <div className="value">{value}</div>
      {sub && <div className="sub">{sub}</div>}
    </Card>
  );
}

export function BarRow({
  label,
  valueLabel,
  percent,
  color,
  status,
}: {
  label: ReactNode;
  valueLabel: ReactNode;
  percent: number;
  color?: string;
  status?: EditStatusFlag;
}) {
  return (
    <div className={'barrow' + statusClass(status)}>
      <div className="rowlabel">{label}</div>
      <div className="bartrack">
        <div className="barfill" style={{ width: `${percent}%`, background: color }} />
      </div>
      <div className="rowvalue">{valueLabel}</div>
    </div>
  );
}

export function Meter({ percent, color, valueLabel }: { percent: number; color: string; valueLabel: ReactNode }) {
  return (
    <div className="meter-wrap">
      <div className="meter-track">
        <div className="meter-fill" style={{ width: `${percent}%`, background: color }} />
      </div>
      <div className="meter-num">{valueLabel}</div>
    </div>
  );
}

export function Timeline({ children }: { children: ReactNode }) {
  return <div className="timeline">{children}</div>;
}

export function TimelineItem({ time, title, description }: { time: string; title: string; description?: string }) {
  return (
    <div className="tl-item">
      <div className="tl-time">{time}</div>
      <div className="tl-rail">
        <div className="tl-dot" />
        <div className="tl-line" />
      </div>
      <div className="tl-body">
        <b>{title}</b>
        {description && <p>{description}</p>}
      </div>
    </div>
  );
}

export function SourceChip({
  label,
  warn,
  tooltip,
  onClick,
}: {
  label: string;
  warn?: boolean;
  tooltip?: string | null;
  onClick?: () => void;
}) {
  return (
    <span
      className={'src-ref' + (warn ? ' warn' : '')}
      data-src={tooltip ?? ''}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
    >
      {label}
    </span>
  );
}

/** Card lặp lại dạng "ld-head + ld-raw (bullet) + ld-inference + ld-meta" ở màn 2/3/4. */
export function LookupDetailCard({
  id,
  badge,
  title,
  qmark,
  rawLabel = 'Dữ liệu tra cứu được',
  rawFindings,
  inferenceHtml,
  metaText,
  status,
}: {
  id?: string;
  badge?: ReactNode;
  title: string;
  qmark?: string;
  rawLabel?: string;
  rawFindings: string[];
  inferenceHtml: string;
  metaText: string;
  status?: EditStatusFlag;
}) {
  return (
    <Card className="lookup-detail" id={id} status={status}>
      <div className="ld-head">
        {badge}
        <span className="ld-title">{title}</span>
        <EditedBadge status={status ?? 'none'} />
        {qmark && <Qmark text={qmark} />}
      </div>
      <div className="ld-raw">
        <div className="ld-label">{rawLabel}</div>
        <ul>
          {rawFindings.map((line, i) => (
            // eslint-disable-next-line react/no-array-index-key
            <li key={i}>{line}</li>
          ))}
        </ul>
      </div>
      <div className="ld-inference">
        <div className="ld-label">💡 Nhận định của PAA</div>
        {/* eslint-disable-next-line react/no-danger */}
        <p dangerouslySetInnerHTML={{ __html: inferenceHtml }} />
      </div>
      <div className="ld-meta">{metaText}</div>
    </Card>
  );
}

export function FlagRow({
  leading,
  title,
  descriptionHtml,
  meta,
  status,
  onClick,
}: {
  leading: ReactNode;
  title: string;
  descriptionHtml: string;
  meta: string;
  status?: EditStatusFlag;
  onClick?: () => void;
}) {
  return (
    <div
      className={'flag-row' + statusClass(status)}
      style={onClick ? { cursor: 'pointer' } : undefined}
      onClick={onClick}
    >
      {leading}
      <div>
        <b>
          {title}
          <EditedBadge status={status ?? 'none'} />
        </b>
        {/* eslint-disable-next-line react/no-danger */}
        <p dangerouslySetInnerHTML={{ __html: descriptionHtml }} />
        <div className="meta">{meta}</div>
      </div>
    </div>
  );
}
