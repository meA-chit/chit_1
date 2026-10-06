import { useState } from 'react';
import { ApiError, Notice, PlusIcon, StarIcon, TextField, Toggle } from '@chit/core';
import { num, useSend, type Goal } from '../../../shared/kids';

export const Stars = ({ n }: { n: number }) => <span className="mono"><span className="kd-star"><StarIcon /></span> {n}</span>;

/** Goals with progress bars. Parents add, approve and remove; a child's own screen is read-only. */
export function GoalList({ goals, memberId, name, adult }: { goals: Goal[]; memberId: string; name: string; adult: boolean }) {
  const [adding, setAdding] = useState(false);
  const [draft, setDraft] = useState({ title: '', cost: '', note: '', count_existing: false });
  const [error, setError] = useState<string | null>(null);
  const send = useSend();
  const fail = (e: unknown) => setError(e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was saved.');
  const create = () => send.mutate(
    { method: 'POST', path: '/api/kids/goals', body: { member_id: memberId, title: draft.title, cost: num(draft.cost), note: draft.note || null, count_existing: draft.count_existing } },
    { onSuccess: () => { setAdding(false); setDraft({ title: '', cost: '', note: '', count_existing: false }); setError(null); }, onError: fail });

  return (
    <div className="stack">
      {goals.length === 0 && <p className="field__hint" style={{ margin: 0 }}>No goals yet. {adult ? `Add something ${name} can work towards.` : 'Ask a parent to set one.'}</p>}
      {goals.map((goal) => (
        <div key={goal.id} className="kd-goal" data-reached={goal.reached || undefined}>
          <div className="kd-goal__head">
            <div>
              <b>{goal.title}</b>
              {goal.note && <div className="kd-row__sub">{goal.note}</div>}
            </div>
            {goal.status === 'approved' ? <span className="badge" data-state="available">Done</span>
              : goal.reached ? <span className="badge" data-state="available">Reached</span>
              : <Stars n={goal.cost} />}
          </div>
          <div className="kd-bar" role="progressbar" aria-valuenow={goal.pct} aria-valuemin={0} aria-valuemax={100} aria-label={goal.title}><i style={{ width: `${goal.pct}%` }} /></div>
          <div className="kd-goal__foot">
            <span>{goal.have} of {goal.cost} stars</span>
            <span>{goal.reached ? (goal.status === 'approved' ? 'Approved' : 'Waiting for a parent') : `${goal.cost - goal.have} to go`}</span>
          </div>
          {adult && (
            <div className="kd-actions">
              {goal.reached && goal.status !== 'approved' && <button type="button" className="btn kd-small" onClick={() => send.mutate({ method: 'POST', path: `/api/kids/goals/${goal.id}/approve`, body: { approved: true } })}>Approve</button>}
              {goal.status === 'approved' && <button type="button" className="btn btn--ghost kd-small" onClick={() => send.mutate({ method: 'POST', path: `/api/kids/goals/${goal.id}/approve`, body: { approved: false } })}>Reopen</button>}
              <button type="button" className="btn btn--ghost kd-small" onClick={() => send.mutate({ method: 'DELETE', path: `/api/kids/goals/${goal.id}` })}>Remove</button>
            </div>
          )}
        </div>
      ))}
      {adult && (adding ? (
        <div className="subcard">
          <div className="form-grid">
            <TextField label="Goal" value={draft.title} placeholder="Sleepover with friends" onChange={(title) => setDraft({ ...draft, title })} wide />
            <TextField label="Stars needed" type="number" min={1} value={draft.cost} onChange={(cost) => setDraft({ ...draft, cost })} />
            <TextField label="Note" value={draft.note} placeholder="Optional" onChange={(note) => setDraft({ ...draft, note })} />
          </div>
          <Toggle label={`Count the stars ${name} already has`} checked={draft.count_existing} hint="Off: the goal starts fresh today. Stars are never spent either way."
            onChange={(count_existing) => setDraft({ ...draft, count_existing })} />
          {error && <Notice tone="error">{error}</Notice>}
          <div className="row">
            <button type="button" className="btn" disabled={!draft.title.trim() || !draft.cost || send.isPending} onClick={create}>Save goal</button>
            <button type="button" className="btn btn--ghost" onClick={() => { setAdding(false); setError(null); }}>Cancel</button>
          </div>
        </div>
      ) : (
        <div><button type="button" className="btn" onClick={() => setAdding(true)}><PlusIcon />Add a goal</button></div>
      ))}
    </div>
  );
}
