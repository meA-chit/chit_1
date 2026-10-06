import { useState } from 'react';
import { Notice, SelectField, TextField, ChipGroup, type Person } from '@chit/core';
import { WhenFields, type DayPart } from './schedule';
import { localDate, type ChoreDraft, type ReminderDraft } from './tasks';

/** The one chore form: used in household settings and on the dashboard so both behave the same. */
export function ChoreForm({ draft, setDraft, members, dayParts, busy, error, onSave, onCancel, onRemove }: {
  draft: ChoreDraft; setDraft: (d: ChoreDraft) => void; members: Person[]; dayParts: DayPart[];
  busy: boolean; error: string | null; onSave: () => void; onCancel: () => void; onRemove?: () => void;
}) {
  const [confirm, setConfirm] = useState(false);
  return (
    <form className="stack" onSubmit={(event) => { event.preventDefault(); if (draft.title.trim()) onSave(); }}>
      <div className="form-grid">
        <TextField label="Chore" value={draft.title} placeholder="e.g. Empty the dishwasher" onChange={(title) => setDraft({ ...draft, title })} required />
        <SelectField label="Who" value={draft.assignee_id} onChange={(assignee_id) => setDraft({ ...draft, assignee_id })}
          options={[['', 'Anyone'], ...members.map((m): [string, string] => [m.id, m.name])]} />
      </div>
      <WhenFields weekdays={draft.weekdays} onWeekdays={(weekdays) => setDraft({ ...draft, weekdays })}
        dayPart={draft.day_part} onDayPart={(day_part) => setDraft({ ...draft, day_part })} parts={dayParts} />
      {error && <Notice tone="error">{error}</Notice>}
      <div className="row">
        <button type="submit" className="btn btn--primary" disabled={busy || !draft.title.trim()}>{draft.id ? 'Save chore' : 'Add chore'}</button>
        <button type="button" className="btn btn--ghost" onClick={onCancel}>Cancel</button>
        {onRemove && !confirm && <button type="button" className="btn btn--danger" onClick={() => setConfirm(true)}>Remove</button>}
        {onRemove && confirm && <button type="button" className="btn btn--danger" onClick={onRemove}>Yes, remove (history is kept)</button>}
      </div>
    </form>
  );
}

/** Reminders are one-off: pick a date (Today, Tomorrow or any day), a part of the day, and who it is for. */
export function ReminderForm({ draft, setDraft, members, dayParts, busy, error, onSave, onCancel, onRemove }: {
  draft: ReminderDraft; setDraft: (d: ReminderDraft) => void; members: Person[]; dayParts: DayPart[];
  busy: boolean; error: string | null; onSave: () => void; onCancel: () => void; onRemove?: () => void;
}) {
  const [confirm, setConfirm] = useState(false);
  const quick = draft.on_date === localDate(0) ? 'today' : draft.on_date === localDate(1) ? 'tomorrow' : '';
  return (
    <form className="stack" onSubmit={(event) => { event.preventDefault(); if (draft.title.trim()) onSave(); }}>
      <div className="form-grid">
        <TextField label="Reminder" value={draft.title} placeholder="e.g. Pack the swimming bag" onChange={(title) => setDraft({ ...draft, title })} required />
        <SelectField label="For" value={draft.member_id} onChange={(member_id) => setDraft({ ...draft, member_id })}
          options={[['', 'Everyone'], ...members.map((m): [string, string] => [m.id, m.name])]} />
      </div>
      <ChipGroup label="Day" single selected={quick ? [quick] : []} options={[{ value: 'today', label: 'Today' }, { value: 'tomorrow', label: 'Tomorrow' }]}
        onChange={(sel) => sel[0] && setDraft({ ...draft, on_date: localDate(sel[0] === 'today' ? 0 : 1) })} />
      <div className="form-grid">
        <TextField label="Or pick a date" type="date" min={undefined} value={draft.on_date} onChange={(on_date) => on_date && setDraft({ ...draft, on_date })} />
      </div>
      <WhenFields weekdays={[]} onWeekdays={() => undefined} showDays={false} dayPart={draft.day_part} onDayPart={(day_part) => setDraft({ ...draft, day_part })} parts={dayParts} />
      {error && <Notice tone="error">{error}</Notice>}
      <div className="row">
        <button type="submit" className="btn btn--primary" disabled={busy || !draft.title.trim() || !draft.on_date}>{draft.id ? 'Save reminder' : 'Add reminder'}</button>
        <button type="button" className="btn btn--ghost" onClick={onCancel}>Cancel</button>
        {onRemove && !confirm && <button type="button" className="btn btn--danger" onClick={() => setConfirm(true)}>Remove</button>}
        {onRemove && confirm && <button type="button" className="btn btn--danger" onClick={onRemove}>Yes, remove</button>}
      </div>
    </form>
  );
}
