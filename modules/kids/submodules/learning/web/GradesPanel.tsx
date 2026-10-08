import { useState } from 'react';
import { ApiError, BookIcon, CardFrame, ChipGroup, Empty, MergeIcon, Notice, PlusIcon, SelectField, Skeleton, TextField, TrashIcon } from '@chit/core';
import { findDuplicates, GRADE_STEPS, gradeLabel, KIND_LETTER, num, SUBJECT_KIND_LABEL, SUBJECT_KINDS, useGrades, useSend, type Subject, type SubjectKind } from '../../../shared/kids';

const tone = (avg: number | null) => (avg === null ? {} : avg <= 2.4 ? { 'data-good': true } : avg < 3.5 ? { 'data-mid': true } : { 'data-bad': true });
const cell = (value: number | null) => <span className="mono" style={{ fontSize: '0.85rem', color: value === null ? 'var(--text-faint)' : 'var(--text-dim)' }}>{value === null ? 'none' : value.toFixed(1)}</span>;
const TREND: Record<string, { mark: string; text: string; color: string }> = {
  better: { mark: '↑', text: 'better', color: 'var(--lime)' }, worse: { mark: '↓', text: 'worse', color: 'var(--amber)' }, steady: { mark: '→', text: 'steady', color: 'var(--text-dim)' },
};

function SubjectRows({ title, subjects }: { title: string; subjects: Subject[] }) {
  if (subjects.length === 0) return null;
  return (
    <div>
      <div className="kd-grade kd-grade--head"><span>{title}</span><span>Written</span><span>Oral</span><span>Avg</span><span>Trend</span></div>
      {subjects.map((subject) => (
        <div key={subject.id} className="kd-grade">
          <span style={{ fontWeight: 500 }}>{subject.name} <span className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }} title={`Code ${subject.code}, ${SUBJECT_KIND_LABEL[subject.kind]}`}>{subject.code}<sup>{KIND_LETTER[subject.kind]}</sup></span></span>{cell(subject.written)}{cell(subject.oral)}
          <span className="kd-avg" {...tone(subject.average)}>{subject.average === null ? '–' : subject.average.toFixed(1)}</span>
          {subject.trend ? <span style={{ fontSize: '0.78rem', color: TREND[subject.trend]!.color }} title={`Trend: ${TREND[subject.trend]!.text}`}>{TREND[subject.trend]!.mark} {TREND[subject.trend]!.text}</span> : <span />}
        </div>
      ))}
    </div>
  );
}

/** The grade overview for one child: average and trend per subject, with adding a grade inline. Grades are private to parents. */
export default function GradesOverview({ memberId, name }: { memberId: string; name: string }) {
  const grades = useGrades(memberId);
  const send = useSend();
  const today = new Date().toLocaleDateString('en-CA');
  const [adding, setAdding] = useState(false);
  const [entry, setEntry] = useState({ subject_id: '', grade_type: 'written', grade: '2', date: today, note: '' });
  const [error, setError] = useState<string | null>(null);
  const fail = (e: unknown) => setError(e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was saved.');
  const frame = { title: 'Grades', icon: <BookIcon />, tone: '#8b7bff' } as const;

  if (grades.isPending) return <CardFrame {...frame} state="unconfigured"><Skeleton lines={5} /></CardFrame>;
  if (grades.isError) return <CardFrame {...frame} state="unavailable"><Empty title="Grades unavailable">The hub could not be reached.</Empty></CardFrame>;
  const data = grades.data;
  const chosen = entry.subject_id || data.subjects[0]?.id || '';
  const ofKind = (kind: SubjectKind) => data.subjects.filter((s) => s.kind === kind);

  return (
    <CardFrame {...frame} state="manual" subtitle={`${name} · scale 1 (best) to 6 · weighted per subject type`} provenance={['grades entered in Chit, visible to parents only']}>
      <div className="stack">
        {data.subjects.length === 0 ? <Empty title="No subjects yet">Subjects come from the school day. Add a lesson under Manage, below, and its subject appears here.</Empty>
          : <div className="kd-grades">{SUBJECT_KINDS.map(([kind, label]) => <SubjectRows key={kind} title={`${label} subjects`} subjects={ofKind(kind)} />)}</div>}
        {adding ? (
          <div className="subcard">
            <div className="form-grid">
              <SelectField label="Subject" value={chosen} options={data.subjects.length ? data.subjects.map((s): [string, string] => [s.id, `${s.name}  (${s.code}, ${SUBJECT_KIND_LABEL[s.kind]})`]) : [['', 'Add a lesson to the school day first']]} onChange={(subject_id) => setEntry({ ...entry, subject_id })} />
              <SelectField label="Grade" value={entry.grade} options={GRADE_STEPS.map(([v, l]): [string, string] => [String(v), l])} onChange={(grade) => setEntry({ ...entry, grade })} />
              <TextField label="Date" type="date" value={entry.date} onChange={(date) => setEntry({ ...entry, date })} />
              <TextField label="Note" value={entry.note} placeholder="Optional, parents only" onChange={(note) => setEntry({ ...entry, note })} />
            </div>
            <ChipGroup single label="Type of grade" selected={[entry.grade_type]} onChange={(v) => v[0] && setEntry({ ...entry, grade_type: v[0] })}
              options={[{ value: 'written', label: 'Written exam' }, { value: 'oral', label: 'Oral / short test' }]} />
            {error && <Notice tone="error">{error}</Notice>}
            <div className="row">
              <button type="button" className="btn" disabled={!chosen || send.isPending}
                onClick={() => send.mutate({ method: 'POST', path: '/api/kids/grades', body: { subject_id: chosen, grade_type: entry.grade_type, grade: num(entry.grade), date: entry.date, note: entry.note || null } },
                  { onSuccess: () => { setEntry({ ...entry, note: '' }); setError(null); setAdding(false); }, onError: fail })}>Save grade</button>
              <button type="button" className="btn btn--ghost" onClick={() => { setAdding(false); setError(null); }}>Cancel</button>
            </div>
          </div>
        ) : <div><button type="button" className="btn" disabled={data.subjects.length === 0} onClick={() => setAdding(true)}><PlusIcon />Add a grade</button></div>}
      </div>
    </CardFrame>
  );
}

/** Grade management for the bottom of the Kids page: latest entries, the subject list and how the average is weighted. */
export function GradesSettings({ memberId }: { memberId: string }) {
  const grades = useGrades(memberId);
  const send = useSend();
  const [weights, setWeights] = useState<{ core: string; minor: string; elective: string } | null>(null);
  const [editing, setEditing] = useState<{ id: string; name: string; code: string; mergeInto: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fail = (e: unknown) => setError(e instanceof ApiError ? e.message : 'Could not reach the hub. Nothing was saved.');

  if (grades.isPending) return <CardFrame title="Grade settings" state="unconfigured"><Skeleton lines={4} /></CardFrame>;
  if (grades.isError) return <CardFrame title="Grade settings" state="unavailable"><Empty title="Grades unavailable">The hub could not be reached.</Empty></CardFrame>;
  const data = grades.data;
  const duplicates = findDuplicates(data.subjects);
  const merge = (from: Subject, into: Subject) => {
    if (!window.confirm(`Merge “${from.name}” into “${into.name}”?\n\nIts ${from.lessons} lesson${from.lessons === 1 ? '' : 's'}, ${from.count} grade${from.count === 1 ? '' : 's'}, homework and bag items move to ${into.name}. ${into.name} keeps its own name, code and type.`)) return;
    send.mutate({ method: 'POST', path: `/api/kids/grades/subjects/${from.id}/merge`, body: { into: into.id } }, { onSuccess: () => { setEditing(null); setError(null); }, onError: fail });
  };
  const remove = (subject: Subject) => {
    if (!window.confirm(`Remove “${subject.name}”?\n\nIts ${subject.lessons} lesson${subject.lessons === 1 ? '' : 's'} leave the school day and its ${subject.count} grade${subject.count === 1 ? '' : 's'} and bag items are deleted. This cannot be undone.`)) return;
    send.mutate({ method: 'DELETE', path: `/api/kids/grades/subjects/${subject.id}` }, { onSuccess: () => setError(null), onError: fail });
  };

  return (
    <>
      <CardFrame title="Subjects" state="manual" tone="#8b7bff" subtitle="Each lesson in the school day is a subject. Manage its name, code and type here.">
        <div className="stack">
          {data.subjects.length === 0 ? <Empty title="No subjects yet">Add lessons to the school day (the editor above). Each new lesson title becomes a subject.</Empty> : (
            <>
              <p className="field__hint" style={{ margin: 0 }}>To add a subject, add a lesson to the school day. If the same subject was entered twice under different names or codes, merge them. The bin removes a subject with its lessons and grades.</p>
              {data.subjects.map((s) => {
                const twin = duplicates.get(s.id);
                return (
                  <div key={s.id} className="kd-row" style={{ alignItems: 'center', flexWrap: 'wrap' }}>
                    <div className="kd-row__main">
                      <div className="kd-row__title">{s.name} <span className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>{s.code}<sup>{KIND_LETTER[s.kind]}</sup></span></div>
                      <div className="kd-row__sub">{SUBJECT_KIND_LABEL[s.kind]} subject · {s.lessons} lesson{s.lessons === 1 ? '' : 's'} a week · {s.count} grade{s.count === 1 ? '' : 's'}</div>
                      {twin && <div className="kd-row__sub" style={{ color: 'var(--amber)' }}>Looks like a duplicate of “{twin.name}”.</div>}
                    </div>
                    {twin && <button type="button" className="btn kd-small" onClick={() => merge(s, twin)} title={`Move everything of ${s.name} into ${twin.name}`}><MergeIcon />Merge into {twin.name}</button>}
                    <button type="button" className="btn btn--ghost kd-small" onClick={() => { setError(null); setEditing(editing?.id === s.id ? null : { id: s.id, name: s.name, code: s.code, mergeInto: '' }); }}>{editing?.id === s.id ? 'Close' : 'Name and code'}</button>
                    <div className="seg" role="group" aria-label={`Type of ${s.name}`} style={{ marginBottom: 0 }}>
                      {SUBJECT_KINDS.map(([kind, label]) => (
                        <button key={kind} type="button" aria-pressed={s.kind === kind} disabled={send.isPending}
                          onClick={() => s.kind !== kind && send.mutate({ method: 'PUT', path: `/api/kids/grades/subjects/${s.id}`, body: { kind } }, { onError: fail })}>{label}</button>
                      ))}
                    </div>
                    <button type="button" className="btn btn--ghost kd-small kd-trash" aria-label={`Remove ${s.name}`} title={`Remove ${s.name}`} onClick={() => remove(s)}><TrashIcon /></button>
                    {editing?.id === s.id && (
                      <div className="subcard" style={{ flexBasis: '100%' }}>
                        <div className="form-grid">
                          <TextField label="Full name" value={editing.name} onChange={(name) => setEditing({ ...editing, name })} hint="Shown in lists and sheets. Renaming also renames its lessons, homework and bag items." />
                          <TextField label="Code" value={editing.code} onChange={(code) => setEditing({ ...editing, code })} hint="Up to 6 characters. Shown in the phone's week plan." />
                        </div>
                        <div className="row">
                          <button type="button" className="btn" disabled={!editing.name.trim() || !editing.code.trim() || send.isPending}
                            onClick={() => send.mutate({ method: 'PUT', path: `/api/kids/grades/subjects/${s.id}`, body: { name: editing.name, code: editing.code } }, { onSuccess: () => { setEditing(null); setError(null); }, onError: fail })}>Save</button>
                          <button type="button" className="btn btn--ghost" onClick={() => { setEditing(null); setError(null); }}>Cancel</button>
                        </div>
                        {data.subjects.length > 1 && (
                          <div className="row" style={{ alignItems: 'flex-end' }}>
                            <SelectField label="Merge this subject into another" value={editing.mergeInto} options={[['', 'Choose the subject to keep'], ...data.subjects.filter((o) => o.id !== s.id).map((o): [string, string] => [o.id, `${o.name}  (${o.code})`])]}
                              onChange={(mergeInto) => setEditing({ ...editing, mergeInto })} hint="Use this when the same subject was entered twice under different names or codes." />
                            <button type="button" className="btn" disabled={!editing.mergeInto || send.isPending} onClick={() => { const target = data.subjects.find((o) => o.id === editing.mergeInto); if (target) merge(s, target); }}><MergeIcon />Merge</button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </>
          )}
          {error && <Notice tone="error">{error}</Notice>}
        </div>
      </CardFrame>
      <CardFrame title="Latest grade entries" state="manual" tone="#8b7bff" subtitle="Newest first">
        {data.entries.length === 0 ? <p className="field__hint" style={{ margin: 0 }}>No grades yet.</p> : data.entries.map((g) => (
          <div key={g.id} className="kd-row">
            <span className="mono" style={{ width: 84, fontSize: '0.75rem', color: 'var(--text-dim)' }}>{g.given_on}</span>
            <div className="kd-row__main"><div className="kd-row__title">{g.subject}</div><div className="kd-row__sub">{g.grade_type === 'written' ? 'Written exam' : 'Oral / short test'}{g.note ? ` · ${g.note}` : ''}</div></div>
            <b style={{ fontSize: '1.05rem', color: g.grade <= 2.4 ? 'var(--lime)' : g.grade < 3.5 ? 'var(--amber)' : 'var(--magenta)' }}>{gradeLabel(g.grade)}</b>
            <button type="button" className="btn btn--ghost kd-small" onClick={() => send.mutate({ method: 'DELETE', path: `/api/kids/grades/${g.id}` })}>Delete</button>
          </div>
        ))}
      </CardFrame>
      <CardFrame title="How the average is worked out" state="manual" tone="#8b7bff" subtitle="Set once for the household">
        <div className="stack">
          <p className="field__hint" style={{ margin: 0 }}>Each type is averaged on its own, then combined with these weights. A subject with only one type uses it alone. Your school's rules decide the split.</p>
          {weights ? (
            <>
              <div className="form-grid">
                <TextField label="Core subjects: written %" type="number" min={0} value={weights.core} onChange={(core) => setWeights({ ...weights, core })} hint="Oral is the rest" />
                <TextField label="Minor subjects: written %" type="number" min={0} value={weights.minor} onChange={(minor) => setWeights({ ...weights, minor })} hint="Oral is the rest" />
                <TextField label="Elective subjects: written %" type="number" min={0} value={weights.elective} onChange={(elective) => setWeights({ ...weights, elective })} hint="Oral is the rest" />
              </div>
              <div className="row">
                <button type="button" className="btn" onClick={() => send.mutate({ method: 'PUT', path: '/api/kids/grades/weights', body: { core_written_pct: num(weights.core), minor_written_pct: num(weights.minor), elective_written_pct: num(weights.elective) } }, { onSuccess: () => setWeights(null), onError: fail })}>Save</button>
                <button type="button" className="btn btn--ghost" onClick={() => setWeights(null)}>Cancel</button>
              </div>
            </>
          ) : (
            <div className="row" style={{ alignItems: 'center' }}>
              <span style={{ flex: 1, fontSize: '0.85rem' }}>
                {SUBJECT_KINDS.map(([kind, label]) => <span key={kind}>{label}: written <b>{data.weights[`${kind}_written_pct`]}%</b> · oral <b>{100 - data.weights[`${kind}_written_pct`]}%</b><br /></span>)}
              </span>
              <button type="button" className="btn btn--ghost" onClick={() => setWeights({ core: String(data.weights.core_written_pct), minor: String(data.weights.minor_written_pct), elective: String(data.weights.elective_written_pct) })}>Edit weights</button>
            </div>
          )}
        </div>
      </CardFrame>
    </>
  );
}
