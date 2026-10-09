import { AnimatePresence, motion } from 'motion/react';
import { Link } from 'react-router-dom';
import { StateBadge } from '../ui/StateBadge';
import { BoltIcon, CalendarIcon, ClockIcon } from '../ui/icons';
import { countdown, minutesUntil, type Ranked } from './rank';
import type { Moment } from './types';

const KIND_ICON = { time: ClockIcon, money: BoltIcon, info: CalendarIcon } as const;
const SNOOZE_MS = 60 * 60_000;

export interface NowPanelProps {
  ranked: Ranked;
  ready: boolean;
  now: Date;
  /** Wide screens: a docked column that collapses to a strip. Narrow: a drawer opened from the bell. */
  mode: 'docked' | 'drawer';
  open: boolean;
  onOpenChange: (open: boolean) => void;
  snoozedCount: number;
  onHide: (id: string, until: number) => void;
  onRestore: () => void;
}

function Chevron({ flip }: { flip: boolean }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden style={{ transform: flip ? 'scaleX(-1)' : undefined }}>
      <path d="M9 6l6 6-6 6" />
    </svg>
  );
}

function MomentCard({ moment, now, onHide }: { moment: Moment; now: Date; onHide: NowPanelProps['onHide'] }) {
  const Icon = KIND_ICON[moment.kind];
  const soon = minutesUntil(moment, now) <= 60;
  const endOfDay = new Date(now).setHours(23, 59, 59, 999);
  return (
    <motion.article layout initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, x: 16 }} transition={{ duration: 0.25 }}
      className="moment" data-soon={soon || undefined} data-kind={moment.kind} aria-label={moment.title}>
      <div className="moment__kicker"><Icon /><span>{countdown(moment, now)}</span></div>
      <h3 className="moment__title">{moment.title}</h3>
      <p className="moment__reason">{moment.reason}</p>
      {moment.value && <p className="moment__value">{moment.value.label}{moment.value.estimated ? ' (estimate)' : ''}</p>}
      <div className="moment__trust">
        <StateBadge state={moment.state} />
        <span className="moment__source">{moment.source}</span>
      </div>
      <div className="moment__actions">
        {moment.action && <Link className="moment__link" to={moment.action.to}>{moment.action.label}</Link>}
        <span className="moment__spacer" />
        <button type="button" className="moment__btn" onClick={() => onHide(moment.id, now.getTime() + SNOOZE_MS)}>Snooze 1 h</button>
        <button type="button" className="moment__btn" onClick={() => onHide(moment.id, endOfDay)}>Done</button>
      </div>
    </motion.article>
  );
}

function Strip({ ranked, now, onOpen }: { ranked: Ranked; now: Date; onOpen: () => void }) {
  const first = ranked.hero[0];
  return (
    <button type="button" className="now-strip" onClick={onOpen} aria-label={`Open Now panel, ${ranked.hero.length} items`}>
      <span className="now-strip__count" data-soon={(first && minutesUntil(first, now) <= 60) || undefined}>{ranked.hero.length}</span>
      {first && <span className="now-strip__next">{countdown(first, now).replace('in ', '')}</span>}
      {ranked.hero.map((moment) => { const Icon = KIND_ICON[moment.kind]; return <span key={moment.id} className="now-strip__icon"><Icon /></span>; })}
      <Chevron flip />
    </button>
  );
}

/** The always-on right panel: a few ranked moments, each with its reason, source and data state. Read-only. */
export function NowPanel({ ranked, ready, now, mode, open, onOpenChange, snoozedCount, onHide, onRestore }: NowPanelProps) {
  if (mode === 'docked' && !open) return <aside className="now now--strip" aria-label="Now"><Strip ranked={ranked} now={now} onOpen={() => onOpenChange(true)} /></aside>;
  if (mode === 'drawer' && !open) return null;
  return (
    <aside className="now" data-mode={mode} aria-label="Now">
      <header className="now__head">
        <h2>Now</h2>
        <button type="button" className="iconbtn" onClick={() => onOpenChange(false)} aria-label="Close Now panel"><Chevron flip={false} /></button>
      </header>
      <div className="now__list" aria-live="polite">
        {!ready && ranked.hero.length === 0 && <div className="moment moment--skeleton" aria-busy="true"><div className="skel" /><div className="skel skel--short" /></div>}
        <AnimatePresence initial={false}>
          {ranked.hero.map((moment) => <MomentCard key={moment.id} moment={moment} now={now} onHide={onHide} />)}
        </AnimatePresence>
        {ready && ranked.hero.length === 0 && (
          <div className="now__empty"><strong>Nothing needs you right now</strong><p>Chit will show a card here when a time or price makes something worth acting on.</p></div>
        )}
        {ranked.quiet.length > 0 && (
          <details className="now__quiet">
            <summary>{ranked.quiet.length} more, later</summary>
            <ul>
              {ranked.quiet.map((moment) => (
                <li key={moment.id}><span>{moment.title}</span><span className="now__when">{countdown(moment, now)}</span></li>
              ))}
            </ul>
          </details>
        )}
        {snoozedCount > 0 && <button type="button" className="moment__btn now__restore" onClick={onRestore}>Show {snoozedCount} snoozed or done</button>}
      </div>
      <details className="now__why">
        <summary>Why these?</summary>
        <p>Shown by how soon they matter, then by how solid the data is. Live data ranks above forecasts and stale readings. Demo and unavailable data never gets a card. Chit only suggests; it changes nothing.</p>
      </details>
    </aside>
  );
}
