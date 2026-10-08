import { useState } from 'react';
import { ApiError, BookIcon, CardFrame, CheckIcon, ChipGroup, Empty, Notice, PlusIcon, SelectField, Skeleton, TextField, TrashIcon, UndoIcon, XIcon } from '@chit/core';
import { subjectOption, useHomework, useSend, type HomeworkTask } from '../../../shared/kids';

const due = (task: HomeworkTask) => {
  if (task.done) return `done ${task.done_on ?? ''}`.trim();
  if (task.days < 0) return `overdue since ${task.due_on}`;
  if (task.days === 0) return 'today';
  if (task.days === 1) return 'tomorrow';
  return task.days <= 7 ? `in ${task.days} days (${task.due_on})` : task.due_on;
};
const tomorrow = () => { const d = new Date(); d.setDate(d.getDate() + 1); return d.toLocaleDateString('en-CA'); };

/** Homework and tests for one child. The child can write here too (from their phone); parents see who added what and can remove anything. */
export default function HomeworkPanel({ memberId, name }: { memberId: string; name: string }) {
  const homework = useHomework(memberId);
  const send = useSend();
  const [adding, setAdding] = useState(false);
  const [showDone, setShowDone] = useState(false);
  const [entry, setEntry] = useState({ kind: 'homework', subject: '', title: '', due_on: tomorrow() });
  const [error, setError] = useState<string | null>(null);
  const fail = (e: unknown) => setError(e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was saved.');
  const frame = { title: 'Homework & tests', icon: <BookIcon />, tone: '#ffc857' } as const;

  if (homework.isPending) return <CardFrame {...frame} state="unconfigured"><Skeleton lines={4} /></CardFrame>;
  if (homework.isError) return <CardFrame {...frame} state="unavailable"><Empty title="Homework unavailable">The hub could not be reached.</Empty></CardFrame>;
  const { summary, tasks, subjects } = homework.data;
  const open = tasks.filter((t) => !t.done && !t.dismissed);
  const done = tasks.filter((t) => t.done);
  const notRelevant = tasks.filter((t) => t.dismissed);
  const confirmRemove = (task: HomeworkTask) => { if (window.confirm(`Remove “${task.title}” for good?`)) send.mutate({ method: 'DELETE', path: `/api/kids/homework/${task.id}` }); };
  const tile = (value: number, label: string, warn = false) => (
    <div className="kd-tile" data-warn={warn && value > 0 ? true : undefined}><b>{value}</b><span>{label}</span></div>
  );

  return (
    <CardFrame {...frame} state="manual" subtitle={`${name} · written by ${name} or a parent`} provenance={['homework and tests entered in Chit']}>
      <div className="stack">
        <div className="kd-tiles">{tile(summary.due_tomorrow, 'due tomorrow')}{tile(summary.tests_soon, 'tests in 2 weeks')}{tile(summary.overdue, 'overdue', true)}{tile(summary.done_this_week, 'done this week')}</div>

        {open.length === 0 ? <Empty title="Nothing open">No homework or tests right now.</Empty> : (
          <div>
            {open.map((task) => (
              <div key={task.id} className="kd-row">
                <button type="button" className="badge" data-state="unconfigured" style={{ minWidth: 28, justifyContent: 'center' }} aria-label={`Mark "${task.title}" done`}
                  onClick={() => send.mutate({ method: 'PUT', path: `/api/kids/homework/${task.id}`, body: { done: true } })} />
                <div className="kd-row__main">
                  <div className="kd-row__title">{task.kind === 'test' && <span className="badge" data-state="forecast" style={{ marginRight: 8 }}>Test</span>}{task.title}</div>
                  <div className="kd-row__sub" style={task.days < 0 ? { color: 'var(--amber)' } : undefined}>
                    {[task.subject, due(task), task.by === 'child' ? `added by ${name}` : 'added by a parent'].filter(Boolean).join(' · ')}
                  </div>
                </div>
                <button type="button" className="btn btn--ghost kd-small" aria-label={`Not relevant: ${task.title}`} title="Not relevant"
                  onClick={() => send.mutate({ method: 'PUT', path: `/api/kids/homework/${task.id}`, body: { dismissed: true } })}><XIcon /></button>
                <button type="button" className="btn btn--ghost kd-small kd-trash" aria-label={`Remove ${task.title}`} title="Remove for good" onClick={() => confirmRemove(task)}><TrashIcon /></button>
              </div>
            ))}
          </div>
        )}

        {notRelevant.length > 0 && (
          <details>
            <summary className="field__hint" style={{ cursor: 'pointer' }}>Not relevant ({notRelevant.length})</summary>
            {notRelevant.map((task) => (
              <div key={task.id} className="kd-row">
                <div className="kd-row__main"><div className="kd-row__title" style={{ color: 'var(--text-dim)' }}>{task.title}</div><div className="kd-row__sub">{[task.subject, 'not relevant'].filter(Boolean).join(' · ')}</div></div>
                <button type="button" className="btn btn--ghost kd-small" aria-label={`Bring back: ${task.title}`} title="Bring back"
                  onClick={() => send.mutate({ method: 'PUT', path: `/api/kids/homework/${task.id}`, body: { dismissed: false } })}><UndoIcon /></button>
                <button type="button" className="btn btn--ghost kd-small kd-trash" aria-label={`Remove ${task.title}`} title="Remove for good" onClick={() => confirmRemove(task)}><TrashIcon /></button>
              </div>
            ))}
          </details>
        )}

        {done.length > 0 && (
          <div>
            <button type="button" className="btn btn--ghost kd-small" aria-expanded={showDone} onClick={() => setShowDone(!showDone)}>{showDone ? 'Hide' : 'Show'} done ({done.length})</button>
            {showDone && done.map((task) => (
              <div key={task.id} className="kd-row">
                <button type="button" className="badge" data-state="available" style={{ minWidth: 28, justifyContent: 'center' }} aria-label={`Reopen "${task.title}"`}
                  onClick={() => send.mutate({ method: 'PUT', path: `/api/kids/homework/${task.id}`, body: { done: false } })}><CheckIcon /></button>
                <div className="kd-row__main"><div className="kd-row__title" style={{ color: 'var(--text-dim)' }}>{task.title}</div><div className="kd-row__sub">{[task.subject, due(task)].filter(Boolean).join(' · ')}</div></div>
              </div>
            ))}
          </div>
        )}

        {adding ? (
          <div className="subcard">
            <ChipGroup single label="What is it" selected={[entry.kind]} onChange={(v) => v[0] && setEntry({ ...entry, kind: v[0] })}
              options={[{ value: 'homework', label: 'Homework' }, { value: 'test', label: 'Test or exam' }]} />
            <div className="form-grid">
              <SelectField label="Subject" value={entry.subject} options={[['', 'No subject'], ...subjects.map(subjectOption)]} onChange={(subject) => setEntry({ ...entry, subject })}
                hint={subjects.length ? 'From the school day plan: core, minor and elective.' : 'No subjects yet: add lessons to the school day first.'} />
              <TextField label="Due" type="date" value={entry.due_on} onChange={(due_on) => setEntry({ ...entry, due_on })} />
              <TextField label="What to do" value={entry.title} placeholder="Worksheet 4, fractions" wide onChange={(title) => setEntry({ ...entry, title })} />
            </div>
            {error && <Notice tone="error">{error}</Notice>}
            <div className="row">
              <button type="button" className="btn" disabled={!entry.title.trim() || send.isPending}
                onClick={() => send.mutate({ method: 'POST', path: '/api/kids/homework', body: { member_id: memberId, ...entry, subject: entry.subject || null } },
                  { onSuccess: () => { setEntry({ ...entry, title: '' }); setError(null); setAdding(false); }, onError: fail })}>Save</button>
              <button type="button" className="btn btn--ghost" onClick={() => { setAdding(false); setError(null); }}>Cancel</button>
            </div>
          </div>
        ) : <div><button type="button" className="btn" onClick={() => setAdding(true)}><PlusIcon />Add homework or a test</button></div>}
      </div>
    </CardFrame>
  );
}
