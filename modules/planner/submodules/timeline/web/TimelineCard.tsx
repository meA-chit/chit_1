import { Fragment, useState } from 'react';
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import {
  api, BellIcon, CardFrame, ClockIcon, Empty, Link, PersonAvatar, Skeleton, useClock, useSurface, useViewer, type CardProps,
} from '@chit/core';
import { AGENDA_KEY, fetchAgenda } from '../../../shared/agenda';
import {
  addDays, dayTitle, fmt, hoursIn, inText, layoutLane, mergeFeedEvents, nextUp, pct, toHours, zoneHours, ticks,
  type Lane, type TimelinePayload, type TimelineReminder, type Zone,
} from '../../../shared/timeline';
import './timeline.css';

export default function TimelineCard({ card }: CardProps) {
  useClock(30_000); // re-render so the NOW marker moves
  const surface = useSurface();
  const { memberId } = useViewer();
  const [date, setDate] = useState<string | null>(null); // null = today
  const timeline = useQuery({
    queryKey: ['planner', 'timeline', date ?? 'today'],
    queryFn: () => api<TimelinePayload>(`/api/planner/timeline/day${date ? `?date=${date}` : ''}`),
    refetchInterval: 5 * 60_000,
    placeholderData: keepPreviousData, // no flash while moving between days
  });
  const agenda = useQuery({ queryKey: AGENDA_KEY, queryFn: fetchAgenda, refetchInterval: 5 * 60_000 });
  const base = { icon: <ClockIcon />, tone: '#4df0ff' } as const;

  if (timeline.isPending) return <CardFrame {...base} title={card.title} state="unavailable"><Skeleton lines={4} /></CardFrame>;
  if (timeline.isError) {
    return <CardFrame {...base} title={card.title} state="unavailable"><Empty title="Timeline unavailable">The hub could not be reached. Nothing is shown rather than a guess.</Empty></CardFrame>;
  }
  const data = timeline.data;
  if (data.state === 'unconfigured') {
    return <CardFrame {...base} title={card.title} state="unconfigured"><Empty title="No household yet" action={<Link className="btn" to="/household">Set up household</Link>}>Today appears here once people are added.</Empty></CardFrame>;
  }

  const shown = data.date ?? '';
  const today = data.today ?? shown;
  const isToday = data.is_today ?? true;
  const maxDate = addDays(today, data.max_days_ahead ?? 14);
  const feedOk = agenda.data && agenda.data.state !== 'unavailable' && agenda.data.reason !== 'unconfigured';
  let lanes: Lane[] = feedOk ? mergeFeedEvents(data.lanes, agenda.data!.events, shown) : data.lanes;
  if (memberId) lanes = lanes.filter((lane) => lane.member_id === memberId || lane.member_id === 'family');
  const reminders = (data.reminders ?? []).filter((r) => !memberId || r.member_id === memberId || r.member_id === null);
  const now = isToday ? hoursIn(data.timezone) : -1;
  const next = isToday ? nextUp(lanes, now) : null;
  const hasContent = lanes.some((lane) => lane.blocks.length > 0) || reminders.length > 0;
  const provenance = ['source: routines and reminders entered in Chit', feedOk ? 'plus calendar feeds' : 'calendar feeds not included'];

  const nav = (
    <div className="tl-nav" role="group" aria-label="Choose day">
      {next && <span className="tl-chip">Next <b>{next.title} · {next.who}</b> in {inText(next.minutes)}</span>}
      {!isToday && <button type="button" className="tl-today" onClick={() => setDate(null)}>Back to today</button>}
      <button type="button" aria-label="Previous day" disabled={isToday} onClick={() => setDate(addDays(shown, -1) === today ? null : addDays(shown, -1))}>‹</button>
      <button type="button" aria-label="Next day" disabled={shown >= maxDate} onClick={() => setDate(addDays(shown, 1))}>›</button>
    </div>
  );
  const frame = { ...base, title: dayTitle(shown, today), state: 'manual' as const, action: nav, provenance };

  if (!hasContent) {
    return (
      <CardFrame {...frame} subtitle="06:00 to 22:00">
        <Empty title={`Nothing is planned for ${isToday ? 'today' : dayTitle(shown, today).toLowerCase()}`} action={<Link className="btn" to="/household">Add routines</Link>}>
          Work hours, school times, activities and reminders show up here. An empty day means nothing was entered, not that everyone is free.
        </Empty>
      </CardFrame>
    );
  }
  const mobile = surface === 'mobile-adult' || surface === 'mobile-kid';
  return (
    <CardFrame {...frame} subtitle={mobile ? undefined : `${new Date(`${shown}T12:00:00`).toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })} · 06:00 to 22:00`}>
      {mobile ? <VerticalAgenda lanes={lanes} now={now} reminders={reminders} zones={data.zones ?? []} /> : <Grid lanes={lanes} now={now} reminders={reminders} zones={data.zones ?? []} />}
    </CardFrame>
  );
}

function BellGlyph() {
  return <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M6 8a6 6 0 1112 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10 21a2 2 0 004 0" /></svg>;
}

/** Blocks too short for a label show a glyph; the full title is in the tooltip and the Next chip. */
function KindGlyph({ kind }: { kind: string }) {
  const common = { width: 14, height: 14, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true } as const;
  if (kind === 'pickup' || kind === 'dropoff' || kind === 'travel') return <svg {...common}><path d="M5 16l1.5-6h11L19 16M4 16h16v3H4zM7 19v1.5M17 19v1.5" /></svg>;
  if (kind === 'commute') return <svg {...common}><path d="M4 12h14M13 7l5 5-5 5" /></svg>;
  return <svg {...common}><path d="M12 3l2.2 5.8L20 11l-5.8 2.2L12 19l-2.2-5.8L4 11l5.8-2.2z" /></svg>;
}

const ROW = 28;

function Grid({ lanes, now, reminders, zones }: { lanes: Lane[]; now: number; reminders: TimelineReminder[]; zones: Zone[] }) {
  const showNow = now >= 6 && now <= 22;
  const byPart = (id: string) => reminders.filter((r) => r.day_part === id);
  const anytime = reminders.filter((r) => r.day_part === null);
  const people = new Map(lanes.map((lane) => [lane.member_id, lane]));
  const chip = (r: TimelineReminder) => {
    const who = r.member_id ? people.get(r.member_id) : undefined;
    return (
      <span key={r.id} className="tl__rem" style={{ ['--c' as string]: who?.color ?? 'var(--violet)' }} title={`${r.title} · ${who ? who.name.split(' ')[0] : 'everyone'}`}>
        <BellGlyph /><span>{r.title}</span>
      </span>
    );
  };
  return (
    <div className="tl-scroll">
      <div className="tl">
        <div className="tl__lab" style={{ border: 0, minHeight: 20 }} />
        <div className="tl__track tl__ruler" aria-hidden>
          {ticks().map((tick) => <span key={tick.hour} className="tl__tick" style={{ left: `${tick.left}%` }}>{tick.label}</span>)}
        </div>

        <div className="tl__lab" style={{ border: 0, alignItems: 'flex-start', paddingTop: 6 }}><span className="eyebrow">Reminders</span></div>
        <div className="tl__zones" style={{ gridTemplateColumns: zones.map((z) => `${zoneHours(z)}fr`).join(' ') }}>
          {zones.map((zone) => (
            <div key={zone.id} className="tl__zone" data-zone={zone.id} title={`${zone.label} ${zone.start} to ${zone.end}`}>
              <span className="tl__zlabel">{zone.label}</span>
              <div className="tl__zrems">{byPart(zone.id).map(chip)}</div>
            </div>
          ))}
        </div>
        {anytime.length > 0 && (
          <>
            <div className="tl__lab" style={{ border: 0, minHeight: 30 }}><span className="eyebrow">Any time</span></div>
            <div className="tl__anytime">{anytime.map(chip)}</div>
          </>
        )}

        {lanes.map((lane) => {
          const { items, rows } = layoutLane(lane.blocks, now);
          return (
            <Fragment key={lane.member_id}>
              <div className="tl__lab" style={{ minHeight: rows * ROW + 12 }} title={lane.role}>
                <PersonAvatar kind={lane.avatar} color={lane.color} size={28} />
                <span>{lane.name.split(' ')[0]}</span>
              </div>
              <div className="tl__track" style={{ minHeight: rows * ROW + 12 }}>
                {items.map(({ block, left, width, past, active, openStart, row }) => (
                  <div key={block.id} className="tl__blk" data-past={past} data-active={active} data-open={openStart} data-compact={width < 8} data-kind={block.kind}
                    title={`${block.title} · ${block.start ?? 'start not set'} to ${block.end}${block.source === 'feed' ? ' · calendar feed' : ''}`}
                    style={{ left: `${left}%`, width: `${width}%`, top: 6 + row * ROW, ['--c' as string]: lane.color ?? 'var(--violet)' }}>
                    {width < 8 ? (block.icon ? <span aria-hidden>{block.icon}</span> : <KindGlyph kind={block.kind} />) : <>{block.icon && <span className="tl__icon" aria-hidden>{block.icon}</span>}{block.title}</>}
                  </div>
                ))}
              </div>
            </Fragment>
          );
        })}
        {showNow && (
          <div className="tl__overlay" aria-hidden>
            <div className="tl__past" style={{ width: `${pct(now)}%` }} />
            <div className="tl__now" style={{ left: `${pct(now)}%` }} />
            <span className="tl__nowtag" style={{ left: `${pct(now)}%` }}>{fmt(now)}</span>
          </div>
        )}
      </div>
    </div>
  );
}

/** Phone layout: what is happening now, then what is next, with a NOW marker (no marker on other days). */
function VerticalAgenda({ lanes, now, reminders, zones }: { lanes: Lane[]; now: number; reminders: TimelineReminder[]; zones: Zone[] }) {
  const isToday = now >= 0;
  const inProgress = isToday ? lanes.flatMap((lane) => lane.blocks.filter((b) => ['work', 'school'].includes(b.kind) && b.start !== null && toHours(b.start) <= now && now < toHours(b.end)).map((b) => ({ lane, b }))) : [];
  const upcoming = lanes
    .flatMap((lane) => lane.blocks.filter((b) => !['work', 'school'].includes(b.kind) && b.start !== null && toHours(b.start) > now).map((b) => ({ lane, b })))
    .sort((x, y) => toHours(x.b.start!) - toHours(y.b.start!)).slice(0, 6);
  const zoneLabel = (id: string | null) => zones.find((z) => z.id === id)?.label ?? 'Any time';
  return (
    <div>
      {inProgress.length > 0 && (
        <div className="va-now"><span className="eyebrow">In progress</span>
          {inProgress.map(({ lane, b }) => <span key={lane.member_id + b.id} className="va-chip"><PersonAvatar kind={lane.avatar} color={null} size={20} selected={false} />{lane.name.split(' ')[0]} · {b.title}</span>)}
        </div>
      )}
      {reminders.length > 0 && (
        <div className="va-now"><span className="eyebrow">Reminders</span>
          {reminders.map((r) => <span key={r.id} className="va-chip"><BellIcon />{zoneLabel(r.day_part)} · {r.title}</span>)}
        </div>
      )}
      <div className="va">
        {isToday && <div className="va__now">NOW {fmt(now)}</div>}
        {upcoming.length === 0 && <div className="va__who" style={{ padding: 8 }}>Nothing more planned.</div>}
        {upcoming.map(({ lane, b }, index) => (
          <div key={lane.member_id + b.id} className="va__item" data-next={isToday && index === 0} style={{ ['--c' as string]: lane.color ?? 'var(--violet)' }}>
            <span className="va__time">{b.start}</span>
            <div style={{ minWidth: 0 }}><div className="va__title">{b.title}</div><div className="va__who">{lane.name.split(' ')[0]}</div></div>
            <PersonAvatar kind={lane.avatar} color={null} size={26} selected={false} />
          </div>
        ))}
      </div>
    </div>
  );
}
