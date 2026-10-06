import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, ApiError, Empty, PersonAvatar, PlusIcon, Skeleton, type SettingsSectionProps } from '@chit/core';
import { ChoreForm } from '../../../shared/forms';
import { describeDays, describePart, useDayParts } from '../../../shared/schedule';
import { emptyChore, KEYS, useRemove, useSaveChore, type ChoreDraft, type ChoreRow } from '../../../shared/tasks';

/** Chores section of the household settings screen. Saves each chore immediately through the planner API. */
export default function ChoresSettings({ members }: SettingsSectionProps) {
  const parts = useDayParts();
  const list = useQuery({ queryKey: [...KEYS.chores, 'all'], queryFn: () => api<{ chores: ChoreRow[] }>('/api/planner/chores') });
  const [draft, setDraft] = useState<ChoreDraft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const save = useSaveChore(() => { setDraft(null); setError(null); });
  const remove = useRemove('chores');
  const failed = (e: unknown) => setError(e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was saved.');

  if (list.isPending || parts.isPending) return <Skeleton lines={3} />;
  if (list.isError || parts.isError) return <Empty title="Chores unavailable">The hub could not be reached.</Empty>;
  const byId = new Map(members.map((m) => [m.id, m]));
  const dayParts = parts.data.day_parts;
  const props = { members, dayParts, busy: save.isPending, error, onCancel: () => setDraft(null) };

  return (
    <div className="stack">
      <p className="field__hint" style={{ margin: 0 }}>
        Chores repeat on chosen days in a part of the day (morning 06-10, day 10-16, evening 16-20). They show on the dashboard with a streak.
      </p>
      {list.data.chores.length === 0 && !draft && <Empty title="No chores yet">Add the first one below.</Empty>}
      {list.data.chores.map((chore) => {
        const who = chore.assignee_id ? byId.get(chore.assignee_id) : undefined;
        return (
          <div key={chore.id} className="subcard">
            {draft?.id !== chore.id ? (
              <div className="subcard__head">
                <div className="row">
                  {who ? <PersonAvatar kind={who.avatar} color={who.color} size={36} /> : <span className="eyebrow">Anyone</span>}
                  <div>
                    <div className="subcard__title">{chore.title}</div>
                    <div className="eyebrow">{who ? who.name.split(' ')[0] : 'Anyone'} · {describeDays(chore.weekdays)} · {describePart(chore.day_part, dayParts)}</div>
                  </div>
                </div>
                <button type="button" className="btn btn--ghost" onClick={() => { setError(null); setDraft({ id: chore.id, title: chore.title, assignee_id: chore.assignee_id ?? '', weekdays: chore.weekdays, day_part: chore.day_part }); }}>Edit</button>
              </div>
            ) : (
              <ChoreForm {...props} draft={draft} setDraft={setDraft} onSave={() => save.mutate(draft, { onError: failed })} onRemove={() => remove.mutate(chore.id, { onSuccess: () => setDraft(null) })} />
            )}
          </div>
        );
      })}
      {draft && draft.id === null ? (
        <div className="subcard"><ChoreForm {...props} draft={draft} setDraft={setDraft} onSave={() => save.mutate(draft, { onError: failed })} /></div>
      ) : (
        <div><button type="button" className="btn" onClick={() => { setError(null); setDraft(emptyChore()); }}><PlusIcon />Add a chore</button></div>
      )}
    </div>
  );
}
