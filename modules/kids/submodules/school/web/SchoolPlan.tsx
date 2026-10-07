import { useState } from 'react';
import { ApiError, CardFrame, ChipGroup, Empty, Notice, PlusIcon, SelectField, Skeleton, TextField } from '@chit/core';
import { dayShort, useSchoolPlan, useSend, WEEKDAY_NAMES, type Slot } from '../../../shared/kids';

const KINDS: [string, string][] = [['lesson', 'Lesson'], ['break', 'Recess or break'], ['meal', 'Meal'], ['care', 'After-school care']];
const KIND_LABEL: Record<string, string> = { lesson: 'Lesson', break: 'Recess', meal: 'Meal', care: 'Care' };
interface Draft { id: string | null; start: string; end: string; title: string; kind: string; note: string }
const blank = (start = '08:00'): Draft => ({ id: null, start, end: '', title: '', kind: 'lesson', note: '' });

/** The whole week as a grid: one row per time slot, one column per weekday. Today's column and the running lesson stand out. */
export function SchoolWeek({ memberId }: { memberId: string }) {
  const plan = useSchoolPlan(memberId);
  if (plan.isPending) return <Skeleton lines={4} />;
  if (plan.isError) return <p className="field__hint" style={{ margin: 0 }}>The school plan could not be loaded.</p>;
  const today = plan.data.today_weekday ?? 0;
  const lessons = plan.data.slots.filter((slot) => slot.kind !== 'care');
  if (lessons.length === 0) return <p className="field__hint" style={{ margin: 0 }}>No school plan yet. Add it under Manage, below.</p>;
  const days = WEEKDAY_NAMES.map((_, i) => i).filter((i) => i < 5 || lessons.some((slot) => slot.weekday === i));
  const rows = [...new Map(lessons.map((slot) => [`${slot.start}|${slot.end}`, slot] as const)).values()].sort((a, b) => a.start.localeCompare(b.start) || a.end.localeCompare(b.end));
  const at = (day: number, row: Slot) => lessons.filter((slot) => slot.weekday === day && slot.start === row.start && slot.end === row.end);
  const period = (row: Slot) => lessons.find((slot) => slot.start === row.start && /period (\d+)/.test(slot.note ?? ''))?.note?.match(/period (\d+)/)?.[1];
  const room = (note: string | null) => note?.replace(/,?\s*period \d+/, '').replace(/^Room /, '').trim() || null;
  const now = plan.data.now;

  return (
    <div className="kd-week-grid-wrap">
      <table className="kd-wg" aria-label="Week plan">
        <thead>
          <tr>
            <th scope="col"><span className="sr-only">Time</span></th>
            {days.map((d) => <th key={d} scope="col" data-today={d === today || undefined}>{dayShort(WEEKDAY_NAMES[d]!)}{d === today ? <small>today</small> : null}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.start}|${row.end}`}>
              <th scope="row"><span className="mono">{row.start}</span><span className="mono">{row.end}</span>{period(row) && <small>{period(row)}.</small>}</th>
              {days.map((d) => {
                const here = at(d, row);
                const active = d === today && now !== undefined && row.start <= now && now < row.end;
                return (
                  <td key={d} data-today={d === today || undefined} data-now={active || undefined} data-empty={here.length === 0 || undefined}>
                    {here.map((slot) => <div key={slot.id} data-kind={slot.kind}><b>{slot.title}</b>{room(slot.note) && <span>{room(slot.note)}</span>}</div>)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Today's timetable (or, with `after`, the after-school care slots) for the Today board. Read-only; editing lives in the page settings. */
export function SchoolToday({ memberId, after = false }: { memberId: string; after?: boolean }) {
  const plan = useSchoolPlan(memberId);
  if (plan.isPending) return <Skeleton lines={3} />;
  if (plan.isError) return <p className="field__hint" style={{ margin: 0 }}>The school day could not be loaded.</p>;
  const today = plan.data.today_weekday ?? 0;
  const slots = plan.data.slots.filter((slot) => slot.weekday === today && (slot.kind === 'care') === after);
  if (slots.length === 0) return <p className="field__hint" style={{ margin: 0 }}>{after ? 'No after-school care today.' : 'No school plan for today.'}</p>;
  return (
    <div className="stack" style={{ gap: 6 }}>
      {slots.map((slot) => {
        const active = plan.data.now !== undefined && slot.start <= plan.data.now && plan.data.now < slot.end;
        return (
          <div key={slot.id} className="kd-slot kd-slot--compact" data-kind={slot.kind} data-now={active || undefined}>
            <span className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>{slot.start}–{slot.end}</span>
            <span className="kd-slot__dot" aria-hidden />
            <div className="kd-row__main"><div className="kd-row__title">{slot.title}{active ? ' · now' : ''}</div>{slot.note && <div className="kd-row__sub">{slot.note}</div>}</div>
            {slot.kind !== 'lesson' && <span className="eyebrow">{KIND_LABEL[slot.kind]}</span>}
          </div>
        );
      })}
    </div>
  );
}

/** The school day for one child: lessons, recess, lunch, care. Typed in by a parent (nothing is read from the school). */
export default function SchoolPlan({ memberId, name, adult }: { memberId: string; name: string; adult: boolean }) {
  const plan = useSchoolPlan(memberId);
  const [picked, setPicked] = useState<number | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [copyTo, setCopyTo] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const send = useSend();
  const fail = (e: unknown) => setError(e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was saved.');

  if (plan.isPending) return <CardFrame title="School day" state="unconfigured"><Skeleton lines={4} /></CardFrame>;
  if (plan.isError) return <CardFrame title="School day" state="unavailable"><Empty title="School day unavailable">The hub could not be reached.</Empty></CardFrame>;
  const today = plan.data.today_weekday ?? 0;
  const weekday = picked ?? today;
  const slots = plan.data.slots.filter((slot) => slot.weekday === weekday);
  const now = weekday === today ? plan.data.now : undefined;

  const save = () => {
    if (!draft) return;
    const body = { member_id: memberId, weekday, start: draft.start, end: draft.end, title: draft.title, kind: draft.kind, note: draft.note || null };
    send.mutate(draft.id ? { method: 'PUT', path: `/api/kids/school/slots/${draft.id}`, body } : { method: 'POST', path: '/api/kids/school/slots', body },
      { onSuccess: () => { setDraft(null); setError(null); }, onError: fail });
  };
  const edit = (slot: Slot) => { setError(null); setDraft({ id: slot.id, start: slot.start, end: slot.end, title: slot.title, kind: slot.kind, note: slot.note ?? '' }); };

  return (
    <CardFrame title="Edit the school day" state="manual" subtitle={`${name} · typed in by a parent, not read from the school`} tone="#8b7bff"
      provenance={['school day entered in Chit']}>
      <div className="stack">
        <div className="seg" role="tablist" aria-label="Weekday" style={{ marginBottom: 0 }}>
          {WEEKDAY_NAMES.map((d, i) => <button key={d} role="tab" aria-selected={weekday === i} onClick={() => { setPicked(i); setDraft(null); }}>{dayShort(d)}{i === today ? ' •' : ''}</button>)}
        </div>
        {slots.length === 0 && <Empty title="Nothing planned">{adult ? `Add the lessons, recess and lunch for ${dayShort(WEEKDAY_NAMES[weekday]!)}.` : 'No school plan for this day.'}</Empty>}
        {slots.map((slot) => {
          const active = now !== undefined && slot.start <= now && now < slot.end;
          return (
            <div key={slot.id} className="kd-slot" data-kind={slot.kind} data-now={active || undefined}>
              <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>{slot.start} to {slot.end}</span>
              <span className="kd-slot__dot" aria-hidden />
              <div className="kd-row__main"><div className="kd-row__title">{slot.title}{active ? ' · now' : ''}</div>{slot.note && <div className="kd-row__sub">{slot.note}</div>}</div>
              {adult ? <button type="button" className="btn btn--ghost kd-small" onClick={() => edit(slot)}>Edit</button> : <span className="eyebrow">{KIND_LABEL[slot.kind]}</span>}
            </div>
          );
        })}
        {adult && draft && (
          <div className="subcard">
            <div className="form-grid">
              <TextField label="From" type="time" value={draft.start} onChange={(start) => setDraft({ ...draft, start })} />
              <TextField label="Until" type="time" value={draft.end} onChange={(end) => setDraft({ ...draft, end })} />
              <TextField label="What" value={draft.title} placeholder="Maths" onChange={(title) => setDraft({ ...draft, title })} />
              <SelectField label="Kind" value={draft.kind} options={KINDS} onChange={(kind) => setDraft({ ...draft, kind })} />
              <TextField label="Note" value={draft.note} placeholder="Room, what to bring" onChange={(note) => setDraft({ ...draft, note })} wide />
            </div>
            {error && <Notice tone="error">{error}</Notice>}
            <div className="row">
              <button type="button" className="btn" disabled={!draft.title.trim() || !draft.end || send.isPending} onClick={save}>Save</button>
              <button type="button" className="btn btn--ghost" onClick={() => { setDraft(null); setError(null); }}>Cancel</button>
              {draft.id && <button type="button" className="btn btn--danger" onClick={() => send.mutate({ method: 'DELETE', path: `/api/kids/school/slots/${draft.id}` }, { onSuccess: () => setDraft(null) })}>Remove</button>}
            </div>
          </div>
        )}
        {adult && !draft && (
          <>
            <div className="row">
              <button type="button" className="btn" onClick={() => { setError(null); setDraft(blank(slots.length ? slots[slots.length - 1]!.end : '08:00')); }}><PlusIcon />Add to this day</button>
            </div>
            {slots.length > 0 && (
              <div className="stack" style={{ gap: 8 }}>
                <ChipGroup label={`Copy ${dayShort(WEEKDAY_NAMES[weekday]!)} to`} selected={copyTo} onChange={setCopyTo}
                  options={WEEKDAY_NAMES.map((d, i) => ({ value: String(i), label: dayShort(d), disabled: i === weekday }))} hint="Replaces what is planned on those days." />
                <div><button type="button" className="btn btn--ghost" disabled={copyTo.length === 0 || send.isPending}
                  onClick={() => send.mutate({ method: 'POST', path: '/api/kids/school/copy', body: { member_id: memberId, from_weekday: weekday, to_weekdays: copyTo.map(Number) } }, { onSuccess: () => setCopyTo([]), onError: fail })}>Copy</button></div>
                {error && <Notice tone="error">{error}</Notice>}
              </div>
            )}
          </>
        )}
      </div>
    </CardFrame>
  );
}
