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
      <button type="button" className="btn btn--ghost kd-small" aria-pressed={now === 'missed'} onClick={() => set(now === 'missed' ? null : 'missed')}>{now === 'missed' ? 'Missed' : 'Missed'}</button>
    </div>
  );
}

/** Medication for one child: reminders, today's doses, the week's given/missed log and the supply. Parents only. */
export default function HealthPanel({ memberId, name, adults }: { memberId: string; name: string; adults: Person[] }) {
  const meds = useMeds(memberId);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const send = useSend();
  const fail = (e: unknown) => setError(e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was saved.');

  if (meds.isPending) return <CardFrame title="Medication" state="unconfigured"><Skeleton lines={4} /></CardFrame>;
  if (meds.isError) return <CardFrame title="Medication" state="unavailable"><Empty title="Medication unavailable">The hub could not be reached.</Empty></CardFrame>;
  const list = meds.data.meds;
  const who = (id: string | null) => adults.find((a) => a.id === id)?.name.split(' ')[0];
  const edit = (m: Med) => { setError(null); setDraft({ id: m.id, name: m.name, dose: m.dose ?? '', time: m.time, weekdays: m.weekdays, remind: m.remind_member_id ?? '', supply: m.supply === null ? '' : String(m.supply) }); };
  const save = () => {
    if (!draft) return;
    const body = { member_id: memberId, name: draft.name, dose: draft.dose || null, time: draft.time, weekdays: draft.weekdays.map((d) => WEEKDAY_NAMES.indexOf(d)), remind_member_id: draft.remind || null, supply: num(draft.supply) };
    send.mutate(draft.id ? { method: 'PUT', path: `/api/kids/health/meds/${draft.id}`, body } : { method: 'POST', path: '/api/kids/health/meds', body }, { onSuccess: () => { setDraft(null); setError(null); }, onError: fail });
  };

  return (
    <div className="kd-cols">
      <div className="kd">
        <CardFrame title="This week" state="manual" icon={<PillIcon />} tone="#4df0ff" subtitle={`${name} · tap a dose to mark it given or missed`} provenance={['entered in Chit, parents only']}>
          {list.length === 0 ? <Empty title="No medication">Add a reminder on the right.</Empty> : list.map((med) => (
            <div key={med.id} className="kd-row" style={{ alignItems: 'flex-start', flexWrap: 'wrap' }}>
              <div className="kd-row__main" style={{ minWidth: 160 }}>
                <div className="kd-row__title">{med.name} <span className="mono" style={{ color: 'var(--text-dim)', fontSize: '0.78rem' }}>{med.time}</span></div>
                <div className="kd-row__sub">{med.dose ?? 'No dose noted'}{who(med.remind_member_id) ? ` · reminds ${who(med.remind_member_id)}` : ''}</div>
              </div>
              <div className="kd-dots" role="group" aria-label={`${med.name} this week`}>
                {med.week.map((d, i) => (
                  <span key={d.day} className="kd-dot" data-status={d.status ?? undefined} data-off={!d.due || undefined} title={`${dayShort(WEEKDAY_NAMES[i]!)}: ${!d.due ? 'not due' : d.status ?? 'open'}`}>
                    {d.status === 'given' ? <CheckIcon /> : d.status === 'missed' ? '×' : ''}
                  </span>
                ))}
              </div>
              <div style={{ width: '100%', display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                <DoseButtons med={med} />
                {med.supply !== null && <span className="badge" data-state={med.refill_soon ? 'stale' : 'unconfigured'}>{med.refill_soon ? `Refill in ${med.days_left} days` : `Supply ${med.days_left} days`}</span>}
                <button type="button" className="btn btn--ghost kd-small" onClick={() => edit(med)}>Edit</button>
              </div>
            </div>
          ))}
        </CardFrame>
      </div>
      <div className="kd">
        <CardFrame title={draft?.id ? 'Edit reminder' : 'Add a reminder'} state="manual" tone="#4df0ff">
          {draft ? (
            <div className="stack">
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
          ) : <div><button type="button" className="btn" onClick={() => { setError(null); setDraft(blank()); }}><PlusIcon />Add medication</button></div>}
        </CardFrame>
        <CardFrame title="Privacy" state="manual" tone="#4df0ff">
          <p className="field__hint" style={{ margin: 0 }}>Medication is the strictest class of data. It never appears on the family timeline or a shared screen, and {name}'s own screen does not show it. Entries here are for parents only.</p>
        </CardFrame>
      </div>
    </div>
  );
}

/** Compact list of today's doses for the Today tab. */
export function MedsToday({ memberId }: { memberId: string }) {
  const meds = useMeds(memberId);
  if (meds.isPending) return <Skeleton lines={2} />;
  const due = (meds.data?.meds ?? []).filter((m) => m.today.due);
  if (due.length === 0) return <p className="field__hint" style={{ margin: 0 }}>No medication due today.</p>;
  return (
    <div>
      {due.map((med) => (
        <div key={med.id} className="kd-row">
          <span className="mono" style={{ width: 48, color: 'var(--text-dim)', fontSize: '0.8rem' }}>{med.time}</span>
          <div className="kd-row__main"><div className="kd-row__title">{med.name}</div><div className="kd-row__sub">{med.dose ?? ''}</div></div>
          <DoseButtons med={med} />
        </div>
      ))}
    </div>
  );
}
