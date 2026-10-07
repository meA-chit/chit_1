import { useState } from 'react';
import { ApiError, CardFrame, CheckIcon, ChipGroup, Empty, Notice, PillIcon, PlusIcon, SelectField, Skeleton, TextField, type Person } from '@chit/core';
import { dayShort, num, useMeds, useSend, WEEKDAY_NAMES, type DoseStatus, type Med } from '../../../shared/kids';

interface Draft { id: string | null; name: string; dose: string; time: string; weekdays: string[]; remind: string; supply: string }
const blank = (): Draft => ({ id: null, name: '', dose: '', time: '08:00', weekdays: [], remind: '', supply: '' });

export function DoseButtons({ med }: { med: Med }) {
  const send = useSend();
  const set = (status: DoseStatus) => send.mutate({ method: 'POST', path: `/api/kids/health/meds/${med.id}/log`, body: { status } });
  const now = med.today.status;
  if (!med.today.due) return <span className="eyebrow">Not today</span>;
  return (
    <div className="kd-actions">
      <button type="button" className="btn kd-small" aria-pressed={now === 'given'} onClick={() => set(now === 'given' ? null : 'given')}>{now === 'given' ? 'Given' : 'Mark given'}</button>
      <button type="button" className="btn btn--ghost kd-small" aria-pressed={now === 'missed'} onClick={() => set(now === 'missed' ? null : 'missed')}>Missed</button>
    </div>
  );
}

/**
 * The week at a glance for one child's medication, with adding and editing inline in the same widget:
 * today's doses, the given/missed log for the week and the supply. Parents only.
 */
export default function MedsWeek({ memberId, name, adults }: { memberId: string; name: string; adults: Person[] }) {
  const meds = useMeds(memberId);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const send = useSend();
  const fail = (e: unknown) => setError(e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was saved.');
  const frame = { title: 'Week & medication', icon: <PillIcon />, tone: '#4df0ff' } as const;

  if (meds.isPending) return <CardFrame {...frame} state="unconfigured"><Skeleton lines={4} /></CardFrame>;
  if (meds.isError) return <CardFrame {...frame} state="unavailable"><Empty title="Medication unavailable">The hub could not be reached.</Empty></CardFrame>;
  const list = meds.data.meds;
  const who = (id: string | null) => adults.find((a) => a.id === id)?.name.split(' ')[0];
  const edit = (m: Med) => { setError(null); setDraft({ id: m.id, name: m.name, dose: m.dose ?? '', time: m.time, weekdays: m.weekdays, remind: m.remind_member_id ?? '', supply: m.supply === null ? '' : String(m.supply) }); };
  const save = () => {
    if (!draft) return;
    const body = { member_id: memberId, name: draft.name, dose: draft.dose || null, time: draft.time, weekdays: draft.weekdays.map((d) => WEEKDAY_NAMES.indexOf(d)), remind_member_id: draft.remind || null, supply: num(draft.supply) };
    send.mutate(draft.id ? { method: 'PUT', path: `/api/kids/health/meds/${draft.id}`, body } : { method: 'POST', path: '/api/kids/health/meds', body }, { onSuccess: () => { setDraft(null); setError(null); }, onError: fail });
  };

  return (
    <CardFrame {...frame} state="manual" subtitle={`${name} · parents only, never on a shared screen`} provenance={['entered in Chit, parents only']}>
      <div className="stack" style={{ gap: 10 }}>
        <div className="kd-dots kd-dots--head" aria-hidden>{WEEKDAY_NAMES.map((d) => <span key={d}>{dayShort(d).slice(0, 2)}</span>)}</div>
        {list.length === 0 && !draft && <p className="field__hint" style={{ margin: 0 }}>No medication for {name}.</p>}
        {list.map((med) => (
          <div key={med.id} className="kd-med">
            <div className="kd-row__main">
              <div className="kd-row__title">{med.name} <span className="mono" style={{ color: 'var(--text-dim)', fontSize: '0.76rem' }}>{med.time}</span></div>
              <div className="kd-row__sub">{med.dose ?? 'No dose noted'}{who(med.remind_member_id) ? ` · reminds ${who(med.remind_member_id)}` : ''}</div>
            </div>
            <div className="kd-dots kd-dots--small" role="group" aria-label={`${med.name} this week`}>
              {med.week.map((d, i) => (
                <span key={d.day} className="kd-dot" data-status={d.status ?? undefined} data-off={!d.due || undefined} title={`${dayShort(WEEKDAY_NAMES[i]!)}: ${!d.due ? 'not due' : d.status ?? 'open'}`}>
                  {d.status === 'given' ? <CheckIcon /> : d.status === 'missed' ? '×' : ''}
                </span>
              ))}
            </div>
            <div className="kd-med__foot">
              <DoseButtons med={med} />
              {med.supply !== null && <span className="badge" data-state={med.refill_soon ? 'stale' : 'unconfigured'}>{med.refill_soon ? `Refill in ${med.days_left} days` : `Supply ${med.days_left} days`}</span>}
              <button type="button" className="btn btn--ghost kd-small" onClick={() => edit(med)}>Edit</button>
            </div>
          </div>
        ))}
        {draft ? (
          <div className="subcard">
            <div className="subcard__title">{draft.id ? 'Edit reminder' : 'Add a reminder'}</div>
            <div className="form-grid">
              <TextField label="Medication" value={draft.name} onChange={(n) => setDraft({ ...draft, name: n })} wide />
              <TextField label="Dose" value={draft.dose} placeholder="1 tablet after dinner" onChange={(dose) => setDraft({ ...draft, dose })} />
              <TextField label="Time" type="time" value={draft.time} onChange={(time) => setDraft({ ...draft, time })} />
              <SelectField label="Reminds" value={draft.remind} options={[['', 'Nobody'], ...adults.map((a): [string, string] => [a.id, a.name])]} onChange={(remind) => setDraft({ ...draft, remind })} />
              <TextField label="Supply left (doses)" type="number" min={0} value={draft.supply} onChange={(supply) => setDraft({ ...draft, supply })} hint="Optional. Each dose given uses one." />
            </div>
            <ChipGroup label="Days" selected={draft.weekdays} onChange={(weekdays) => setDraft({ ...draft, weekdays })} options={WEEKDAY_NAMES.map((d) => ({ value: d, label: dayShort(d) }))} hint="None selected means every day." />
            {error && <Notice tone="error">{error}</Notice>}
            <div className="row">
              <button type="button" className="btn" disabled={!draft.name.trim() || send.isPending} onClick={save}>Save</button>
              <button type="button" className="btn btn--ghost" onClick={() => { setDraft(null); setError(null); }}>Cancel</button>
              {draft.id && <button type="button" className="btn btn--danger" onClick={() => send.mutate({ method: 'DELETE', path: `/api/kids/health/meds/${draft.id}` }, { onSuccess: () => setDraft(null) })}>Remove</button>}
            </div>
          </div>
        ) : <div><button type="button" className="btn btn--ghost kd-small" onClick={() => { setError(null); setDraft(blank()); }}><PlusIcon />Add medication</button></div>}
      </div>
    </CardFrame>
  );
}
