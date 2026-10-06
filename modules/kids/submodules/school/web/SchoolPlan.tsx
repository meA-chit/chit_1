import { useState } from 'react';
import { ApiError, CardFrame, ChipGroup, Empty, Notice, PlusIcon, SelectField, Skeleton, TextField } from '@chit/core';
import { dayShort, useSchoolPlan, useSend, WEEKDAY_NAMES, type Slot } from '../../../shared/kids';

const KINDS: [string, string][] = [['lesson', 'Lesson'], ['break', 'Recess or break'], ['meal', 'Meal'], ['care', 'After-school care']];
const KIND_LABEL: Record<string, string> = { lesson: 'Lesson', break: 'Recess', meal: 'Meal', care: 'Care' };
interface Draft { id: string | null; start: string; end: string; title: string; kind: string; note: string }
const blank = (start = '08:00'): Draft => ({ id: null, start, end: '', title: '', kind: 'lesson', note: '' });

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
    <CardFrame title="School day" state="manual" subtitle={`${name} · typed in by a parent, not read from the school`} tone="#8b7bff"
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
