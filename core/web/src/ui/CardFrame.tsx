import type { CSSProperties, ReactNode } from 'react';
import type { DataState } from '../api/types';
import { StateBadge } from './StateBadge';

interface Props {
  title: string;
  state: DataState;
  children: ReactNode;
  subtitle?: string;
  /** Icon chip, tinted by `tone`. Every card uses the same header grammar. */
  icon?: ReactNode;
  tone?: string;
  /** One action on the right of the header (a link or button). */
  action?: ReactNode;
  /** Provenance lines: source, observed/checked time. Required by ADR-0003 for normalized data. */
  provenance?: string[];
  /** Inside a tabbed panel the panel supplies the frame; the card renders only its body. */
  embedded?: boolean;
}

export function CardFrame({ title, state, children, subtitle, icon, tone, action, provenance = [], embedded }: Props) {
  if (embedded) {
    return (
      <div>
        <div className="embedded__meta">
          <StateBadge state={state} />
          {provenance.length > 0 && <span className="card__foot" style={{ margin: 0, padding: 0, border: 0 }}>{provenance.join(' · ')}</span>}
        </div>
        {children}
      </div>
    );
  }
  return (
    <section className="card" aria-label={title} style={tone ? ({ '--c': tone } as CSSProperties) : undefined}>
      <header className="card__head">
        {icon && <div className="card__icon">{icon}</div>}
        <div className="card__titles">
          <h2 className="card__title">{title}</h2>
          {subtitle && <p className="card__subtitle">{subtitle}</p>}
        </div>
        {action}
        <StateBadge state={state} />
      </header>
      <div className="card__body">{children}</div>
      {provenance.length > 0 && (
        <footer className="card__foot">
          {provenance.map((line) => <span key={line}>{line}</span>)}
        </footer>
      )}
    </section>
  );
}

export function Skeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div aria-busy="true" aria-label="Loading">
      {Array.from({ length: lines }, (_, i) => (
        <div key={i} className="skeleton" style={{ width: `${90 - i * 18}%` }} />
      ))}
    </div>
  );
}

export function Empty({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="empty">
      <strong>{title}</strong>
      {children}
      {action && <div style={{ marginTop: 14 }}>{action}</div>}
    </div>
  );
}
