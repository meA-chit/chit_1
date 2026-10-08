import { useEffect, useState } from 'react';
import {
  ApiError, BellIcon, CardFrame, CardsIcon, CheckIcon, Empty, FlameIcon, ListIcon, PersonAvatar, PlusIcon, Skeleton, TrashIcon, UndoIcon, XIcon, useShell, useViewer, type CardProps, type Person,
} from '@chit/core';
import { api } from '@chit/core';
import { useMutation } from '@tanstack/react-query';
import { ChoreForm, ReminderForm } from '../../../shared/forms';
import { describePart, type DayPart } from '../../../shared/schedule';
import {
  emptyChore, emptyReminder, useChoresToday, useRemindersToday, useRemove, useReminderDone, useSaveChore, useSaveReminder, useSkip, usePlannerInvalidate,
  type Chore, type ChoreDraft, type Reminder, type ReminderDraft,
} from '../../../shared/tasks';
import './chores.css';

type Editing = { kind: 'chore'; draft: ChoreDraft } | { kind: 'reminder'; draft: ReminderDraft } | null;
type Undo = { kind: 'chores' | 'reminders'; id: string; title: string } | null;
const MAX_ROWS = 5;
const LAYOUT_KEY = 'chit.todo.layout';
const readLayout = (): 'list' | 'cards' => { try { return localStorage.getItem(LAYOUT_KEY) === 'cards' ? 'cards' : 'list'; } catch { return 'list'; } };

/**
 * One calm place for what needs doing today: chores (tick off, streaks) and one-off reminders.
 * Row actions are the day-to-day operations: skip for today (undoable), edit, remove for good.
 */
export default function TodoCard({ card }: CardProps) {
  const { memberId } = useViewer();
  const shell = useShell();
  const chores = useChoresToday();
  const reminders = useRemindersToday();
  const invalidate = usePlannerInvalidate();
  const [adding, setAdding] = useState<'menu' | null>(null);
  const [editing, setEditing] = useState<Editing>(null);
  const [error, setError] = useState<string | null>(null);
  const [menu, setMenu] = useState<string | null>(null);
  const [confirmRemove, setConfirmRemove] = useState<string | null>(null);
  const [undo, setUndo] = useState<Undo>(null);
  const [showAll, setShowAll] = useState(false);
  const [layout, setLayout] = useState<'list' | 'cards'>(readLayout);
  const switchLayout = () => { const next = layout === 'cards' ? 'list' : 'cards'; setLayout(next); try { localStorage.setItem(LAYOUT_KEY, next); } catch { /* the choice just is not remembered */ } };

  const close = () => { setEditing(null); setAdding(null); setError(null); };
  const saveChore = useSaveChore(close);
  const saveReminder = useSaveReminder(close);
  const removeChore = useRemove('chores');
  const removeReminder = useRemove('reminders');
  const skipChore = useSkip('chores');
  const skipReminder = useSkip('reminders');
  const reminderDone = useReminderDone();
  const toggle = useMutation({
    mutationFn: ({ id, done }: { id: string; done: boolean }) => api(`/api/planner/chores/${id}/toggle`, { method: 'POST', body: JSON.stringify({ done }) }),
    onSettled: invalidate,
  });
  const failed = (e: unknown) => setError(e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was saved.');

  useEffect(() => {
    if (!undo) return;
    const timer = setTimeout(() => setUndo(null), 8000);
    return () => clearTimeout(timer);
  }, [undo]);

  const frame = { title: card.title, icon: <CheckIcon />, tone: '#8dffb0' } as const;
  if (chores.isPending || reminders.isPending) return <CardFrame {...frame} state="unavailable"><Skeleton lines={5} /></CardFrame>;
  if (chores.isError || reminders.isError) return <CardFrame {...frame} state="unavailable"><Empty title="To-do unavailable">The hub could not be reached.</Empty></CardFrame>;

  const people: Person[] = shell.data?.members ?? [];
  const dayParts: DayPart[] = chores.data.day_parts ?? reminders.data.day_parts ?? [];
  // "View as" a member: their chores, and the reminders that are theirs or for everyone
  const forMemberChore = (c: Chore) => !memberId || c.assignee_id === memberId;
  const forMemberReminder = (r: Reminder) => !memberId || r.member_id === memberId || r.member_id === null;
  const choreList = chores.data.chores.filter(forMemberChore);
  const reminderList = reminders.data.reminders.filter(forMemberReminder);
  const skippedChores = chores.data.skipped.filter(forMemberChore);
  const skippedReminders = reminders.data.skipped.filter(forMemberReminder);
  const upcoming = reminders.data.upcoming.filter(forMemberReminder).slice(0, 3);
  const done = choreList.filter((c) => c.done).length;
  const person = (id: string | null | undefined) => people.find((p) => p.id === id);
  const shownChores = showAll ? choreList : choreList.slice(0, MAX_ROWS);
  const shownReminders = showAll ? reminderList : reminderList.slice(0, MAX_ROWS);
  const hidden = choreList.length - shownChores.length + (reminderList.length - shownReminders.length);
  const skippedCount = skippedChores.length + skippedReminders.length;
  const startChore = () => { setAdding(null); setError(null); setEditing({ kind: 'chore', draft: emptyChore(memberId ?? '') }); };
  const startReminder = () => { setAdding(null); setError(null); setEditing({ kind: 'reminder', draft: emptyReminder(memberId ?? '') }); };

  const skip = (kind: 'chores' | 'reminders', id: string, title: string) => {
    (kind === 'chores' ? skipChore : skipReminder).mutate({ id, skipped: true }, { onSuccess: () => setUndo({ kind, id, title }) });
    setMenu(null);
  };
  const restore = (kind: 'chores' | 'reminders', id: string) => { (kind === 'chores' ? skipChore : skipReminder).mutate({ id, skipped: false }); setUndo(null); };

  const editChore = (c: Chore) => { setMenu(null); setError(null); setEditing({ kind: 'chore', draft: { id: c.id, title: c.title, assignee_id: c.assignee_id ?? '', weekdays: (c as Chore & { weekdays?: string[] }).weekdays ?? [], day_part: c.day_part } }); };
  const editReminder = (r: Reminder) => { setMenu(null); setError(null); setEditing({ kind: 'reminder', draft: { id: r.id, title: r.title, member_id: r.member_id ?? '', on_date: r.on_date ?? emptyReminder().on_date, day_part: r.day_part } }); };

  const remove = (kind: 'chores' | 'reminders', id: string, title: string) => {
    if (window.confirm(`Remove “${title}” for good?`)) (kind === 'chores' ? removeChore : removeReminder).mutate(id);
  };
  const choreCardEl = (chore: Chore) => {
    const who = person(chore.assignee_id);
    return (
      <div key={chore.id} className="tcardw" data-done={chore.done}>
        <div className="tcardw__top">
          <span className="tcardw__ic"><CheckIcon /></span>
          <span className="streak" data-zero={chore.streak === 0} title={`${chore.streak} days in a row`}><FlameIcon />{chore.streak}</span>
          <button className="rowbtn" aria-label={`Edit ${chore.title}`} title="Edit" onClick={() => editChore(chore)}>✎</button>
        </div>
        <div className="tcardw__title">{chore.title}</div>
        <div className="chore__sub">{who && <PersonAvatar kind={who.avatar} color={null} size={16} selected={false} />}{who ? who.name.split(' ')[0] : 'Anyone'}{chore.day_part ? ` · ${dayParts.find((p) => p.id === chore.day_part)?.label.toLowerCase() ?? chore.day_part}` : ''}</div>
        <div className="tcardw__act">
          <button className="btn tcardw__ok" onClick={() => toggle.mutate({ id: chore.id, done: !chore.done })}>{chore.done ? <><UndoIcon />Undo</> : <><CheckIcon />Done</>}</button>
          <button className="btn btn--ghost" onClick={() => skip('chores', chore.id, chore.title)}><XIcon />Not relevant</button>
          <button className="btn btn--ghost tcardw__trash" aria-label={`Remove ${chore.title}`} title="Remove for good" onClick={() => remove('chores', chore.id, chore.title)}><TrashIcon /></button>
        </div>
      </div>
    );
  };
  const reminderCardEl = (reminder: Reminder) => {
    const who = person(reminder.member_id);
    return (
      <div key={reminder.id} className="tcardw" data-done={!!reminder.done}>
        <div className="tcardw__top">
          <span className="tcardw__ic" style={{ ['--c' as string]: who?.color ?? 'var(--violet)' }}><BellIcon /></span>
          <button className="rowbtn" aria-label={`Edit ${reminder.title}`} title="Edit" onClick={() => editReminder(reminder)}>✎</button>
        </div>
        <div className="tcardw__title">{reminder.title}</div>
        <div className="chore__sub"><PersonAvatar kind={who?.avatar ?? 'home'} color={null} size={16} selected={false} />{who ? who.name.split(' ')[0] : 'Everyone'} · {(describePart(reminder.day_part, dayParts).split(' (')[0] ?? '').toLowerCase()}</div>
        <div className="tcardw__act">
          <button className="btn tcardw__ok" onClick={() => reminderDone.mutate({ id: reminder.id, done: !reminder.done })}>{reminder.done ? <><UndoIcon />Undo</> : <><CheckIcon />Done</>}</button>
          <button className="btn btn--ghost" onClick={() => skip('reminders', reminder.id, reminder.title)}><XIcon />Not relevant</button>
          <button className="btn btn--ghost tcardw__trash" aria-label={`Remove ${reminder.title}`} title="Remove for good" onClick={() => remove('reminders', reminder.id, reminder.title)}><TrashIcon /></button>
        </div>
      </div>
    );
  };

  const subtitle = `${done} of ${choreList.length} chores done · ${reminderList.length} reminder${reminderList.length === 1 ? '' : 's'}`;
  const addButton = (
    <>
      <button className="card__action" onClick={switchLayout} aria-label={layout === 'cards' ? 'Show as a list' : 'Show as cards'} title={layout === 'cards' ? 'Show as a list' : 'Show as cards'}>{layout === 'cards' ? <ListIcon /> : <CardsIcon />}</button>
      <button className="card__action" onClick={() => { setEditing(null); setAdding(adding ? null : 'menu'); }} aria-expanded={adding === 'menu'} aria-label="Add a chore or reminder"><PlusIcon /></button>
    </>
  );

  return (
    <CardFrame {...frame} state="manual" subtitle={subtitle} action={addButton}
      provenance={[`longest streak ${Math.max(0, ...chores.data.chores.map((c) => c.streak))} days`, 'source: chores and reminders kept in Chit']}>
      {adding === 'menu' && (
        <div className="add-menu">
          <button className="btn" onClick={startChore}><PlusIcon />Chore</button>
          <button className="btn" onClick={startReminder}><BellIcon />Reminder</button>
        </div>
      )}
      {editing?.kind === 'chore' && (
        <div className="form-wrap">
          <ChoreForm draft={editing.draft} setDraft={(draft) => setEditing({ kind: 'chore', draft })} members={people} dayParts={dayParts}
            busy={saveChore.isPending} error={error} onCancel={close}
            onSave={() => saveChore.mutate(editing.draft, { onError: failed })}
            onRemove={editing.draft.id ? () => removeChore.mutate(editing.draft.id!, { onSuccess: close }) : undefined} />
        </div>
      )}
      {editing?.kind === 'reminder' && (
        <div className="form-wrap">
          <ReminderForm draft={editing.draft} setDraft={(draft) => setEditing({ kind: 'reminder', draft })} members={people} dayParts={dayParts}
            busy={saveReminder.isPending} error={error} onCancel={close}
            onSave={() => saveReminder.mutate(editing.draft, { onError: failed })}
            onRemove={editing.draft.id ? () => removeReminder.mutate(editing.draft.id!, { onSuccess: close }) : undefined} />
        </div>
      )}

      {choreList.length > 0 && <div className="progress" role="img" aria-label={`${done} of ${choreList.length} chores done`}><i style={{ width: `${(done / choreList.length) * 100}%` }} /></div>}
      <div className="todo-sec"><span className="eyebrow">Chores</span></div>
      {choreList.length === 0 && <div className="field__hint" style={{ padding: '6px 2px' }}>No chores due today.</div>}
      {layout === 'cards' ? <div className="tgrid">{shownChores.map(choreCardEl)}</div> : (<>
      {shownChores.map((chore) => {
        const who = person(chore.assignee_id);
        return (
          <div key={chore.id}>
            <div className="chore" data-done={chore.done}>
              <button className="chore__check" role="checkbox" aria-checked={chore.done} aria-label={chore.title} onClick={() => toggle.mutate({ id: chore.id, done: !chore.done })}>
                <span style={{ opacity: chore.done ? 1 : 0, display: 'grid' }}><CheckIcon /></span>
              </button>
              <div className="chore__main">
                <div className="chore__title">{chore.title}</div>
                <div className="chore__sub">
                  {who && <PersonAvatar kind={who.avatar} color={null} size={16} selected={false} />}
                  {who ? who.name.split(' ')[0] : 'Anyone'}{chore.day_part ? ` · ${dayParts.find((p) => p.id === chore.day_part)?.label.toLowerCase() ?? chore.day_part}` : ''}
                </div>
              </div>
              <span className="streak" data-zero={chore.streak === 0} title={`${chore.streak} days in a row`}><FlameIcon />{chore.streak}</span>
              <button className="rowbtn" aria-label={`Actions for ${chore.title}`} aria-expanded={menu === chore.id} onClick={() => { setMenu(menu === chore.id ? null : chore.id); setConfirmRemove(null); }}>⋯</button>
            </div>
            {menu === chore.id && (
              <div className="rowmenu">
                <button onClick={() => skip('chores', chore.id, chore.title)}>Not relevant today</button>
                <button onClick={() => editChore(chore)}>Edit</button>
                {confirmRemove !== chore.id ? <button className="danger" aria-label={`Remove ${chore.title}`} title="Remove for good" onClick={() => setConfirmRemove(chore.id)}><TrashIcon /></button>
                  : <button className="danger" onClick={() => removeChore.mutate(chore.id, { onSuccess: () => setMenu(null) })}>Remove for good?</button>}
              </div>
            )}
          </div>
        );
      })}

      </>)}

      <div className="todo-sec"><span className="eyebrow">Reminders</span></div>
      {reminderList.length === 0 && <div className="field__hint" style={{ padding: '6px 2px' }}>No reminders today.</div>}
      {layout === 'cards' ? <div className="tgrid">{shownReminders.map(reminderCardEl)}</div> : (<>
      {shownReminders.map((reminder) => {
        const who = person(reminder.member_id);
        return (
          <div key={reminder.id}>
            <div className="rem" data-done={!!reminder.done}>
              <button className="chore__check" role="checkbox" aria-checked={!!reminder.done} aria-label={`Done: ${reminder.title}`} onClick={() => reminderDone.mutate({ id: reminder.id, done: !reminder.done })}>
                <span style={{ opacity: reminder.done ? 1 : 0, display: 'grid' }}><CheckIcon /></span>
              </button>
              <span className="rem__icon" style={{ ['--c' as string]: who?.color ?? 'var(--violet)' }}><BellIcon /></span>
              <div className="chore__main">
                <div className="chore__title">{reminder.title}</div>
                <div className="chore__sub">
                  <PersonAvatar kind={who?.avatar ?? 'home'} color={null} size={16} selected={false} />
                  {who ? who.name.split(' ')[0] : 'Everyone'} · {(describePart(reminder.day_part, dayParts).split(' (')[0] ?? '').toLowerCase()}
                </div>
              </div>
              <button className="rowbtn" aria-label={`Actions for ${reminder.title}`} aria-expanded={menu === reminder.id} onClick={() => { setMenu(menu === reminder.id ? null : reminder.id); setConfirmRemove(null); }}>⋯</button>
            </div>
            {menu === reminder.id && (
              <div className="rowmenu">
                <button onClick={() => skip('reminders', reminder.id, reminder.title)}>Not relevant today</button>
                <button onClick={() => editReminder(reminder)}>Edit</button>
                {confirmRemove !== reminder.id ? <button className="danger" aria-label={`Remove ${reminder.title}`} title="Remove for good" onClick={() => setConfirmRemove(reminder.id)}><TrashIcon /></button>
                  : <button className="danger" onClick={() => removeReminder.mutate(reminder.id, { onSuccess: () => setMenu(null) })}>Remove for good?</button>}
              </div>
            )}
          </div>
        );
      })}

      </>)}

      {hidden > 0 && <button className="card__action" style={{ marginTop: 8 }} onClick={() => setShowAll(true)}>Show all ({hidden} more)</button>}
      {showAll && (choreList.length > MAX_ROWS || reminderList.length > MAX_ROWS) && <button className="card__action" style={{ marginTop: 8 }} onClick={() => setShowAll(false)}>Show less</button>}

      {upcoming.length > 0 && (
        <>
          <div className="todo-sec"><span className="eyebrow">Coming up</span></div>
          {upcoming.map((r) => (
            <div key={r.id} className="upnext">
              <b>{r.on_date ? new Date(`${r.on_date}T12:00:00`).toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' }) : ''}</b>
              <span>{r.title}{person(r.member_id) ? ` · ${person(r.member_id)!.name.split(' ')[0]}` : ''}</span>
            </div>
          ))}
        </>
      )}

      {undo && (
        <div className="undo" role="status">
          <span>Marked “{undo.title}” not relevant for today.</span>
          <button className="rowbtn" style={{ width: 'auto', padding: '4px 12px' }} onClick={() => restore(undo.kind, undo.id)}>Undo</button>
        </div>
      )}
      {skippedCount > 0 && !undo && (
        <details style={{ marginTop: 10 }}>
          <summary className="field__hint" style={{ cursor: 'pointer' }}>Not relevant today ({skippedCount})</summary>
          {skippedChores.map((c) => (
            <div key={c.id} className="upnext"><span style={{ flex: 1 }}>{c.title}</span><button className="rowbtn" style={{ width: 'auto', padding: '3px 10px' }} onClick={() => restore('chores', c.id)}>Restore</button></div>
          ))}
          {skippedReminders.map((r) => (
            <div key={r.id} className="upnext"><span style={{ flex: 1 }}>{r.title}</span><button className="rowbtn" style={{ width: 'auto', padding: '3px 10px' }} onClick={() => restore('reminders', r.id)}>Restore</button></div>
          ))}
        </details>
      )}
    </CardFrame>
  );
}
