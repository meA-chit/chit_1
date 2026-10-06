import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, ApiError, Empty, PersonAvatar, PlusIcon, Skeleton, type SettingsSectionProps } from '@chit/core';
import { ReminderForm } from '../../../shared/forms';
import { describeDays, describePart, useDayParts, type DayPart } from '../../../shared/schedule';
import { emptyReminder, KEYS, useRemove, useSaveReminder, type Reminder, type ReminderDraft } from '../../../shared/tasks';

const when = (row: Reminder, parts: DayPart[]) =>
  `${row.on_date ? new Date(`${row.on_date}T12:00:00`).toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' }) : describeDays(row.weekdays)} · ${describePart(row.day_part, parts)}`;

/** Reminders section of the household settings screen: one-off reminders on a chosen date, in a part of the day. */
export default function RemindersSettings({ members }: SettingsSectionProps) {
  const parts = useDayParts();
  const list = useQuery({ queryKey: [...KEYS.reminders, 'all'], queryFn: () => api<{ reminders: Reminder[] }>('/api/planner/reminders') });
  const [draft, setDraft] = useState<ReminderDraft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const save = useSaveReminder(() => { setDraft(null); setError(null); });
  const remove = useRemove('reminders');
  const failed = (e: unknown) => setError(e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was saved.');

  if (list.isPending || parts.isPending) return <Skeleton lines={3} />;
  if (list.isError || parts.isError) return <Empty title="Reminders unavailable">The hub could not be reached.</Empty>;
  const byId = new Map(members.map((m) => [m.id, m]));
  const dayParts = parts.data.day_parts;
  const props = { members, dayParts, busy: save.isPending, error, onCancel: () => setDraft(null) };

  return (
    <div className="stack">
      <p className="field__hint" style={{ margin: 0 }}>
        One-off reminders for a person or the whole family, on a date you pick and in a part of the day. They appear in that zone on the day's timeline. Chit does not send alerts.
      </p>
      {list.data.reminders.length === 0 && !draft && <Empty title="No reminders yet">Add one below.</Empty>}
      {list.data.reminders.map((row) => {
        const who = row.member_id ? byId.get(row.member_id) : undefined;
        return (
          <div key={row.id} className="subcard">
            {draft?.id !== row.id ? (
              <div className="subcard__head">
                <div className="row">
                  <PersonAvatar kind={who?.avatar ?? 'home'} color={who?.color ?? '#8d9bc2'} size={36} />
                  <div>
                    <div className="subcard__title">{row.title}</div>
                    <div className="eyebrow">{who ? who.name.split(' ')[0] : 'Everyone'} · {when(row, dayParts)}</div>
                  </div>
                </div>
                <button type="button" className="btn btn--ghost" onClick={() => { setError(null); setDraft({ id: row.id, title: row.title, member_id: row.member_id ?? '', on_date: row.on_date ?? emptyReminder().on_date, day_part: row.day_part }); }}>Edit</button>
              </div>
            ) : (
              <ReminderForm {...props} draft={draft} setDraft={setDraft} onSave={() => save.mutate(draft, { onError: failed })} onRemove={() => remove.mutate(row.id, { onSuccess: () => setDraft(null) })} />
            )}
          </div>
        );
      })}
      {draft && draft.id === null ? (
        <div className="subcard"><ReminderForm {...props} draft={draft} setDraft={setDraft} onSave={() => save.mutate(draft, { onError: failed })} /></div>
      ) : (
        <div><button type="button" className="btn" onClick={() => { setError(null); setDraft(emptyReminder()); }}><PlusIcon />Add a reminder</button></div>
      )}
    </div>
  );
}
