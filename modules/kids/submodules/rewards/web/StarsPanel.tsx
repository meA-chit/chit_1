import { CardFrame, CheckIcon, Empty, StarIcon, Toggle } from '@chit/core';
import { dayShort, useSend, type StarChild } from '../../../shared/kids';

/** Today's star chores with the three outcomes a parent can give: Done (just ticked), Done well (green star), Try again. */
export function TodayStars({ child, adult, part, empty = 'No chores today.' }: { child: StarChild; adult: boolean; part?: 'morning' | 'after'; empty?: string }) {
  const send = useSend();
  const outcome = (chore: string, value: 'well' | 'again' | null) => send.mutate({ method: 'POST', path: '/api/kids/stars/outcome', body: { chore_id: chore, outcome: value } });
  const dayPart = (id: string) => child.chores.find((c) => c.id === id)?.day_part ?? null;
  const list = child.today.filter((chore) => !part || (part === 'morning') === (dayPart(chore.id) === 'morning'));
  if (list.length === 0) return <p className="field__hint" style={{ margin: 0 }}>{empty}</p>;
  return (
    <div>
      {list.map((chore) => (
        <div key={chore.id} className="kd-row">
          <span className="badge" data-state={chore.done ? 'available' : 'unconfigured'} style={{ minWidth: 28, justifyContent: 'center' }} aria-label={chore.done ? 'Done' : 'Not done yet'}>{chore.done ? <CheckIcon /> : ''}</span>
          <div className="kd-row__main">
            <div className="kd-row__title" style={chore.done ? { color: 'var(--text-dim)' } : undefined}>{chore.title}</div>
            <div className="kd-row__sub">{!chore.star ? 'Tick only' : chore.outcome === 'well' ? 'Green star' : chore.outcome === 'again' ? 'Try again' : chore.done ? 'Waiting for a parent' : 'Star chore'}</div>
          </div>
          {chore.star && chore.outcome === 'well' && <span className="kd-star"><StarIcon /></span>}
          {adult && chore.star && chore.done && (
            <div className="kd-actions">
              <button type="button" className="btn kd-small" aria-pressed={chore.outcome === 'well'} onClick={() => outcome(chore.id, chore.outcome === 'well' ? null : 'well')}>Done well</button>
              <button type="button" className="btn btn--ghost kd-small" aria-pressed={chore.outcome === 'again'} onClick={() => outcome(chore.id, chore.outcome === 'again' ? null : 'again')}>Try again</button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export function StarsSummary({ child }: { child: StarChild }) {
  const top = Math.max(1, ...child.week.map((d) => d.stars));
  return (
    <div className="stack">
      <div className="row" style={{ alignItems: 'center', gap: 22 }}>
        <div><div className="kd-big">{child.stars_total}</div><div className="field__hint">stars in total</div></div>
        <p className="field__hint" style={{ margin: 0, flex: 1 }}>{child.stars_week} this week. Stars are never spent: they count toward every active goal.</p>
      </div>
      <div className="kd-week" aria-label="Stars this week">
        {child.week.map((d, i) => (
          <div key={d.day}><span style={{ height: 96, display: 'flex', alignItems: 'flex-end', width: '100%', justifyContent: 'center' }}><i data-has={d.stars > 0 || undefined} style={{ height: d.stars ? 14 + (d.stars / top) * 80 : 4 }} /></span><span>{dayShort(['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'][i]!)}</span><span>{d.stars}</span></div>
        ))}
      </div>
    </div>
  );
}

/** Settings for stars: which chores count, and how a chore finishes. Parents only; lives at the bottom of the Kids page. */
export function StarsSettings({ child }: { child: StarChild }) {
  const send = useSend();
  const name = child.name.split(' ')[0] ?? child.name;
  return (
    <>
      <CardFrame title="Chores and what counts" state="manual" subtitle="Chores come from the planner; stars belong to Kids" tone="#8dffb0">
        {child.chores.length === 0 ? <Empty title="No chores for this child yet">Add chores in the household settings and assign them to {name}.</Empty> : child.chores.map((chore) => (
          <div key={chore.id} className="kd-row">
            <div className="kd-row__main"><div className="kd-row__title">{chore.title}</div><div className="kd-row__sub">{chore.weekdays.length ? chore.weekdays.map(dayShort).join(', ') : 'Every day'}{chore.day_part ? ` · ${chore.day_part}` : ''}</div></div>
            <Toggle label="Star chore" checked={chore.star} onChange={(enabled) => send.mutate({ method: 'PUT', path: `/api/kids/stars/chores/${chore.id}`, body: { enabled } })} />
          </div>
        ))}
        <p className="field__hint" style={{ margin: '12px 0 0' }}><b>Done</b> keeps the streak. <b>Done well</b> gives a green star. <b>Try again</b> gives nothing and takes nothing away. Stars are only ever added; a chore that was not done stays open and never counts against anyone.</p>
      </CardFrame>
    </>
  );
}
